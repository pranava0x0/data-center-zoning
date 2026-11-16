"""City of Boston Inspectional Services Department approved building permits (Analyze Boston CKAN datastore), screened for data center text."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import CACHE
from lib.files import pack, unpack
from lib.records import rec
from lib.net import query, get_simple as get
from lib.terms import EX
import json, re
D=CACHE/'ma';B='https://data.boston.gov/api/3/action/datastore_search_sql';BID='6ddcd912-32a0-43df-9908-63574f8c7e77'
TERMS=['data center','data-center','datacenter','data centre','data-centre','datacentre','data processing cent','server farm','server-farm']
def getj(u):return json.loads(get(u))
def cond(fields,engine):
 return '('+' OR '.join((('LOWER('+f+') LIKE ' if engine=='sql' else 'lower('+f+') like ')+"'%"+t+"%'") for f in fields for t in TERMS)+')'
def bos_download():
 wc=cond(['description','comments'],'sql');table='FROM "'+BID+'" WHERE '+wc
 def sql(q):
    r=getj(query(B,sql=q));return r['result']['records']
 n=int(sql('SELECT COUNT(*) AS n '+table)[0]['n']);rows=[]
 for off in range(0,n,300):
    rows+=sql('SELECT _id,permitnumber,worktype,permittypedescr,description,comments,issued_date,expiration_date,status,address,city '+table+' ORDER BY _id LIMIT 300 OFFSET '+str(off))
 if len(rows)!=n:raise ValueError('Boston count mismatch')
 pack(D/'boston-hits.json.gz',dict(count=n,rows=rows,url=query(B,sql='SELECT COUNT(*) '+table)))
def download():
 D.mkdir(exist_ok=True,parents=True);bos_download()
def rows():
 """Records plus the candidate count the validation file reports."""
 rows=[];p=D/'boston-hits.json.gz';o=unpack(p);seen=set()
 for x in o['rows']:
    n=x['permitnumber'];kind=x['permittypedescr'];text=' '.join((str(x.get('comments') or '')+' '+str(x.get('description') or '')).split())
    if not EX.search(text):continue
    if n in seen:raise ValueError('Duplicate Boston permit number '+n)
    seen.add(n);sql='SELECT * FROM "'+BID+'" WHERE permitnumber=\''+n+"'";u=query(B,sql=sql)
    a={'A21185':'LF1360/2010','A491662':'ALT437194'};parent=a.get(n)
    if 'Amendment' in kind and not parent:raise ValueError('Check original instrument for new amendment '+n)
    site_phase='decommissioning' if re.search('decommission|remove data centers|demoing out old data center|data center consolidation',text,re.I) else 'data center-related work or occupancy'
    date=(x.get('issued_date') or '')[:10] or None
    rows.append(rec('MA','bos-'+n,'Boston ISD approved building permits',n,kind,x['status'],date,'permit issue date',u,'City permitnumber '+n+'; comments, type, status and date',text,'Boston','Suffolk County',p,issuer='Boston Inspectional Services Department',address=x['address'],source_location=x['city'],issue_date=date,expiration_date=(x.get('expiration_date') or '')[:10] or None,amends=parent,project_phase=site_phase))
 return rows,o['count']
