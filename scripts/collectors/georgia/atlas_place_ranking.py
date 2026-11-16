"""Atlas place ranking: the PNNL data center atlas points (OSM-derived) matched to 2026 Census BAS incorporated places
(Georgia Census place layer), written to data/history/georgia/rank.json. Supplies geography only, not permit records."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.geo import pinring
import collections
import lib.net as netfetch
import lib.discovery as collect
from collectors.georgia.evidence_store import get, read, M, RK
def rank(m):
    polys=read(m['places']);fs=polys['features'];ids=read(m['place_ids'])['objectIds']
    if polys.get('exceededTransferLimit') or len(ids)!=len(fs) or set(ids)!={v['attributes']['OBJECTID'] for v in fs}:raise ValueError('Incomplete incorporated places')
    bb=[]
    for v in fs:
        rs=v['geometry']['rings'];xy=[p for r in rs for p in r];bb.append((v['attributes']['NAME'],(min(p[0] for p in xy),min(p[1] for p in xy),max(p[0] for p in xy),max(p[1] for p in xy)),rs))
    points=[]
    for v in read(m['atlas'])['features']:
        a=v['properties']
        if a['state_abb']!='GA':continue
        x,y=v['geometry']['coordinates'];matches=[n for n,(ax,ay,bx,by),rs in bb if ax<=x<=bx and ay<=y<=by and sum(pinring(x,y,r) for r in rs)%2]
        if len(matches)>1:raise ValueError('Ambiguous incorporated place')
        points.append(dict(county=a['county'],place=matches[0] if matches else 'Outside incorporated places',name=a['name'],operator=a['operator'],type=a['type']))
    def cnt(k):return dict(sorted(collections.Counter(z[k] for z in points).items(),key=lambda z:(-z[1],z[0])))
    collect.dump(RK,dict(unit='Mapped OSM-derived POI/building/campus centroid records, not unique operating sites, permits or MW',version='2026.11.02',source=m['atlas']['url'],boundary_vintage='2026 Census BAS incorporated places',boundary_source=m['places']['url'],georgia_total=len(points),counties=cnt('county'),places=cnt('place'),points=points))
def fetch(c,m):
    def stage(k,fn):
        if k not in m or netfetch.REFETCH:m[k]=fn();collect.dump(M,m)
    stage('atlas',lambda:get(c['atlas']));u=c['places']+'/query'
    stage('place_ids',lambda:get(u,where="STATE='13'",returnIdsOnly='true'));stage('places',lambda:get(u,where="STATE='13'",outFields='OBJECTID,GEOID,NAME',returnGeometry='true',outSR=4326,maxAllowableOffset='.000025',geometryPrecision='6'))
    rank(m)
