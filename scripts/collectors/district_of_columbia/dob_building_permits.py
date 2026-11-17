"""Replay DC's DOB yearly construction registers; skip the overlapping 30-day layer.
Single source, so not split: the District of Columbia Department of Buildings (formerly DCRA) building permit register."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import lib.arcgis as arcgis
import re, collections, argparse, datetime
from urllib.parse import urlencode
from lib.url_archive import Archive
import lib.discovery as c
BASE='https://maps2.dcgis.dc.gov/dcgis/rest/services/FEEDS/DCRA/FeatureServer';DS='District of Columbia building permit register'
def query(u,**q):return u+'/query?'+urlencode({'f':'json',**q})
def run(fetch):
 a=Archive('dcprojects',fetch,owner='district_of_columbia');layers=a.json(BASE+'?f=json')['layers'];out=[];held=[];years={};keys=set()
 for l in layers:
    y=re.fullmatch(r'Building Permits - (20\d\d)',l['name'])
    if not y or int(y[1])>2026:continue
    year=y[1];layer=BASE+'/'+str(l['id']);meta=a.json(layer+'?f=json');cols={k['name'] for k in meta['fields']};required='OBJECTID PERMIT_ID ISSUE_DATE DESC_OF_WORK APPLICATION_STATUS_NAME PERMIT_TYPE_NAME'.split()
    if set(required)-cols:raise ValueError('Unexpected field layout '+year)
    where=' OR '.join("UPPER(DESC_OF_WORK) LIKE '%"+x+"%'" for x in ('DATA CENTER','DATACENTER','DATA-CENTER','DATA CENTRE','SERVER FARM'))
    pages=[]
    def g(u,**q):
        link=query(u[:-len('/query')],**q);return dict(url=link,body=a.json(link))
    p=arcgis.pull(g,lambda ref:ref['body'],layer,where,','.join(required+[k for k in ['PERMIT_SUBTYPE_NAME','WARD'] if k in cols]),batch=120,on_page=lambda ref,rows:pages.append((ref['url'],rows)))
    years[year]=len(p['ids']['body']['objectIds'] or [])
    for u,rs in pages:
        for r in rs:
            n=r['PERMIT_ID'];txt=' '.join((r['DESC_OF_WORK'] or '').split());stamp=r['ISSUE_DATE'];status=r['APPLICATION_STATUS_NAME'] or 'Not stated'
            when=datetime.datetime.fromtimestamp(stamp/1000,datetime.timezone.utc).date().isoformat() if isinstance(stamp,(int,float)) else str(stamp or '')[:10]
            if not re.fullmatch(r'\d{4}-\d\d-\d\d',when) or when>'2026-11-15' or not n or n in keys or re.search(r'former(?:ly)? (?:a )?data center|convert(?:ing)? (?:the |an existing )?data center (?:to|into)|adjacent to (?:a |the )?data center',txt,re.I):
                held.append([year,n,'Date, duplicate or different use']);continue
            keys.add(n);w="PERMIT_ID='"+str(n).replace("'","''")+"'";url=query(layer,where=w,outFields='*',f='html');rowid=r['OBJECTID'];out.append(dict(id='dc-dob-'+str(n),state='DC',dataset=DS,record_no=str(n),kind='Building permit',status=status,date=when,date_role='Issue date',jurisdiction='District of Columbia',county='District of Columbia',project=r['PERMIT_TYPE_NAME']+' '+str(n),url=url,source_url=query(layer,where=w,outFields='*',f='json'),source_sha256=a.sources[u]['sha256'],locator='DOB '+year+' register · '+str(n),details=dict(portal_row_id_at_capture=rowid,work_description=txt,subtype=r.get('PERMIT_SUBTYPE_NAME'),ward=r.get('WARD'),published_status=status)))
 c.dump(series_path('dc'),out);c.dump(c.R/'data/national/dc_audit.json',dict(yearly_candidates=years,held=held,published=len(out)));print(len(out),'DOB records',len(held),'held',collections.Counter(r['status'] for r in out))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
