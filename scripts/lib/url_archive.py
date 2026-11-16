"""Small immutable evidence store for HTML/PDF/ArcGIS collectors. Offline by default."""
import gzip, hashlib, json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
import lib.discovery as c
import lib.net as netfetch
from lib.paths import collector_data

class Archive:
    def __init__(self, state, fetch=False, owner=None, name='sources.json'):
        # owner: the collector (or script) folder under data/history/ whose sources these are; None = shared, kept in data/
        self.root=c.R/'cache/history'/state
        self.root.mkdir(exist_ok=True,parents=True)
        self.manifest=collector_data(owner,name) if owner else c.R/'data'/f'history_{state}_sources.json'
        self.sources=c.read(self.manifest,{});self.fetch=fetch

    def get(self,url):
        if url not in self.sources or (self.fetch and netfetch.REFETCH and url not in netfetch.SEEN):
            if not self.fetch:raise ValueError('Unarchived evidence: '+url)
            b,final=netfetch.get(url,timeout=60,limit=64*1024**2,with_url=True)
            netfetch.SEEN.add(url)
            sha=hashlib.sha256(b).hexdigest()
            (self.root/(sha+'.gz')).write_bytes(gzip.compress(b,mtime=0))
            self.sources[url]=dict(sha256=sha,bytes=len(b),retrieved=c.now(),resolved=final)
            c.dump(self.manifest,self.sources)
        row=self.sources[url];b=gzip.decompress((self.root/(row['sha256']+'.gz')).read_bytes())
        if hashlib.sha256(b).hexdigest()!=row['sha256']:raise ValueError('Source bytes changed: '+url)
        return b,row['sha256']
    def json(self,url):return json.loads(self.get(url)[0])

def place_rank(archive,state,fips):
    from lib.geo import pinring
    from collections import Counter
    from urllib.parse import urlencode
    url='https://immm-sfa.github.io/datacenter-atlas/im3_datacenter_centroids.geojson'
    layer='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/11/query?'
    args=dict(f='json',where=f"STATE='{fips}'")
    idurl=layer+urlencode(dict(**args,returnIdsOnly='true'))
    purl=layer+urlencode(dict(**args,outFields='OBJECTID,GEOID,NAME',returnGeometry='true',outSR=4326,maxAllowableOffset='.000025',geometryPrecision=6))
    fs=archive.json(purl);ids=archive.json(idurl)['objectIds']
    assert not fs.get('exceededTransferLimit') and set(ids)=={f['attributes']['OBJECTID'] for f in fs['features']}
    rows=[]
    for f in archive.json(url)['features']:
        a=f['properties']
        if a['state_abb']!=state:continue
        x,y=f['geometry']['coordinates']
        places=[p['attributes']['NAME'] for p in fs['features'] if sum(pinring(x,y,r) for r in p['geometry']['rings'])%2]
        if len(places)>1:raise ValueError('Overlapping city polygons')
        rows.append(dict(county=a['county'],place=next(iter(places),'Outside incorporated places'),name=a.get('name')))
    def counts(k):return dict(sorted(Counter(r[k] for r in rows).items(),key=lambda item:(-item[1],item[0])))
    return dict(unit='Mapped features; a campus may have several points. No current operating status inferred.',points=len(rows),counties=counts('county'),places=counts('place'),facility_source=url,place_source=purl,cases=rows)
