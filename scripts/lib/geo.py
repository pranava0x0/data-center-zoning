"""Data-center marker geography: Census place polygons, point-in-polygon, IM3 county/place ranking."""
import collections, io, struct, zipfile
import lib.discovery as collect
from lib.paths import R, collector_data, state_folder
PNNL = 'https://raw.githubusercontent.com/IMMM-SFA/datacenter-atlas/fe4d8420f9fdc7b16b82b8461c5e4c39b93d8f1d/static/im3_datacenter_centroids.geojson'
GAZ = 'https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip'


def places(z):
    """Read Census DBF plus polygon parts; holes/multipart use even-odd containment."""
    c=zipfile.ZipFile(io.BytesIO(z));s=c.read(next(n for n in c.namelist() if n.endswith('.shp')));d=c.read(next(n for n in c.namelist() if n.endswith('.dbf')))
    n,hl,rl=struct.unpack_from('<IHH',d,4);cols=[];at=32
    while d[at]!=13:
        cols.append((d[at:at+11].split(b'\0')[0].decode(),d[at+16]));at+=32
    o=100
    for i in range(n):
        rr=hl+i*rl+1;attrs={}
        for k,w in cols:attrs[k]=d[rr:rr+w].decode('utf-8').strip();rr+=w
        rec,size=struct.unpack_from('>ii',s,o);raw=s[o+8:o+8+size*2];o+=size*2+8
        assert rec==i+1 and struct.unpack_from('<i',raw,0)[0]==5
        bbox=struct.unpack_from('<4d',raw,4);nr,np=struct.unpack_from('<ii',raw,36);idx=struct.unpack_from('<%di'%nr,raw,44)+(np,);pts=list(struct.iter_unpack('<dd',raw[44+4*nr:]));assert len(pts)==np
        yield attrs,bbox,[pts[idx[j]:idx[j+1]] for j in range(nr)]
def contains(x,y,poly):
    inside=False
    for ring in poly:
        for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
            if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
    return inside
def pinring(x,y,r):
    if not r:return False
    inside=False
    for (x1,y1),(x2,y2) in zip(r,r[1:]):
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
    return inside
def geofetch(store,code):
    u='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/11/query';where="STATE='"+code+"'"
    return dict(atlas=store.get('https://immm-sfa.github.io/datacenter-atlas/im3_datacenter_centroids.geojson'),ids=store.get(u,where=where,returnIdsOnly='true'),polygons=store.get(u,where=where,outFields='OBJECTID,GEOID,NAME',returnGeometry='true',outSR=4326,maxAllowableOffset='.000025',geometryPrecision='6'))
def rank(store,m):
    data=store.read(m['polygons']);fs=data['features'];ids=store.read(m['ids'])['objectIds'];boxes=[]
    if data.get('exceededTransferLimit') or {v['attributes']['OBJECTID'] for v in fs}!=set(ids):raise ValueError('Incomplete boundaries')
    for f in fs:
        rs=f['geometry']['rings'];xs,ys=zip(*(p for r in rs for p in r));boxes.append((f['attributes']['NAME'],(min(xs),min(ys),max(xs),max(ys)),rs))
    out=[]
    for f in store.read(m['atlas'])['features']:
        a=f['properties']
        if a['state_abb']!=store.st:continue
        x,y=f['geometry']['coordinates'];place=[n for n,(a1,b1,a2,b2),rs in boxes if a1<=x<=a2 and b1<=y<=b2 and sum(pinring(x,y,r) for r in rs)%2]
        if len(place)>1:raise ValueError('Boundary overlap')
        out.append(dict(county=a['county'],place=place[0] if place else 'Outside incorporated places',name=a['name'],operator=a['operator'],type=a['type']))
    def count(k):return dict(sorted(collections.Counter(z[k] for z in out).items(),key=lambda kv:(-kv[1],kv[0])))
    collect.dump(collector_data(state_folder(store.st),'rank.json'),dict(unit='OSM-derived mapped centroid records, not operational sites or capacity',atlas_version='2026.11.02',source=m['atlas']['url'],boundary_vintage='2026 Census BAS incorporated places',boundary_source=m['polygons']['url'],total=len(out),counties=count('county'),places=count('place'),points=out))
