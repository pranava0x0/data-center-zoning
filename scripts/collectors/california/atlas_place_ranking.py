"""California data-center atlas (PNNL/IM3 geojson) points ranked by county and Census place, using the Census place boundaries
and county gazetteer. Issuers: PNNL/IM3 atlas; U.S. Census Bureau. Writes data/history/california/rankings.csv."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import csv, io
from collections import Counter
import lib.geo
from collectors.california.evidence_store import D, cf, data, js, fetch
def download_tasks():return [lambda:fetch('pnnl.geojson.gz',cf['pnnl']),lambda:fetch('census-places.zip',cf['census']),lambda:fetch('counties.zip',cf['county_gazetteer'])]
def rank():
 import zipfile
 z=zipfile.ZipFile(io.BytesIO(data('counties.zip')));f=io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig'));geos={('county',r['NAME']):r['GEOID'] for r in csv.DictReader(f,delimiter='\t') if r['USPS']=='CA'}
 ps=[a for a in js('pnnl.geojson.gz')['features'] if a['properties']['state_abb']=='CA'];polys=list(lib.geo.places(data('census-places.zip')));counts=Counter();outside=0
 for a in ps:
  co=a['properties']['county'];counts['county',co]+=1;x,y=a['geometry']['coordinates'][:2];mm=[m for m,(l,b,r,t),rings in polys if l<=x<=r and b<=y<=t and lib.geo.contains(x,y,rings)];assert len(mm)<2
  if not mm:outside+=1;continue
  m=mm[0];k=('census_designated_place' if m['LSAD']=='57' else 'incorporated_place',m['NAMELSAD']);geos[k]=m['GEOID'];counts[k]+=1
 with (collector_data('california','rankings.csv')).open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['level','rank','name','point_count','geoid','inventory_commit','boundary_vintage'])
  for lev in ('county','incorporated_place','census_designated_place'):
   a=sorted([(k,n) for k,n in counts.items() if k[0]==lev],key=lambda p:(-p[1],p[0][1]))
   for k,n in a:w.writerow([lev,1+sum(v>n for _,v in a),k[1],n,geos[k],'fe4d8420f9fdc7b16b82b8461c5e4c39b93d8f1d','Atlas county' if lev=='county' else '2024 generalized'])
 return {'markers':len(ps),'outside_mapped_places':outside}
