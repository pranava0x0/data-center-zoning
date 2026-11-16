"""PNNL/IM3 data-center atlas centroids joined to Census 2024 places to rank Texas counties and places by data-center point count
(writes data/history/texas/rankings.csv and data/history/texas/geo_summary.json). Publishes no permit records."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from lib.files import dump, sha
from lib.net import req
from lib.terms import MATCH, patterns
from lib.text import isodate, Fields
import lib.arcgis as arcgis
import gzip, json, re
from urllib.parse import urlencode, quote
from collections import Counter
from lib.geo import places, contains
import csv
from collectors.texas.common import ROOT, C, CONFIG, saver
def download(m):
    save=saver(m)
    for k,n in [('pnnl','pnnl-centroids.geojson'),('places','census-places.zip')]:save(n,req(CONFIG[k]),CONFIG[k])
def rankings():
    us=json.loads((C/'pnnl-centroids.geojson').read_bytes())['features'];tx=[f for f in us if f['properties']['state_abb']=='TX']
    polys=list(places((C/'census-places.zip').read_bytes()));counts=Counter();names={};unplaced=0
    for f in tx:
        p=f['properties'];co=p['county'];counts[('county',co)]+=1
        x,y=f['geometry']['coordinates'][:2];matches=[a for a,(l,b,r,t),rings in polys if l<=x<=r and b<=y<=t and contains(x,y,rings)]
        if len(matches)>1:raise ValueError('Overlapping places')
        if not matches:unplaced+=1;continue
        a=matches[0];level='census_designated_place' if a['LSAD']=='57' else 'incorporated_place';key=(level,a['NAMELSAD']);names[key]=a['GEOID'];counts[key]+=1
    rankings=[]
    for lev in ('county','incorporated_place','census_designated_place'):
        items=sorted([(k,v) for k,v in counts.items() if k[0]==lev],key=lambda kv:(-kv[1],kv[0][1]))
        for key,v in items:
            rank=1+sum(other>v for _,other in items)
            rankings.append(dict(level=lev,rank=rank,name=key[1],point_count=v,geoid=names.get(key,''),inventory_commit='fe4d8420f9fdc7b16b82b8461c5e4c39b93d8f1d',boundary_vintage='2024 generalized' if lev!='county' else 'lab supplied'))
    with (collector_data('texas','rankings.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rankings[0]));w.writeheader();w.writerows(rankings)
    assert sum(r['point_count'] for r in rankings if r['level']=='county')==len(tx)
    assert sum(r['point_count'] for r in rankings if r['level']!='county')+unplaced==len(tx)
    dump(collector_data('texas','geo_summary.json'),{'us_points':len(us),'texas_points':len(tx),'outside_2024_mapped_place':unplaced,'tx_source_geometry':Counter(f['properties']['type'] for f in tx),'counts_by_level':{l:sum(r['point_count'] for r in rankings if r['level']==l) for l in ('county','incorporated_place','census_designated_place')}})
