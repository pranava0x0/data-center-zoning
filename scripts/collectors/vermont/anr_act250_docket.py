"""Vermont permit history: one source, the Vermont ANR Act 250 permit docket (District 1 Environmental Commission case
1R0372-10, VELCO Pinnacle Ridge data center) with its official exhibits, which include Vermont Department of
Environmental Conservation stormwater discharge and underground injection control records. The exhibits are attached
to the docket case, so they are not split into separate modules. Writes output/history/vermont/history.json. PDF archive
hash-checked offline; --refresh re-downloads."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import lib.net as netfetch
import re, argparse, html, json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from datetime import datetime
import fitz
from lib.text import plain
from lib.archive import NamedArchive as Archive
A=Archive('VT');BASE='https://anrweb.vt.gov/ANR/Act250/';INDEX=BASE+'default.aspx';CASE=BASE+'Details.aspx?Num=1R0372-10';NAMES={'land.pdf':'1R0372-10 Permit and COS.pdf','discharge.pdf':'027 1R0372-10 Discharge Permit 3329-9020.pdf','uic.pdf':'029 1R0372-10 Darlene Autery No UIC permit req.pdf','draftwater.pdf':'034 DRAFT Operational Stormwater Permit-3329-INDS.pdf'}
def hidden(s):
 d={}
 for t in re.findall(r'<input[^>]*>',s):
  k=re.search('name="([^"]+)"',t);v=re.search('value="([^"]*)"',t)
  if 'type="hidden"' in t and k:d[html.unescape(k[1])]=html.unescape(v[1]) if v else ''
 return d
def refresh():
 A.geom()
 def term(k):
  se=netfetch.Session()
  r=se.get(INDEX,timeout=30);form=hidden(r.text);form['ctl00$body$txtProjectDescription']=k;form['ctl00$body$btnSearch']='Search';v=se.post(INDEX,form,timeout=45);A.save('query-'+k.replace(' ','-')+'.html.gz',INDEX,v.body)
 with ThreadPoolExecutor(2) as ex:list(ex.map(term,['data center','data centre','server room','data processing']))
 def exhibit(t):
  n,name=t
  se=netfetch.Session()
  if True:
   r=se.get(CASE,timeout=30);form=hidden(r.text)
   for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',r.text,re.S):
    if name not in plain(tr):continue
    m=re.search(r'__doPostBack\(\x27([^\x27]+)',html.unescape(tr));form['__EVENTTARGET']=m[1];form['__EVENTARGUMENT']='';v=se.post(CASE,form,timeout=45);link=re.search(r"window.open\('(https://anrweb.vt.gov/[^']+)'",v.text);assert link;pdf=se.get(link[1],timeout=30);assert pdf.body.startswith(b'%PDF');A.save(n,pdf.url,pdf.body);return
   raise ValueError(n)
 A.fetch('detail.html.gz',CASE)
 with ThreadPoolExecutor(2) as ex:list(ex.map(exhibit,NAMES.items()))
 A.seal()
def build():
 A.verify();o=[];terms={}
 for n in A.files:
  if n.startswith('query-'):
   s=A.read(n).decode();found=sorted(set(re.findall(r'Details\.aspx\?Num=([^"&]+)',s)));terms[n]=found
 # Explicitly require review of a newly surfaced case, rather than silently dropping it.
 assert set(x for ns in terms.values() for x in ns)=={'1R0372-10'},terms
 ds='Vermont Act 250 permit docket';proj='VELCO Pinnacle Ridge data center and standby generator enclosure';n='detail.html.gz';s=plain(A.read(n).decode());pat=r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}, 20\d\d'
 def add(n,num,k,st,date,role,loc,**d):
  o.append(dict(id='vt-velco-'+str(len(o)),state='VT',dataset=ds,jurisdiction='Rutland Town',project=proj,record_no=num,kind=k,status=st,date=date,date_role=role,url=CASE,source_url=A.files[n]['url'],locator=loc,details={'issuer':d.pop('issuer','Vermont District 1 Environmental Commission'),'archive':'cache/history/vt/'+n,'archive_sha256':A.files[n]['sha256'],**d}))
 for label,stat in [('Date Application Received','Received'),('Date Deemed Complete','Deemed complete'),('Notice Issued','Notice issued'),('Response Deadline','Response deadline')]:
  m=re.search(label+' ('+pat+')',s);assert m;add(n,'1R0372-10','Act 250 case milestone',stat,datetime.strptime(m[1],'%b %d, %Y').date().isoformat(),label,'Project Status / '+label)
 def txt(n):return ' '.join(' '.join(p.get_text().split()) for p in fitz.open(A.c/n))
 assert 'hereby issues Land Use Permit Amendment' in txt('land.pdf') and 'Date Decision Issued May 23, 2017' in s
 add('land.pdf','1R0372-10','Act 250 land use permit amendment','Issued','2017-05-23','Commission decision date','Docket Project Status; final permit p. 1 explicitly authorizes data center and generator enclosure')
 n='discharge.pdf';t=txt(n);assert '4/11/2017 and shall continue until 4/11/2019' in t
 add(n,'3329-9020','Low-risk construction stormwater discharge coverage','Authorized','2017-04-11','Authorization date','Exhibit 027, pp. 1–2, discharge under CGP 3-9020',expiration_date='2019-04-11',issuer='Vermont Department of Environmental Conservation')
 n='uic.pdf';t=txt(n);assert 'no reason for a UIC Program permit' in t;add(n,'1R0372-10 / exhibit 029','Underground injection control applicability','No UIC permit required','2017-04-24','Agency review email date','Exhibit 029, p. 1: agency found no reason for a UIC permit; not issuance',issuer='Vermont Department of Environmental Conservation')
 n='draftwater.pdf';t=txt(n);assert 'DRAFT STORMWATER DISCHARGE PERMIT' in t;add(n,'3329-INDS','Operational stormwater discharge draft','Draft','2017-04-27','Docket exhibit date; final issuance not established','Exhibit 034 marked DRAFT; five-year proposed term not a final permit',issuer='Vermont Department of Environmental Conservation')
 lib.files.dump(series_path('vt'),o);lib.files.dump(collector_data('vermont','validation.json'),dict(events=len(o),search_results=terms,geography=A.rank()));print(len(o),'VT events')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
