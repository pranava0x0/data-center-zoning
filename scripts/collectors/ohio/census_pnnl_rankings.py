"""Ohio county and incorporated-place ranking of PNNL IM3 data-center atlas points, using Census place and township
boundaries (TIGERweb). download() captures atlas and boundaries; rankings() builds rank.json offline."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import collections
from lib.geo import pinring
from collectors.ohio.common import get, read, dump, RANK
def download(c,m):
    m['atlas']=get(c['atlas'])
    m['places']=get(c['places']+'/query',where="STATE='39'",outFields='GEOID,NAME',outSR=4326,returnGeometry='true',maxAllowableOffset='0.000025',geometryPrecision='6')
    if read(m['places']).get('exceededTransferLimit'):raise ValueError('Incomplete place geometry capture')
    m['place_ids']=get(c['places']+'/query',where="STATE='39'",returnIdsOnly='true')
    m['union_townships']=get(c['townships']+'/query',where="STATE='39' AND COUNTY='159'",outFields='GEOID,NAME',outSR=4326,returnGeometry='true',maxAllowableOffset='0.000025',geometryPrecision='6')
def rank(m):
    atlas=read(m['atlas']);places=read(m['places'])['features'];n=len(read(m['place_ids'])['objectIds'])
    if len(places)!=n or len({f['attributes']['GEOID'] for f in places})!=n:raise ValueError('Place polygons incomplete')
    polys=[]
    for f in places:
        rings=f['geometry']['rings'];v=[p for r in rings for p in r]
        polys.append((f['attributes']['NAME'],(min(p[0] for p in v),min(p[1] for p in v),max(p[0] for p in v),max(p[1] for p in v)),rings))
    rows=[]
    for f in atlas['features']:
        a=f['properties']
        if a['state_abb']!='OH':continue
        x,y=f['geometry']['coordinates'][:2];matches=[nm for nm,(x1,y1,x2,y2),rings in polys if x1<=x<=x2 and y1<=y<=y2 and sum(pinring(x,y,r) for r in rings)%2]
        if len(matches)>1:raise ValueError('Ambiguous incorporated place')
        rows.append((a['county'],matches[0] if matches else 'Outside incorporated places'))
    def counts(lst):return dict(sorted(collections.Counter(lst).items(),key=lambda e:(-e[1],e[0])))
    return {'unit':'PNNL IM3 observed OSM-derived centroid records; not unique campuses, permits, confirmed operating sites, or MW','atlas_version':'2026.11.02','boundary_vintage':'2026 Census BAS incorporated places (Ohio); remaining points are outside incorporated places','source':m['atlas']['url'],'boundary_source':m['places']['url'],'ohio_total':len(rows),'counties':counts(x for x,y in rows),'places':counts(y for x,y in rows),'county_place':counts(x+' / '+y for x,y in rows)}
def rankings(m):
    rnk=rank(m);tp=read(m['union_townships'])
    if tp.get('exceededTransferLimit'):raise ValueError('Incomplete township polygons')
    uni=[a for a in read(m['atlas'])['features'] if a['properties']['state_abb']=='OH' and a['properties']['county']=='Union County']
    ts=collections.Counter()
    for a in uni:
        x,y=a['geometry']['coordinates'][:2];found=[f['attributes']['NAME'] for f in tp['features'] if sum(pinring(x,y,r) for r in f['geometry']['rings'])%2]
        if len(found)!=1:raise ValueError('Union point to township ambiguous')
        ts[found[0]]+=1
    rnk['union_county_subdivisions']=dict(ts);rnk['township_source']=m['union_townships']['url'];dump(RANK,rnk)
