"""A county public GIS query with complete object-ID batches and case-level deduplication."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.arcgis as arcgis
import argparse, collections, datetime, re
from urllib.parse import urlencode,urlsplit
from zoneinfo import ZoneInfo
from lib.url_archive import Archive
import lib.discovery as c
BASE='https://www.fairfaxcounty.gov/idrisi/rest/services/Jade/LandDevelopment/MapServer/13';REG='Fairfax County site plan and land development decisions'
COND="UPPER(PROJECT_NAME) LIKE '%DATA CENTER%' OR UPPER(PROJECT_NAME) LIKE '%DATACENTER%' OR UPPER(PROJECT_NAME) LIKE '%DATA CENTRE%' OR UPPER(PROJECT_NAME) LIKE '%SERVER FARM%'"
def parse_date(d):
 if not d:return ''
 return datetime.datetime.fromtimestamp(d/1000,ZoneInfo('America/New_York')).date().isoformat()
def run(fetch):
 a=Archive('fairfax',fetch,owner='virginia/fairfax_county/land_use_cases');md=a.json(BASE+'?f=json');oid=next(f['name'] for f in md['fields'] if f['type']=='esriFieldTypeOID')
 def req(**args):
    u=BASE+'/query?'+urlencode(dict(f='json',**args));x=a.json(u)
    if x.get('error'):raise ValueError(x['error'])
    return x,u,a.sources[u]['sha256']
 fields=oid+',RECORDID,PROJECT_NAME,APPTYPEALIAS,RECORD_STATUS,RECORD_STATUS_DATE,APPROVED_DATE,PROJECT_STATUS,LINK_URL';pages=[]
 def g(_,**q):
    x,u,h=req(**q);return dict(body=x,url=u,sha=h)
 pulled=arcgis.pull(g,lambda r:r['body'],BASE,COND,fields,oid,70,on_page=lambda ref,rows:pages.append((ref['url'],ref['sha'],rows)))
 iu,ih=pulled['ids']['url'],pulled['ids']['sha'];ids=sorted(pulled['ids']['body']['objectIds']);cases={};hold=[];objects=[]
 for url,sha,rows in pages:
    for q in rows:
        obj=q[oid];objects.append(obj);num=q['RECORDID'];day=parse_date(q['APPROVED_DATE']);status=q['RECORD_STATUS'];link=q['LINK_URL'] or ''
        if not day or day>'2026-11-15' or not num or not link.startswith('https://plus.fairfaxcounty.gov/'):
            hold.append(dict(objectid=obj,number=num,reason='No scoped approved date, case number or direct case URL'));continue
        when=day;kind=q['APPTYPEALIAS'];key=(num,kind,when)
        if key in cases:
            if cases[key]['project']!=q['PROJECT_NAME']:raise ValueError('Conflicting descriptions on same case')
            cases[key]['details']['object_ids'].append(obj);continue
        cases[key]=dict(id='va-fairfax-'+c.digest('|'.join(key).encode())[:18],state='VA',dataset=REG,record_no=num,jurisdiction='Fairfax County',county='Fairfax County',project=q['PROJECT_NAME'],kind=kind,status=status or 'Approval date recorded',date=when,date_role='Site register approval date',url=link,source_url=url,source_sha256=sha,locator=f'{md["name"]} · record {num} · OBJECTID {obj}',details=dict(issuer='Fairfax County Land Development Services',object_ids=[obj],source_project_status=q['PROJECT_STATUS'],current_status_date=parse_date(q['RECORD_STATUS_DATE']),scope='County site record. The approval date concerns the named submission, not a building permit or permission to operate. The county register can show a later project status.'))
 c.dump(series_path('fairfax_va'),sorted(cases.values(),key=lambda r:r['id']));c.dump(collector_data('virginia/fairfax_county/land_use_cases','audit.json'),dict(layer=BASE,id_query=iu,query_sha256=ih,source_features=len(ids),unique_site_cases=len(cases),held=hold,limits='Exact project-name terms in the public approved site layer. PLUS building and fire layers do not disclose a work description in their public map table. Independent City of Fairfax excluded.'));print(len(objects),'geometry records;',len(cases),'different case numbers, types and approval dates')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
