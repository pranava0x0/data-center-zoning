"""City of San Jose building permit registers (data.sanjoseca.gov CKAN datastore resources). Issuer: City of San Jose."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json
from collections import defaultdict
from urllib.parse import urlencode
import lib.net
from collectors.california.evidence_store import keep_archived
from collectors.california.evidence_store import cf, js, dt, fetch, counts, PATS
SJ='https://data.sanjoseca.gov/api/3/action/datastore_search_sql'
def sj(resource):
  try:cols=json.loads(lib.net.req('https://data.sanjoseca.gov/api/3/action/datastore_search',{'resource_id':resource,'limit':0}))['result']['fields']
  except lib.net.Refused as e:return keep_archived('sj-'+resource,e)
  allcols=[c['id'] for c in cols];search=[x for x in ['FOLDERDESC','FOLDERNAME','WORKDESCRIPTION','SUBTYPEDESCRIPTION'] if x in allcols];assert len(search)>=2
  w=' OR '.join(f'''"{f}" ILIKE '{p}' ''' for f in search for p in PATS);tail=' FROM "'+resource+'" WHERE '+w
  fields=[f for f in ['_id','Status','STATUS','gx_location','FOLDERNUMBER','FOLDERDESC','FOLDERNAME','SUBTYPEDESCRIPTION','WORKDESCRIPTION','PERMITAPPROVALS','ISSUEDATE','FINALDATE','FOLDERRSN'] if f in allcols];assert 'FOLDERNUMBER' in fields
  n='sj-'+resource;ct=int(json.loads(fetch(n+'-count.json',SJ,{'sql':'SELECT count(*) AS n'+tail}))['result']['records'][0]['n']);seen=[]
  for i in range(0,ct,500):
   q='SELECT '+','.join('"'+x+'"' for x in fields)+tail+' ORDER BY "_id" LIMIT 500 OFFSET '+str(i);a=json.loads(fetch(f'{n}-{i}.json.gz',SJ,{'sql':q}))['result']['records'];seen.extend(r['_id'] for r in a)
  assert len(seen)==len(set(seen))==ct,n;counts[n]=ct
def download_tasks():return [lambda r=r:sj(r) for r in cf['san_jose']]
def rows(ctx):
 add=ctx.add;selected=ctx.selected;dups=ctx.dups;sjset=defaultdict(list)
 for res,scope in cf['san_jose'].items():
  k='sj-'+res;ct=int(js(k+'-count.json')['result']['records'][0]['n']);seen=[]
  for i in range(0,ct,500):
   n=f'{k}-{i}.json.gz'
   for a in js(n)['result']['records']:
    seen.append(a['_id']);no=a['FOLDERNUMBER']
    if selected(a,['FOLDERNAME','FOLDERDESC','WORKDESCRIPTION','SUBTYPEDESCRIPTION'],no,k):sjset[no].append((n,res,a))
  assert len(seen)==len(set(seen))==ct
 for no,members in sjset.items():
  ss={a['Status'] for _,_,a in members};assert len({(a['FOLDERRSN'],a['ISSUEDATE']) for _,_,a in members})==1
  if len(members)>1:dups['San Jose overlapping source rows']+=len(members)-1
  if not ss<={'Active','UnderInspection','Expired'} or ('Expired' in ss and len(ss)>1):raise ValueError((no,ss))
  n,res,a=sorted(members,key=lambda e:e[2]['Status']!='Active')[0];when=dt(a['ISSUEDATE']);detail={'issuer':'City of San José','issue_date':when,'final_date':dt(a['FINALDATE']),'source_statuses':sorted(ss),'address':a['gx_location'],'subtype':a['SUBTYPEDESCRIPTION'],'matched_resources':[x[1] for x in members],'folder_rsn':a['FOLDERRSN']}
  add('San José building permit registers','sj',n,no,a['FOLDERNAME'] or a['SUBTYPEDESCRIPTION'],a['WORKDESCRIPTION'] or a['FOLDERDESC'],a['Status'],when,'Permit issue date','San Jose','https://data.sanjoseca.gov/api/3/action/datastore_search?'+urlencode({'resource_id':res,'filters':json.dumps({'FOLDERNUMBER':no})}),'FOLDERNUMBER '+no,detail)
