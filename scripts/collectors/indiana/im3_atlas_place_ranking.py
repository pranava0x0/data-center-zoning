"""Indiana IM3 atlas data-center centroids joined to Census 2026 incorporated places (state ranking by county and place)
for output in data/history/indiana/rank.json. Issuers: PNNL IM3 Open Source Data Center Atlas; U.S. Census Bureau place boundaries."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import collections, json
from urllib.parse import urlencode
from lib.geo import pinring
from collectors.indiana.evidence_store import M, RANK, get, read, j, netfetch, collect
def rank(m):
    atlas=json.loads(read(m['atlas']));polys=json.loads(read(m['places']));ids=json.loads(read(m['place_ids']))['objectIds'];fs=polys['features']
    if polys.get('exceededTransferLimit') or len(fs)!=len(ids) or set(ids)!={f['attributes']['OBJECTID'] for f in fs}:raise ValueError('Incomplete Census places')
    bs=[]
    for f in fs:
        rr=f['geometry']['rings'];pts=[p for r in rr for p in r];bs.append((f['attributes']['NAME'],(min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)),rr))
    rows=[]
    for f in atlas['features']:
        a=f['properties']
        if a['state_abb']!='IN':continue
        x,y=f['geometry']['coordinates'];matches=[n for n,(u,v,w,z),rs in bs if u<=x<=w and v<=y<=z and sum(pinring(x,y,r) for r in rs)%2]
        if len(matches)>1:raise ValueError('Boundary overlap')
        rows.append(dict(county=a['county'],place=matches[0] if matches else 'Outside incorporated places',type=a['type'],label=a['name'],operator=a['operator']))
    def count(key):return dict(sorted(collections.Counter(a[key] for a in rows).items(),key=lambda q:(-q[1],q[0])))
    collect.dump(RANK,dict(unit='Mapped IM3 centroid records; campus and building geometries may overlap; unverified names retained',version='2026.11.02',boundary_vintage='2026 BAS incorporated places',source=m['atlas']['url'],boundary_source=m['places']['url'],indiana_total=len(rows),counties=count('county'),places=count('place'),points=rows))
def download(m,c):
    apex=c['places']+'/query?';common=dict(f='json',where="STATE='18'")
    for key,url in [('atlas',c['atlas']),('place_ids',apex+urlencode(dict(**common,returnIdsOnly='true'))),('places',apex+urlencode(dict(**common,outFields='OBJECTID,GEOID,NAME',returnGeometry='true',outSR=4326,maxAllowableOffset='.000025',geometryPrecision='6')))]:
        if key not in m or netfetch.REFETCH:m[key]=get(url,'json'); collect.dump(M,m)
    rank(m)
