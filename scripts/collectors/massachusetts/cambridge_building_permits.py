"""City of Cambridge Inspectional Services permit registers (three Socrata datasets on data.cambridgema.gov), screened for data center text."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import CACHE
from lib.files import pack, unpack
from lib.net import query, get_simple as get
import json
D=CACHE/'ma';C='https://data.cambridgema.gov/resource/';CF={'9qm7-wbdc':['description_of_work','isd_approved_description'],'qu2z-8suj':['detailed_description_of_work','isd_approved_description'],'ex75-8iwq':['description_of_work','isd_approved_description']}
TERMS=['data center','data-center','datacenter','data centre','data-centre','datacentre','data processing cent','server farm','server-farm']
def getj(u):return json.loads(get(u))
def cond(fields,engine):
 return '('+' OR '.join((('LOWER('+f+') LIKE ' if engine=='sql' else 'lower('+f+') like ')+"'%"+t+"%'") for f in fields for t in TERMS)+')'
def cam(id):
 fields=['id','full_address','status','issue_date','applicant_submit_date','permit_type']+CF[id];where=cond(CF[id],'soda');base=C+id+'.json';count=int(getj(query(base,**{'$select':'count(*) AS n','$where':where}))[0]['n']);rows=[]
 for off in range(0,count,500):
    u=query(base,**{'$select':','.join(fields),'$where':where,'$order':'id','$limit':500,'$offset':off});rows.extend(getj(u))
 if count!=len(rows):raise ValueError('Cambridge result changed')
 pack(D/('cam-'+id+'.json.gz'),dict(count=count,rows=rows,url=query(base,**{'$where':where})))
def download():
 D.mkdir(exist_ok=True,parents=True)
 for k in CF:cam(k)
def rows():
 """Candidate counts per Cambridge register; every register currently has none, so no records are produced."""
 cp={}
 for id in CF:
    j=unpack(D/('cam-'+id+'.json.gz'));cp[id]=j['count']
    if cp[id]:raise ValueError('First Cambridge match requires status and project-scope review: '+id)
 return cp
