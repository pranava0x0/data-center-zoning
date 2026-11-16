"""Puerto Rico helpers shared by the source modules: the MIPR Permisos MapServer store and base URL, the search terms,
the shared layer-fetch step, the register replay, and the build loop that dispatches each feature to its layer's module."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R
import lib.net as netfetch
import json, sys, re, argparse, datetime as dt
from lib.files import j
from lib.archive import Store
from lib.arcgis import arcstore
import lib.discovery as collect
from urllib.parse import urlencode
from collections import Counter
S=Store('PR');BASE='https://sigejp.pr.gov/server/rest/services/MIPR/Permisos/MapServer/'
TERMS=['DATA CENTER','DATACENTER','DATA CENTRE','CENTRO DE DATO','CENTRO DE PROCESAMIENTO DE DATO','CENTRO DE PROCESAR DATO','CENTRO DE CÓMPUTO','CENTRO DE COMPUTO','COLOCATION','CODISA','NAP DEL CARIBE','CARIBBEAN NAP','PR-DC','PUERTO RICO DATA','CRITICAL HUB','EVERTEC','TRIPLET-S','AERONET']
def fetch_layer(m,p,i,fields):
 layer=next(x for x in S.read(j(collector_data('puerto_rico','sources.json'))['sige'])['layers'] if x['id']==i)
 fields_out=[f['name'] for f in layer['fields'] if f['type'] not in ('esriFieldTypeGeometry','esriFieldTypeOID')]
 for group,terms in [('use',TERMS[:9]),('alias',TERMS[9:])]:
  k=f'{i}-{group}'
  if k in m and not netfetch.REFETCH:continue
  where=' OR '.join("UPPER("+f+") LIKE '%"+v+"%'" for f in fields for v in terms)
  try:m[k]=arcstore(S,BASE+str(i),where,fields_out,100)
  except (ValueError,OSError) as e:m[k]={'url':BASE+str(i),'where':where,'error':str(e)}
  collect.dump(p,m);print(k,len(m[k].get('batches',[])),m[k].get('error',''),flush=True)
def rows(m):
 for k,r in m.items():
  for ref in r.get('batches',[]):
   for f in S.read(ref)['features']:yield k,f['attributes'],ref
def dateof(v):return dt.datetime.fromtimestamp(v/1000,dt.timezone.utc).date().isoformat() if v is not None else None
def hold_reason(l,a):
 reason='No reviewed facility scope, unequivocal disposition and date.'
 if l==16:reason='ARPE has filing date and procedure but no decision or issue status in this register.'
 if l==20 and a.get('OBJECTID')==11732:reason='Applicant name only; no facility description or status date.'
 return reason
def build(layers):
 """layers: {layer id: module with disposition(a,num,review) and OUT_FIELDS}."""
 m=j(collector_data('puerto_rico','register.json'));review=j(collector_data('puerto_rico','review.json'));out={};seen={};held=[];by={}
 for k,r in m.items():
  if 'error' in r:raise ValueError('Incomplete Puerto Rico discovery: '+k)
  ids=S.read(r['ids'])['objectIds'] or [];obs=[f['attributes'][r['oid']] for b in r['batches'] for f in S.read(b)['features']]
  if set(ids)!=set(obs) or len(ids)!=len(obs):raise ValueError('Incomplete Puerto Rico register: '+k)
  by[k]=len(ids)
 for k,a,ref in rows(m):
  l=int(k.split('-')[0]);oid=a['OBJECTID']
  if (l,oid) in seen:continue
  seen[l,oid]=True;ds=None;num=a.get('Caso') or a.get('CASO') or a.get('NUMERO_CAS')
  hit=layers[l].disposition(a,num,review)
  if hit:ds,d,s,typ,jur,project,role,extra=hit
  if not ds or not d or d>'2026-11-16':
   held.append(dict(layer=l,objectid=oid,case=num,reason=hold_reason(l,a)));continue
  lurl=BASE+str(l)+'/query?'+urlencode(dict(f='pjson',objectIds=oid,outFields=layers[l].OUT_FIELDS,returnGeometry='false'))
  z=dict(id='pr-jp-'+num.lower(),state='PR',dataset=ds,jurisdiction=jur,record_no=num,project=project,kind=typ,status=s,date=d,date_role=role,url=lurl,source_url=ref['url'],locator='MIPR Permisos; layer '+str(l)+'; OBJECTID '+str(oid)+'; '+num,details=dict(source_sha256=ref['sha256'],source_layer=l,objectid=oid,municipio=jur,**extra))
  if num in out:raise ValueError('Unexpected duplicate PR case')
  out[num]=z
 data=sorted(out.values(),key=lambda z:z['id']);collect.dump(series_path('pr'),data);collect.dump(collector_data('puerto_rico','held.json'),held);collect.dump(collector_data('puerto_rico','coverage.json'),dict(matches_per_query=by,unique_features=len(seen),held=len(held),published=len(data),municipalities=dict(Counter(a['jurisdiction'] for a in data)),by_status=dict(Counter(a['status'] for a in data)),by_class=dict(Counter(a['details']['procedure_code'] for a in data))));return data
