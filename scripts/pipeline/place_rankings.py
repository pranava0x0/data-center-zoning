"""Geographic priority, independently from permit discovery, using pinned IM3 markers and Census incorporated-place polygons."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import lib.net as netfetch
import argparse, json, collections, gzip, hashlib, csv
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from lib.paths import ROOT, CACHE, collector_data, state_folder
ATLAS='https://raw.githubusercontent.com/IMMM-SFA/datacenter-atlas/fe4d8420f9fdc7b16b82b8461c5e4c39b93d8f1d/static/im3_datacenter_centroids.geojson'
BAS='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/11/query'
def inring(x,y,pts):
    test=False
    for a,b in zip(pts,pts[1:]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:test=not test
    return test
def run(st,refresh):
    fp={'MS':'28','LA':'22','NY':'36','MN':'27','CO':'08'}[st];d=CACHE/st.lower();d.mkdir(parents=True,exist_ok=True);src={}
    def get(k,url):
        p=d/f'rank-{k}.json.gz'
        if refresh:
            raw=netfetch.get(url,timeout=90)
            if k=='atlas':
                # Hold only state features; preserve original national hash for exact upstream replay.
                subset=[v for v in json.loads(raw)['features'] if v['properties']['state_abb']==st]
                raw=json.dumps(dict(national_sha256=hashlib.sha256(raw).hexdigest(),features=subset)).encode()
            p.write_bytes(gzip.compress(raw,mtime=0))
        raw=gzip.decompress(p.read_bytes());src[k]=dict(url=url,sha256=hashlib.sha256(raw).hexdigest());return json.loads(raw)
    a=get('atlas',ATLAS);criteria={'where':"STATE='"+fp+"'",'f':'json'}
    ids=get('ids',BAS+'?'+urlencode(dict(criteria,returnIdsOnly='true')))['objectIds']
    fs=get('places',BAS+'?'+urlencode(dict(criteria,outFields='OBJECTID,GEOID,NAME',outSR=4326,maxAllowableOffset='.000025',geometryPrecision='6',returnGeometry='true')))
    if fs.get('exceededTransferLimit') or set(ids)!={f['attributes']['OBJECTID'] for f in fs['features']}:raise ValueError('Incomplete Census frame')
    pol=[]
    for f in fs['features']:
        rr=f['geometry']['rings'];ps=[p for r in rr for p in r];pol.append((f['attributes']['NAME'],(min(x for x,y in ps),min(y for x,y in ps),max(x for x,y in ps),max(y for x,y in ps)),rr))
    vals=[]
    for f in a['features']:
        x,y=f['geometry']['coordinates'];places=[name for name,(xmin,ymin,xmax,ymax),rr in pol if xmin<=x<=xmax and ymin<=y<=ymax and sum(inring(x,y,r) for r in rr)%2]
        if len(places)>1:raise ValueError('Boundary overlap')
        p=f['properties'];vals.append(dict(place=places[0] if places else 'Outside incorporated places',county=p['county'],geometry=p['type'],label=p['name']))
    rank=lambda k:dict(sorted(collections.Counter(v[k] for v in vals).items(),key=lambda p:(-p[1],p[0])))
    out=dict(state=st,unit='Mapped IM3 markers, not unique sites or MW; building and campus counts may overlap. Source county; incorporated place is Census point-in-polygon.',sources=src,atlas_national_sha256=a['national_sha256'],total=len(vals),county=rank('county'),place=rank('place'),geometry=rank('geometry'),markers=vals)
    collector_data(state_folder(st),'rank.json').write_text(json.dumps(out,indent=2)+'\n');print(st,len(vals),list(rank('county').items())[:4],list(rank('place').items())[:5])
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('states',nargs='+',choices=['MS','LA','NY','MN','CO']);ap.add_argument('--refresh',action='store_true');a=ap.parse_args()
    for state in a.states:run(state,a.refresh)
