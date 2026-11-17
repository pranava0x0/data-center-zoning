"""California shared evidence store: the hash-pinned archive (cache/history/ca) and its manifest, the Socrata/Legistar download
helpers, and the record-building helpers every source module uses."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from lib.text import plain
import gzip, json, re, urllib.error, urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode,quote
import lib.files, lib.net, lib.terms, lib.text, lib.geo
R=Path(__file__).resolve().parents[3];C=R/'cache/history/ca';D=R/'data';cf=json.loads((collector_data('california','config.json')).read_text());MAN=collector_data('california','manifest.json');ASOF=cf['cutoff']
rx=re.compile(r'\b(?:data[\s/-]*(?:cent(?:er|re)s?|halls?)|server[\s/-]*farms?)\b',re.I); PATS=['%data%center%','%data%centre%','%data%hall%','%server%farm%']
def data(n):
 b=(C/n).read_bytes();return gzip.decompress(b) if n.endswith('.gz') else b
def js(n):return json.loads(data(n))
m={};counts={}
def fetch(n,url,params=None):
  full=url+('?'+urlencode(params) if params else '')
  try:b=lib.net.req(url,params)
  except lib.net.Refused as e:
    # robots.txt now disallows this endpoint (data.sanjoseca.gov /api/). Keep the last archived capture, and say so.
    if not (C/n).exists():raise
    bb=(C/n).read_bytes();m[n]={'url':full,'sha256':lib.files.sha(bb),'bytes':len(bb),'not_refreshed':str(e)};return data(n)
  bb=gzip.compress(b,mtime=0) if n.endswith('.gz') else b;(C/n).write_bytes(bb);m[n]={'url':full,'sha256':lib.files.sha(bb),'bytes':len(bb)};return b
class _NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*a,**k):return None
_STOP=urllib.request.build_opener(_NoRedirect)
def fetch_download(n,url,limit=400*1024**2):
  """Download a CKAN resource file (a robots-allowed /dataset/<id>/resource/<id>/download/ link) through lib.net and archive it
  gzipped. The portal answers with one 302 to a signed file-storage URL; each hop is robots-checked by lib.net, and the
  default ':443' is dropped from the signed host because urllib would otherwise sign-mismatch. Refused -> keep the last capture."""
  try:
    try:b=lib.net.request(url,limit=limit,timeout=900,opener=_STOP).body
    except urllib.error.HTTPError as e:
      if e.code not in (301,302,303,307,308) or not e.headers.get('Location'):raise
      b=lib.net.request(e.headers['Location'].replace(':443/','/',1),limit=limit,timeout=900).body
  except lib.net.Refused as e:
    if not (C/n).exists():raise
    bb=(C/n).read_bytes();m[n]={'url':url,'sha256':lib.files.sha(bb),'bytes':len(bb),'not_refreshed':str(e)};return data(n)
  bb=gzip.compress(b,mtime=0);(C/n).write_bytes(bb);m[n]={'url':url,'sha256':lib.files.sha(bb),'bytes':len(bb)};return b
def keep_archived(prefix,reason):
  """A source robots.txt no longer allows: carry its last sealed capture (files and counts) into the new manifest."""
  old=json.loads(MAN.read_text())
  for k,v in old['files'].items():
    if k.startswith(prefix):m[k]={**{x:y for x,y in v.items() if x!='not_refreshed'},'not_refreshed':str(reason)}
  for k,v in old['candidate_counts'].items():
    if k.startswith(prefix):counts[k]=v
def so(it):
  k,base,cols,sc=it;w=' OR '.join(f"lower({f}) like '{pat}'" for f in sc for pat in PATS);ct=int(json.loads(fetch(k+'-count.json',base,{'$select':'count(*) as n','$where':w}))[0]['n']);found=[]
  for i in range(0,ct,500):
   a=json.loads(fetch(f'{k}-{i}.json.gz',base,{'$select':cols+',:id as src_row_id','$where':w,'$limit':500,'$offset':i,'$order':':id'}));found.extend(r['src_row_id'] for r in a)
  assert len(found)==len(set(found))==ct,k;counts[k]=ct
def leg(prefix,base,mids):
  a=json.loads(fetch(prefix+'-matters.json.gz',base,{'$filter':"substringof('data center',MatterTitle) eq true",'$orderby':'MatterId','$top':1000}));assert len(a)<1000 and set(mids)<={a['MatterId'] for a in a}
  for mid in mids:fetch(f'{prefix}-{mid}.json.gz',f'{base}/{mid}/histories')
  counts[prefix+'-title-candidates']=len(a)
def dt(v):
 if isinstance(v,str) and '/' in v:return lib.text.isodate(v.split()[0])
 return lib.text.isodate(v)
class Ctx:
 """Accumulates the normalized events, exclusions and overlap counts while the source modules build their rows."""
 def __init__(self,files):
  self.files=files;self.out={};self.exc=[];self.dups=Counter()
 def add(self,ds,k,n,no,project,kind,status,when,role,city,url,loc,d,key=None):
  files=self.files;out=self.out;exc=self.exc
  if when and when>ASOF:exc.append({'source':k,'key':no,'reason':'Post-cutoff'});return
  rid='ca-'+k+'-'+quote(str(key or no),safe='');assert rid not in out and no and project and kind and status,(rid,no)
  out[rid]=dict(id=rid,state='CA',dataset=ds,jurisdiction=city,record_no=str(no),project=project,kind=kind,status=status,date=when,date_role=role,url=url,source_url=files[n]['url'],source_sha256=files[n]['sha256'],locator=loc,details={**d,'archive':'cache/history/ca/'+n})
 def selected(self,a,cols,id_,k):
  if not rx.search(' '.join(str(a.get(c) or '') for c in cols)):
   self.exc.append({'source':k,'key':id_,'reason':'Broad keyword screen did not match a sector phrase.'});return False
  return True
def legistar_rows(ctx,prefix,city,base,mids):
 add=ctx.add;exc=ctx.exc;ns=prefix+'-matters.json.gz';mrs=js(ns)
 for a in mrs:
  mid=a['MatterId'];no=a['MatterFile'];title=plain(a['MatterTitle'])
  if mid not in mids:exc.append({'source':prefix,'key':no,'reason':'Outside reviewed list of site-specific land-use, assessment or design matters.'});continue
  url=f'{base}/{mid}/histories';ds=city+' public land-use proceedings';n=f'{prefix}-{mid}.json.gz';accepted=0
  for h in js(n):
   stat=h['MatterHistoryActionName'];flag=h['MatterHistoryPassedFlagName'];motion=plain(h['MatterHistoryActionText'] or '')
   if not stat or not motion or re.search(r'close (the )?public hearing|waive rule|reopen the public hearing',motion,re.I) or (not flag and stat.lower() in ('approved','adopted')):continue
   when=dt(h['MatterHistoryActionDate']);accepted+=1
   add(ds,prefix,n,no,title,'Planning motion',stat,when,'Recorded motion date',city,url,'Matter '+no+', history '+str(h['MatterHistoryId']),{'issuer':h['MatterHistoryActionBodyName'],'motion_text':motion,'vote_result':flag,'matter_id':mid,'matter_title_archive':'cache/history/ca/'+ns,'matter_number':no},key=str(h['MatterHistoryId']))
  if not accepted and a['MatterAgendaDate']:
   add(ds,prefix,ns,no,title,'Agenda item','On agenda',dt(a['MatterAgendaDate']),'Agenda date',city,f'{base}/{mid}','Matter '+no+', agenda date',{'issuer':a['MatterBodyName'],'matter_id':mid,'scope':'Site-specific item; no verified substantive motion in returned history.'},key='agenda-'+str(mid))
