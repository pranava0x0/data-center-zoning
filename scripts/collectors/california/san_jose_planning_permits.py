"""City of San Jose planning register and C.3 stormwater project tracking (PLN_PermitsAndComplaints MapServer layers 23 and 24). Issuer: City of San Jose Planning."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json
from urllib.parse import urlencode
import lib.arcgis as arcgis
import lib.terms
from collectors.california.evidence_store import js, dt, fetch, counts
def sjplan():
  s='https://geo.sanjoseca.gov/server/rest/services/PLN/PLN_PermitsAndComplaints/MapServer'
  for k in [23,24]:
   w=lib.terms.patterns(['FOLDERDESC','FOLDERNAME','WORKDESC','SUBDESC'],'UPPER');fs='OBJECTID,FOLDERRSN,FOLDERNUM,FOLDERDESC,FOLDERNAME,ADDRESS,APN,WORKDESC,SUBDESC,ISSUEDATE,FINALDATE,INDATE,'+('PERMITSTATUS,PERMITTYPE' if k==23 else 'STATUS');off=[0]
   def g(u,**p):
    if 'returnIdsOnly' in p:n=f'sjp-{k}-ids.json.gz'
    else:n=f'sjp-{k}-{off[0]}.json.gz';off[0]+=100
    return json.loads(fetch(n,u,p))
   r=arcgis.pull(g,lambda a:a,s+f'/{k}',w,fs,batch=100,id_params={'f':'json'},page_params={'f':'json'})
   counts[f'sjp-{k}']=len(r['ids']['objectIds'] or [])
def download_tasks():return [sjplan]
def rows(ctx):
 add=ctx.add;selected=ctx.selected;dups=ctx.dups
 for layer in [23,24]:
  k='sjp-'+str(layer);ids=sorted(js(k+'-ids.json.gz')['objectIds'] or []);seen=[];unique={}
  for i in range(0,len(ids),100):
   n=f'{k}-{i}.json.gz'
   for f in js(n)['features']:
    a=f['attributes'];o=a['OBJECTID'];seen.append(o);no=a['FOLDERRSN'];assert no
    if not selected(a,['FOLDERDESC','FOLDERNAME','WORKDESC','SUBDESC'],no,k):continue
    if no in unique:
     assert (a['STATUS' if layer==24 else 'PERMITSTATUS'],a['FOLDERNUM'],a['ISSUEDATE'])==unique[no];dups['San Jose repeated parcels']+=1;continue
    unique[no]=(a['STATUS' if layer==24 else 'PERMITSTATUS'],a['FOLDERNUM'],a['ISSUEDATE']);d1=dt(a['INDATE']);iss=dt(a['ISSUEDATE'])
    url='https://geo.sanjoseca.gov/server/rest/services/PLN/PLN_PermitsAndComplaints/MapServer/'+str(layer)+'/query?'+urlencode({'where':'FOLDERRSN='+repr(no),'outFields':'*','returnGeometry':'false','f':'pjson'})
    add('San José C.3 stormwater project tracking' if layer==24 else 'San José planning register',k,n,no,a['FOLDERNAME'] or a['FOLDERDESC'],a.get('PERMITTYPE') or 'C.3 project stage',unique[no][0],iss or d1,'Source issue date' if iss else 'Intake date','San Jose',url,f'FOLDERRSN {no}; OBJECTID {o}',{'issuer':'City of San José','folder_no':a['FOLDERNUM'],'summary':a['FOLDERDESC'],'intake_date':d1,'issue_date':iss,'final_date':dt(a['FINALDATE']),'address':a['ADDRESS']})
  assert sorted(seen)==ids
