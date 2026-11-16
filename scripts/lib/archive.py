"""Local evidence stores. Store: content-addressed gzip (by SHA-256). NamedArchive: files by name plus a sealed
manifest of hashes. (permit_archive.Archive is the URL-keyed store.)"""
import csv, gzip, hashlib, io, json, zipfile
from collections import Counter
from urllib.parse import urlencode
from lib import net as netfetch, files
from lib import geo as geolib
from lib.paths import R, D, collector_data, state_folder
from lib.geo import PNNL, GAZ


class Store:
    def __init__(self,st):self.st=st;self.d=R/f'cache/history/{st.lower()}';self.d.mkdir(exist_ok=True,parents=True)
    def get(self,url,ext='json',**args):
        if args:url+='?'+urlencode(dict(f='json',**args))
        b=netfetch.get(url,timeout=160)
        if ext=='json' and isinstance((o:=json.loads(b)),dict) and 'error' in o:raise ValueError(str(o['error']))
        h=hashlib.sha256(b).hexdigest();p=self.d/(h+'.'+ext+'.gz')
        if not p.exists():p.write_bytes(gzip.compress(b,mtime=0))
        return dict(url=url,sha256=h,bytes=len(b),ext=ext)
    def read(self,x):
        b=gzip.decompress((self.d/(x['sha256']+'.'+x['ext']+'.gz')).read_bytes())
        if len(b)!=x['bytes'] or hashlib.sha256(b).hexdigest()!=x['sha256']:raise ValueError('Invalid archive')
        return json.loads(b) if x['ext']=='json' else b

class NamedArchive:
 def __init__(self,st,owner=None):
  self.st=st;self.c=R/'cache/history'/st.lower();self.c.mkdir(exist_ok=True,parents=True);self.owner=owner or state_folder(st);self.m=collector_data(self.owner,'manifest.json');self.files={}
 def save(self,n,url,b):
  if n.endswith('.gz'):b=gzip.compress(b,mtime=0)
  old=self.c/n
  if old.exists():
   prev=old.read_bytes()
   if prev!=b:
    # Keep superseded bytes: a published edition may still cite them until the next build.
    keep=self.c/'superseded'/(files.sha(prev)+'-'+n);keep.parent.mkdir(exist_ok=True);keep.write_bytes(prev)
  (self.c/n).write_bytes(b);self.files[n]=dict(url=url,bytes=len(b),sha256=files.sha(b));return b if not n.endswith('.gz') else gzip.decompress(b)
 def fetch(self,n,url):return self.save(n,url,netfetch.req(url))
 def read(self,n):
  b=(self.c/n).read_bytes();return gzip.decompress(b) if n.endswith('.gz') else b
 def geom(self):
  fips={'NJ':'34','OR':'41','NC':'37','SC':'45','AL':'01','CT':'09','WV':'54','AK':'02','VT':'50','HI':'15'}[self.st]
  for name,url in [('points.geojson.gz',PNNL),('counties.zip',GAZ),('census-places.zip',f'https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_{fips}_place_500k.zip')]+([('cousub.zip',f'https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_{fips}_cousub_500k.zip')] if self.st=='NJ' else []):self.fetch(name,url)
 def seal(self,meta=None):files.dump(self.m,dict(cutoff='2026-11-15',files=dict(sorted(self.files.items())),**(meta or {})))
 def verify(self):
  self.files=json.loads(self.m.read_text())['files']
  for n,m in self.files.items():assert files.sha((self.c/n).read_bytes())==m['sha256'],n
 def rank(self):
  z=zipfile.ZipFile(io.BytesIO(self.read('counties.zip')));f=io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig'));geo={('county',r['NAME']):r['GEOID'] for r in csv.DictReader(f,delimiter='\t') if r['USPS']==self.st}
  ps=[a for a in json.loads(self.read('points.geojson.gz'))['features'] if a['properties']['state_abb']==self.st];levels={'place':list(geolib.places(self.read('census-places.zip')))}
  if self.st=='NJ':levels['municipality']=list(geolib.places(self.read('cousub.zip')))
  counts=Counter();outside=Counter()
  for a in ps:
   co=a['properties']['county'];counts['county',co]+=1;x,y=a['geometry']['coordinates'][:2]
   for lev,polys in levels.items():
    ms=[m for m,(l,b,r,t),rings in polys if l<=x<=r and b<=y<=t and geolib.contains(x,y,rings)];assert len(ms)<=1
    if not ms:outside[lev]+=1;continue
    m=ms[0];k=(lev if lev!='place' else ('census_designated_place' if m['LSAD']=='57' else 'incorporated_place'),m['NAMELSAD']);geo[k]=m['GEOID'];counts[k]+=1
  with collector_data(self.owner,'rankings.csv').open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['level','rank','name','point_count','geoid','inventory_commit','boundary_vintage'])
   for lev in ['county','municipality','incorporated_place','census_designated_place']:
    pairs=sorted([(k,n) for k,n in counts.items() if k[0]==lev],key=lambda a:(-a[1],a[0][1]))
    for k,n in pairs:w.writerow([lev,1+sum(v>n for _,v in pairs),k[1],n,geo[k],'fe4d8420f9fdc7b16b82b8461c5e4c39b93d8f1d','Atlas county' if lev=='county' else '2024 generalized'])
  return {'markers':len(ps),'outside':dict(outside)}
