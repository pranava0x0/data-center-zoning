"""Nevada helpers shared by the source modules: config, sealed-archive reader, record builder, GIS candidate reader and the
generic download helpers (the SOURCES config keys and GIS layers select what each module fetches)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import lib.arcgis as arcgis
import argparse, csv, gzip, html, io, json, re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,quote
from pypdf import PdfReader
import lib.files, lib.net, lib.terms, lib.text, lib.geo
R=Path(__file__).resolve().parents[3]; C=R/'cache/history/nv';D=R/'data'
cf=json.loads((collector_data('nevada','config.json')).read_text()); ASOF=cf['cutoff']; SOURCES=cf['sources']; GIS=cf['gis']; MAN=collector_data('nevada','manifest.json')
rx=re.compile(r'\b(?:data[\s/-]*(?:cent(?:er|re)s?|halls?)|server[\s/-]*farms?|super[\s-]*nap|switch\b.{0,16}\bnap\s*\d+|novva)\b',re.I)
labels={'henderson_other':'Henderson open development permits','henderson_grading':'Henderson open development permits','clark_inspection':'Clark County inspection sites','reno':'Reno issued permits','clark.pdf':'Clark County Part 70 operating permits','ctitle.html':'Clark County Title V renewal applications','dust.pdf':'Clark County active dust-control snapshot','ndep-air.html':'NDEP air applications','switch.pdf':'NDEP preliminary air determinations','lasvegas':'Las Vegas building permits'}
def plain(s):return ' '.join(html.unescape(re.sub(r'<[^>]*>',' ',s)).split())
def read(n):
 b=(C/n).read_bytes()
 return gzip.decompress(b) if n.endswith('.gz') else b
labels.update({'washoe-2015.pdf':'Washoe County special use permits','washoe-2023.pdf':'Washoe County project case files','washoe-minutes.pdf':'Washoe County planning decisions','washoe-notice.html':'Northern Nevada Public Health air notices','flexential.html':'Clark County air participation notices'})
def saver(m):
 def save(n,url,b):
  if b[:2]==b'\x1f\x8b':b=gzip.decompress(b)
  if n.endswith('.gz'):b=gzip.compress(b,mtime=0)
  (C/n).write_bytes(b);m[n]={'url':url,'sha256':lib.files.sha(b),'bytes':len(b)}
 return save
def fetch_sources(m,names,reuse=False):
 save=saver(m)
 for n,url in SOURCES.items():
  if n not in names:continue
  if reuse and (C/n).exists():b=read(n)
  elif reuse and n=='pnnl.geojson.gz':b=(R/'cache/history/tx/pnnl-centroids.geojson').read_bytes()
  else:b=lib.net.req(url)
  save(n,url,b)
def pull_layer(m,stats,k):
 save=saver(m);url,oid,fields,terms=GIS[k]
 uq=url+'/query';w=' OR '.join(f"UPPER({f}) LIKE '{p}'" for f in terms.split(',') for p in ['%DATA%CENTER%','%DATA%CENTRE%','%DATA%HALL%','%SERVER%FARM%','%SUPERNAP%','%SWITCH%NAP%','%NOVVA%'])
 def q(n,p):
  b=lib.net.req(uq,p);j=json.loads(b)
  if 'error' in j:raise ValueError((k,j['error']))
  save(n,uq+'?'+urlencode(p),b);return j
 offset=[0]
 def g(_,**p):
  if 'returnIdsOnly' in p:
   j=q(k+'-ids.json.gz',p)
   if j.get('objectIds'):assert j['objectIdFieldName'].lower()==oid.lower(),(k,oid,j['objectIdFieldName'])
   return j
  j=q(f'{k}-{offset[0]}.json.gz',p);offset[0]+=120;return j
 r=arcgis.pull(g,lambda j:j,url,w,fields,oid,batch=120,id_params={'f':'json'},page_params={'f':'json'})
 ids=r['ids']['objectIds'] or []
 stats[k]=len(ids);print(k,len(ids),flush=True)
def make_add(rows,m):
 def add(k,n,no,project,kind,status,date,role,jur,loc,details=None,url=None,key=None):
  if date and date>ASOF:return
  uid='nv-'+k.removesuffix('.pdf').removesuffix('.html')+'-'+quote(key or str(no),safe='')
  assert uid not in rows and no and project and kind and status,(uid,no)
  rows[uid]=dict(id=uid,state='NV',dataset=labels[k],jurisdiction=jur,record_no=str(no),project=project,kind=kind,status=status,date=date,date_role=role,url=url or m[n]['url'],source_url=m[n]['url'],locator=loc,source_sha256=m[n]['sha256'],details={**(details or {}),'archive':'cache/history/nv/'+n})
 return add
def pages(n):return [' '.join(p.extract_text().split()) for p in PdfReader(io.BytesIO(read(n))).pages]
def candidates(k,excluded):
 url,oid,fields,cols=GIS[k]
 ids=sorted(json.loads(read(k+'-ids.json.gz'))['objectIds'] or []);seen=[]
 for i in range(0,len(ids),120):
  n=f'{k}-{i}.json.gz';rr=json.loads(read(n))['features']
  for f in rr:
   a=f['attributes'];o=a[oid];seen.append(o);loc=f'{oid}={o}';u=url+'/query?'+urlencode(dict(where=loc,outFields=fields,returnGeometry='false',f='pjson'))
   if not rx.search(' '.join(str(a[c] or '') for c in cols.split(','))):
    excluded.append({'source':k,'object':o,'reason':'Broad query matched unrelated or separated words; no admitted sector phrase.'});continue
   yield a,n,o,loc,u
 assert sorted(seen)==ids
