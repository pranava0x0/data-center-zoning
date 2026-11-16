"""Build a repeatable geography worklist and lightweight map from Census/CISA."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, hashlib, io, json, math, re
from collections import defaultdict, Counter
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
import xml.etree.ElementTree as ET
R = Path(__file__).resolve().parents[2]
STATES = 'VA TX OH LA NV AZ NM MS TN IN'.split()
GAZ = 'https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_{}_national.zip'
MAP = 'https://www2.census.gov/geo/tiger/GENZ2025/kml/cb_2025_us_{}_20m.zip'
DOT = 'https://raw.githubusercontent.com/cisagov/dotgov-data/main/current-full.csv'
def norm(s):
    return re.sub(r'[^a-z0-9 ]','',s.casefold()).strip()
def main(refresh=False):
    provenance = []
    def fetch(name, url):
        p = R/'cache/geo'/name
        p.parent.mkdir(exist_ok=True, parents=True)
        if refresh or not p.exists():
            b=urlopen(url,timeout=45).read();p.write_bytes(b)
        b=p.read_bytes()
        provenance.append(dict(url=url,file=str(p.relative_to(R)),sha256=hashlib.sha256(b).hexdigest()))
        return b
    dot=csv.DictReader(io.StringIO(fetch('dotgov.csv',DOT).decode('utf-8-sig')))
    domains=defaultdict(list)
    for d in dot:
        if d['Domain type'] in ('City','County','Township'):
            domains[d['State'],norm(d['Organization name'])].append(d['Domain name'])
    inventory=[]; counts=Counter()
    for kind in ['state','counties','place','cousubs']:
        z=ZipFile(io.BytesIO(fetch(kind+'.zip',GAZ.format(kind))))
        raw=z.read(z.namelist()[0]).decode('utf-8-sig')
        for d in csv.DictReader(io.StringIO(raw),delimiter='|'):
            name,st=d['NAME'],d['USPS']
            if kind=='place' and (d['FUNCSTAT'] not in ('A','B','C') or d['LSAD']=='57'):continue
            if kind=='cousubs' and d['FUNCSTAT'] not in ('A','B','C'):continue
            if st not in ('PR',): counts[kind]+=1
            if st not in STATES:continue
            g=d['GEOID']; keys={norm(name)}
            for suf in (' city',' town',' village',' municipality',' township',' County',' Parish',' borough'):
                if name.lower().endswith(suf.lower()):
                    keys.add(norm(suf.strip()+' of '+name[:-len(suf)]))
            urls=sorted({v for k in keys for v in domains[st,k]})
            inventory.append(dict(state=st,geoid=g,layer=kind,name=name,lat=d['INTPTLAT'],lon=d['INTPTLONG'],
                                  domain_candidates='|'.join(urls)))
    with (R/'data/jurisdictions.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=inventory[0]);w.writeheader();w.writerows(inventory)
    shapes={}
    for kind in ['state','county']:
        z=ZipFile(io.BytesIO(fetch('map_'+kind+'.zip',MAP.format(kind))))
        xml=ET.fromstring(z.read(next(i for i in z.namelist() if i.endswith('.kml'))))
        features=[]
        for p in xml.findall('.//{*}Placemark'):
            a={s.attrib['name']:s.text for s in p.findall('.//{*}SimpleData')}
            if a['STUSPS'] not in STATES and (kind=='county' or a['STUSPS'] in ('AK','HI','PR','GU','AS','MP','VI')):continue
            rings=[]
            for ring in p.findall('.//{*}LinearRing/{*}coordinates'):
                points=[]
                for item in ring.text.split():
                    lon,lat=map(float,item.split(',')[:2])
                    points.append([round(lon,3),round(lat,3)])
                rings.append(points)
            features.append([a['STUSPS'],a['GEOID'],a.get('NAMELSAD',a['NAME']),rings])
        shapes[kind]=features
    (R/'viewer/geography.js').write_text('window.GEOGRAPHY='+json.dumps(shapes,separators=(',',':'))+';\n')
    (R/'data/geography_sources.json').write_text(json.dumps({'sources':provenance,'national_frame_rows_by_layer_excluding_pr':counts},indent=2)+'\n')
    print(len(inventory),'geographies;',sum(bool(d['domain_candidates']) for d in inventory),'with domain candidates')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');main(p.parse_args().refresh)
