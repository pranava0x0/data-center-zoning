"""Arkansas Department of Energy and Environment (DEQ): Permit Data System facility lookup and bulk registers (regulated
storage tanks, air permits) plus the DEQ air-permit application and other-air-request registers."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.net as netfetch
import json, re, html, sys, gzip
from datetime import datetime
from urllib.parse import urlencode,urljoin
from concurrent.futures import ThreadPoolExecutor
from lib.paths import CACHE
from lib.net import get_simple as get, query
from lib.terms import EX
from lib.records import rec
from lib.text import strip
import csv, fitz
D=CACHE/'ar';P='https://adeq.state.ar.us/home/pdssql/'
AIR='Arkansas DEQ air permitting and PDS';MISC='Arkansas DEQ other air requests';TANK='Arkansas PDS regulated storage tank records';LR='Little Rock municipal permits';AURL='https://adeq.state.ar.us/air/permits/applications.aspx';FILES='https://adeq.state.ar.us/downloads/WebDatabases/PDS/'
def fetchterm(term):
 q=urlencode({'T_Name':term,'Search':'Search'}).encode();u=P+'pds.aspx'
 s=netfetch.request(u,data=q,headers={'Referer':u,'Content-Type':'application/x-www-form-urlencoded'},timeout=60).text;p=D/('term-'+term.replace(' ','_')+'.html.gz');p.write_bytes(gzip.compress(s.encode(),mtime=0))
 return list(set(html.unescape(h) for h in re.findall(r'href=["\']([^"\']+p_facil_details[^"\']+|p_facil_details[^"\']+)["\']',s,re.I)))
def bulk(k):
 b=get(FILES+k+'.csv');(D/(k+'.csv.gz')).write_bytes(gzip.compress(b,compresslevel=5,mtime=0))
def tab(k):
 with gzip.open(D/(k+'.csv.gz'),'rt',encoding='cp1252') as f:yield from csv.DictReader(f)
def select():
 out={};count=0
 for v in tab('FacilitiesWithCodes'):
    count+=1
    if EX.search(v['FacName']+' '+v['AltFacName']) or any(v.get('Fac'+k+t+'Code','').strip() in ('518210','7374') for k in ['Primary','Secondary','Tertiary'] for t in ['NAICS','SIC']):out[v['AFIN']]=v
 return count,out
def airlist():
 _,fs=select();return sorted({v['AFINDash'] for v in tab('FacAndPmtSummary') if v['AFIN'] in fs and v['PmtMedia'].strip()=='A'})
def forms(z):
 i,m=z;params=({'T_AFINDashMisc':i,'SearchMisc':'Search','FormNo':'2'} if m else {'T_AFINDash':i,'Search':'Search','FormNo':'1'});res=netfetch.request(AURL,data=params,timeout=60).body
 (D/(('misc-' if m else 'air-')+i+'.html.gz')).write_bytes(gzip.compress(res,mtime=0))
def source_rows(p):
 s=gzip.decompress(p.read_bytes()).decode()
 if 'Page 1 /' in strip(s) and not re.search(r'Page 1\s*/\s*1(?:\s|$)',strip(s)):raise ValueError('Paginate '+str(p))
 return re.findall(r'<tr\b[^>]*class=[\'"]addfooplus[\'"][^>]*>(.*?)</tr>',s,re.I|re.S)
def download():
 D.mkdir(exist_ok=True,parents=True)
 with ThreadPoolExecutor(max_workers=2) as t:list(t.map(bulk,['FacilitiesWithCodes','FacAndPmtSummary','AllPermitsWithCodes']))
 with ThreadPoolExecutor(max_workers=2) as t:list(t.map(forms,[(k,m) for k in airlist() for m in (False,True)]))
 for n in ['2507-AOP-R0','2273-A']:(D/(n+'.pdf')).write_bytes(get(urljoin(P,'/downloads/WebDatabases/PermitsOnline/Air/'+n+'.pdf')))
def rows():
 rows=[];cnt,fs=select();air=airlist();tank=0;water=[];held=[];allp=0;pdss={}
 for r in tab('AllPermitsWithCodes'):
    allp+=1;fid=r['PmtAFIN'];n=r['PmtNbr'].strip();media=r['PmtMedia'].strip()
    if fid not in fs:continue
    v=fs[fid];facility=v['FacName'];ct=v['FacCountyName'].title()+' County';place=v['FacSiteCity'].title()
    if media=='A':pdss[(fid,n)]=r['PmtStatusDesc'].strip();continue
    if media=='WN':water.append(n);continue # nationwide water register is a separate release
    if media!='R':held.append(n);continue
    tank+=1;p=D/'AllPermitsWithCodes.csv.gz';dash=fid[:2]+'-'+fid[2:]
    u=query(P+'p_permit_details_rst.aspx',AFIN=fid,AFINDash=dash,PmtNbr=n);when=None
    rows.append(rec('AR','rst-'+fid+'-'+n,TANK,n,'Regulated storage tank registry','Listed',when,'no issuance date reported',u,'DEQ regulated storage tank number '+n+', AFIN '+dash,facility,place,ct,p,issuer='Arkansas DEQ',facility_id=dash,agency_record_created=(r['RecCreatedDate'] or '').split(' ')[0],record_number_is='Tank program number; not proof of new permit issuance.'))
 for dash in air:
    fid=dash.replace('-','');fac=fs[fid];site=fac['FacName'];place=fac['FacSiteCity'].title();ct=fac['FacCountyName'].title()+' County';agency=query(P+'p_facil_info.aspx',AFIN=fid,AFINDash=dash)
    for misc in [False,True]:
        p=D/(('misc-' if misc else 'air-')+dash+'.html.gz')
        for z in source_rows(p):
            kv={k:strip(v) for k,v in re.findall(r'<td[^>]*headers="([^"]+)"[^>]*>(.*?)</td>',z,re.I|re.S)}
            if kv.get('AFIN',kv.get('AFIN_Misc'))!=dash:raise ValueError('Unexpected facility '+str(kv))
            raw=strip(z);submission=kv.get('Submission ID',kv.get('Submission_Id'));typ=re.search(r'Request Type:\s*(.+?)\s+Description:',raw)[1];curr=re.search(r'Status:\s*(.+?)\s+'+re.escape((kv.get('Name of Engineer') or kv['Staff'])),raw)[1]
            wn=re.search('Permit Number:\s*(\S+)',raw);no=wn[1] if wn else submission
            if not no:raise ValueError('Unidentified application')
            for label,role in [('Received','application received'),('Admin Complete','application complete date'),('Final','agency final decision date')]:
                match=re.search(label+r':\s*(\d{1,2}/\d{1,2}/\d{4})',raw)
                if not match:continue
                dt=datetime.strptime(match[1],'%m/%d/%Y').date().isoformat();status=label if label!='Final' else curr;key=no+'-'+label.replace(' ','-');doc=p;u=agency
                if label=='Final' and curr=='Issued':
                    if (fid,no) not in pdss:raise ValueError('Missing issuance cross-check')
                    doc=D/(no+'.pdf');txt=' '.join(' '.join(pg.get_text().split()) for pg in fitz.open(doc)[:3]);assert no in txt
                    u=urljoin(P,'/downloads/WebDatabases/PermitsOnline/Air/'+no+'.pdf')
                rows.append(rec('AR','air-'+key,MISC if misc else AIR,no,typ+' / air',status,dt,role,u,'DEQ Air Applications; facility '+dash+'; submission '+str(submission)+'; '+label,site,place,ct,doc,issuer='Arkansas DEQ',facility_id=dash,submission_id=submission,register_status=curr,pds_status=pdss.get((fid,no)),register_url=AURL,association='Data processing industry code plus site name or state air record. Includes proposed associated power infrastructure; not necessarily a data-hall permit.'))
                if misc and curr=='Issued' and label=='Received':
                    rows.append(rec('AR','misc-undated-'+submission,MISC,submission,typ+' / air',curr,None,'decision date not reported',agency,'Other Air Permit Requests: '+submission+'; Issued is the request status, not a dated final Title V permit.',site,place,ct,p,register_url=AURL,facility_id=dash))
 return rows,dict(facility_source_rows=cnt,permit_source_rows=allp,matched_facility_names_codes=len(fs),air_request_facilities=air,excluded_water_ids=sorted(water),other_programs_held=sorted(held))
