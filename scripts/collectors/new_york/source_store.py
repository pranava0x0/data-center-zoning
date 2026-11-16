"""Shared New York helpers: cache folder, Socrata (NYC Open Data / data.ny.gov) dataset IDs, query builders, record
builder and the paged series fetch used by the source modules in this folder."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.net as netfetch
from pathlib import Path
import json, csv, gzip, re, datetime, hashlib, time, argparse
from urllib.request import urlopen,Request
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from collections import Counter,defaultdict
from lib.paths import ROOT, CACHE
from lib.epa_icis import digest
D=CACHE/'ny';CITY='https://data.cityofnewyork.us';STATE='https://data.ny.gov'
EL='dm9a-ab7w';NOW='rbx6-tga4';NJ='w9ak-ipjd';BIS='ic3t-wcy2';BP='ipu4-2q9a';ASF='2wgt-bc53';TV='4n3a-en4b'
NY_FLD={EL:'job_filing_number,job_number,filing_number,filing_date,filing_type,filing_status,job_status,house_number,street_name,borough,bin,job_description,permit_issued_date',NOW:'job_filing_number,work_permit,sequence_number,filing_reason,house_no,street_name,borough,bin,work_type,approved_date,issued_date,expired_date,job_description,permit_status,tracking_number',NJ:'job_filing_number,filing_status,house_no,street_name,borough,bin,filing_date,current_status_date,first_permit_date,job_description',BIS:'job__,doc__,job_status_descrp,job_type,borough,house__,street_name,bin__,pre__filing_date,latest_action_date,job_description',BP:'borough,bin__,house__,street_name,job__,job_doc___,work_type,permit_status,filing_status,permit_type,permit_sequence__,permit_subtype,filing_date,issuance_date,expiration_date,permit_si_no'}
# Deliberately coarse positive search. Exact word boundaries and exclusions are enforced after download.
PRED=" OR ".join("upper(job_description) like '%"+s+"%'" for s in ('DATA CENTER','DATACENTER','DATA-CENTER','DATA CENTRE','DATACENTRE','DATA-CENTRE','SERVER FARM','SERVER-FARM','DATA PROCESSING CENTER','DATA PROCESSING CENTRE'))
EX=re.compile(r'\b(?:data[\s-]*(?:processing[\s-]+)?cent(?:er|re)s?|server[\s-]+farms?)\b',re.I)
def url(host,ds,**params):return host+'/resource/'+ds+'.json?'+urlencode(params)
def get(u):
    return json.loads(netfetch.get(u,timeout=110))
def put(fn,x):
    raw=json.dumps(x,sort_keys=True).encode();(D/(fn+'.json.gz')).write_bytes(gzip.compress(raw,mtime=0))
def read(fn):return json.loads(gzip.decompress((D/(fn+'.json.gz')).read_bytes()))
def fetch_series(ds):
    host=CITY if ds in NY_FLD else STATE
    where=PRED if ds in (NOW,NJ,BIS,EL) else '1=1'
    fields=NY_FLD.get(ds,'*');base={'$where':where}
    counturl=url(host,ds,**dict(base,**{'$select':'count(*)'}));cnt=int(get(counturl)[0]['count'])
    allrows=[];urls=[]
    for start in range(0,cnt,5000):
        u=url(host,ds,**dict(base,**{'$select':fields,'$order':':id','$offset':start,'$limit':5000}));urls.append(u);allrows.extend(get(u))
    if len(allrows)!=cnt:raise ValueError('Source count changed during paging '+ds)
    put(ds,dict(count=cnt,urls=urls,count_url=counturl,rows=allrows))
    print(ds,cnt,flush=True)
BOROS={'MANHATTAN':'New York County','STATEN ISLAND':'Richmond County','BROOKLYN':'Kings County','QUEENS':'Queens County','BRONX':'Bronx County'}
def iso(s):
    if not s:return None
    if '/' in s:return datetime.datetime.strptime(s[:10],'%m/%d/%Y').date().isoformat()
    return datetime.date.fromisoformat(s[:10]).isoformat()
def dataurl(host,ds,where):return url(host,ds,**{'$where':where})
def eq(field,val):return field+"='"+str(val).replace("'","''")+"'"
def matched(t):return EX.search(t or '') or 'FLOORDATA CENTER' in (t or '').upper()
def uniq(items):
    return list({json.dumps(a,sort_keys=True):a for a in items}.values())
def mk(ds,id,kind,status,num,day,role,surl,loc,project,place,county,archive,**extra):
    if not day or day>'2026-11-15':return None
    return dict(id='ny-'+id,state='NY',dataset=ds,jurisdiction=place,project=project,record_no=num,kind=kind,status=status,date=day,date_role=role,url=surl,source_url=surl,source_sha256=digest(archive),locator=loc,details=dict(county=county,**extra))
