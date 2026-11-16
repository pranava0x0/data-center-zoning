"""City of Lincoln, Nebraska commercial new-construction permits (Planning MapServer layers 0-5), filtered to data-center descriptions."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.arcgis as arcgis
from lib.paths import CACHE
from lib.records import rec
from lib.net import get_simple as get, query
from lib.terms import pred, EX
from lib.files import pack, unpack
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json
D=CACHE/'ne';B='https://gis.lincoln.ne.gov/public/rest/services/Planning/Commercial_New_Construction_Permits/MapServer/'
FIELDS='OBJECTID_1,PermNo,CurrStatus,CityCounty,DescWork,Address,PermType,Issued,Applied,Final,UseType,Occupancy,CITY'
LIN='Lincoln nonresidential building permits'
def iso(v):return datetime.strptime(v.strip(),'%m/%d/%Y').date().isoformat() if v and v.strip() else None
def layer(i):
 where=pred(['DescWork','UseType','Occupancy']);first=[];rows=[]
 def g(q,**p):
    link=query(q,**p,f='json');r=json.loads(get(link))
    if not first:
        first.append(link)
        if 'objectIds' not in r:raise ValueError(r)
    return r
 res=arcgis.pull(g,lambda r:r,B+str(i),where,FIELDS,'OBJECTID_1',batch=100,sort=False,on_page=lambda ref,items:rows.extend(items))
 u=first[0];ids=res['ids']['objectIds'] or []
 pack(D/('lincoln-'+str(i)+'.json.gz'),dict(url=u,records=rows,candidate_ids=ids))
def download():
 with ThreadPoolExecutor(max_workers=3) as t:list(t.map(layer,range(6)))
def rows():
 rows=[];candidates={};groups={}
 for idx in range(6):
    p=D/('lincoln-'+str(idx)+'.json.gz');o=unpack(p);candidates[str(idx)]=len(o['records'])
    for r in o['records']:
        if not EX.search(' '.join(str(r.get(k) or '') for k in ['DescWork','UseType','Occupancy'])):continue
        n=r['PermNo'].strip()
        basic={k:str(r.get(k) or '').strip() for k in ('CurrStatus','DescWork','Issued','Address')}
        if n in groups and groups[n]!=basic:raise ValueError('Conflicting Lincoln permit '+n)
        if n in groups:continue
        groups[n]=basic;dt=iso(r['Issued']);u=query(B+str(idx)+'/query',where="PermNo='"+n+"'",outFields=FIELDS,returnGeometry='false',f='pjson')
        rows.append(rec('NE','lin-'+n,LIN,n,'Nonresidential building permit / '+r['PermType'],r['CurrStatus'],dt or iso(r['Applied']),'permit issue date' if dt else 'application date',u,'Permit '+n+'; DescWork, Issued, CurrStatus',r['DescWork'],'Lincoln','Lancaster County',p,issuer='City of Lincoln / Lancaster County',address=r['Address'],issue_date=dt,final_date=iso(r['Final'])))
 return rows,candidates,len(groups)
