"""Census Bureau places (2024 cartographic boundary file) joined to the IM3 data-center atlas centroids to rank Nevada
counties and places by data-center point count; writes data/history/nevada/rankings.csv. Publishes no permit records."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import csv, json
from collections import Counter
from pathlib import Path
import lib.geo
from collectors.nevada.common import read, D, fetch_sources
NAMES=('census-places.zip','pnnl.geojson.gz')
def download(m,stats):fetch_sources(m,NAMES)
def rank():
 points=[a for a in json.loads(read('pnnl.geojson.gz'))['features'] if a['properties']['state_abb']=='NV']; polys=list(lib.geo.places(read('census-places.zip'))); counts=Counter();geos={};outside=Counter();county_geo={'Clark County':'32003','Storey County':'32029','Washoe County':'32031'}
 for p in points:
  co=p['properties']['county'];k=('county',co);counts[k]+=1;geos[k]=county_geo[co];x,y=p['geometry']['coordinates'][:2];inside=[m for m,(l,b,r,t),rings in polys if l<=x<=r and b<=y<=t and lib.geo.contains(x,y,rings)];assert len(inside)<2
  if inside:
   m=inside[0];k=('census_designated_place' if m['LSAD']=='57' else 'incorporated_place',m['NAMELSAD']);counts[k]+=1;geos[k]=m['GEOID']
  else:outside[co]+=1
 with (collector_data('nevada','rankings.csv')).open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['level','rank','name','point_count','geoid','inventory_commit','boundary_vintage'])
  for level in ('county','incorporated_place','census_designated_place'):
   sect=sorted([(k,n) for k,n in counts.items() if k[0]==level],key=lambda a:(-a[1],a[0][1]))
   for k,n in sect:w.writerow([level,1+sum(v>n for _,v in sect),k[1],n,geos[k],'fe4d8420f9fdc7b16b82b8461c5e4c39b93d8f1d','Atlas county' if level=='county' else '2024 generalized'])
 return {'markers':len(points),'outside_mapped_places':dict(outside)}
