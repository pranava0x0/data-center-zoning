"""Build national administrative worklists separately from legal findings. No API credentials."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, collections, csv, gzip, hashlib, io, json, re, zipfile
from pathlib import Path
from urllib.parse import urlencode,urljoin
import openpyxl
import lib.discovery as c
from lib.url_archive import Archive
R=c.R;OUT=R/'data/national';BASE='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/'
ISLAND={'60':'AS','66':'GU','69':'MP','78':'VI','72':'PR'}
def write(name,cols,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
def build(fetch=False):
    OUT.mkdir(exist_ok=True);a=Archive('national',fetch,owner='pipeline/national_frame');areas={};aux=[]
    def add(st,layer,id,name,func,lat,lon,url):
        k=st,layer,id
        if k in areas:raise ValueError('Repeated geography '+str(k))
        areas[k]=dict(state=st,layer=layer,geoid=id,name=name,funcstat=func,lat=lat,lon=lon,source=url)
    zsrc=json.loads((R/'data/geography_sources.json').read_text())['sources'];byfile={Path(x['file']).name:x for x in zsrc}
    for k in ('state','counties','place','cousubs'):
        p=R/'cache/geo'/(k+'.zip');ref=byfile[p.name]
        if hashlib.sha256(p.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('Gazetteer changed')
        with zipfile.ZipFile(p) as z:fs=csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig')),delimiter='|')
        for d in fs:
            layer=k
            if k=='place' and (d['FUNCSTAT'] not in ('A','B','C') or d['LSAD']=='57'):layer='statistical place'
            elif k=='cousubs' and d['FUNCSTAT'] not in ('A','B','C'):layer='other county subdivision'
            add(d['USPS'],layer,d['GEOID'],d['NAME'],d.get('FUNCSTAT',''),d['INTPTLAT'],d['INTPTLONG'],ref['url'])
    def table(service,layer,where,fields):
        path=BASE+service+'/MapServer/'+str(layer)+'/query?';q=dict(f='json',where=where)
        ids=a.json(path+urlencode(dict(**q,returnIdsOnly='true')))['objectIds'];items=[]
        for off in range(0,len(ids),200):
            u=path+urlencode(dict(f='json',objectIds=','.join(map(str,sorted(ids)[off:off+200])),outFields='OBJECTID,'+fields,returnGeometry='false'));d=a.json(u)
            if d.get('exceededTransferLimit'):raise ValueError('Partial layer')
            items.extend(f['attributes'] for f in d['features'])
        if len(items)!=len(ids) or {x['OBJECTID'] for x in items}!=set(ids):raise ValueError('TIGERweb records differ')
        return items,path.split('/query?')[0]
    for service,layer,k in [('State_County',18,'state'),('State_County',19,'counties'),('Places_CouSub_ConCity_SubMCD',8,'territory subdivisions'),('Places_CouSub_ConCity_SubMCD',11,'place'),('Places_CouSub_ConCity_SubMCD',12,'statistical place')]:
        rows,source=table(service,layer,"STATE IN ('60','66','69','78')",'STATE,GEOID,NAME,FUNCSTAT,INTPTLAT,INTPTLON')
        for d in rows:add(ISLAND[d['STATE']],k,d['GEOID'],d['NAME'],d['FUNCSTAT'],d['INTPTLAT'],d['INTPTLON'],source)
    for layer,k in [(13,'Tribal subdivision'),(14,'Federal reservation'),(15,'Off-reservation trust land'),(16,'State reservation'),(17,'Hawaiian home land'),(18,'Alaska Native village statistical area'),(19,'Oklahoma tribal statistical area')]:
        rows,source=table('AIANNHA',layer,'1=1','GEOID,NAME,FUNCSTAT,INTPTLAT,INTPTLON')
        for d in rows:
            aux.append(dict(layer=k,geoid=d['GEOID'],name=d['NAME'],funcstat=d['FUNCSTAT'],lat=d['INTPTLAT'],lon=d['INTPTLON'],source=source))
    write('jurisdictions.csv','state layer geoid name funcstat lat lon source'.split(),areas.values())
    write('tribal_areas.csv','layer geoid name funcstat lat lon source'.split(),aux)
    count=collections.Counter((r['state'],r['layer']) for r in areas.values())
    f=R/'cache/local-screen/census-gov.zip';meta='https://www.census.gov/data/datasets/2022/econ/gus/public-use-files.html'
    with zipfile.ZipFile(f) as z:w=openpyxl.load_workbook(io.BytesIO(z.read(next(k for k in z.namelist() if k.endswith('.xlsx')))),read_only=True)
    bodies=[]
    for sheet in w.sheetnames:
        it=iter(w[sheet].values);hdr=next(it)
        for v in it:
            d=dict(zip(hdr,v))
            if d.get('IS_ACTIVE')!='Y' or not d.get('UNIT_NAME'):continue
            bodies.append(dict(state=d['STATE'],class_name=sheet,government_id=d['CENSUS_ID_GIDID'],name=d['UNIT_NAME'],classification=d.get('UNIT_TYPE'),site=d.get('WEB_ADDRESS'),county_area=d.get('COUNTY_AREA_NAME'),authority='Not established by roster',source=meta))
    write('government_units.csv','state class_name government_id name classification site county_area authority source'.split(),bodies)
    scores={r['state']:r for r in csv.DictReader((R/'data/national_counts_2026-10.csv').open())}
    assert len(scores)==52 and all(int(x['total'])==sum(int(x[t]) for t in ('operating','under_construction','planned')) for x in scores.values())
    states=[r for r in areas.values() if r['layer']=='state'];assert len(states)==56
    queue=[]
    for r in states:
        st=r['state'];d=scores.get(st,{});rank=1+sum(int(p['total'])>int(d['total']) for p in scores.values()) if d else ''
        queue.append(dict(state=st,name=r['name'],geoid=r['geoid'],count_rank=rank,listed_count=d.get('total'),operating=d.get('operating'),under_construction=d.get('under_construction'),planned=d.get('planned'),county_equivalents=count[st,'counties'],places=count[st,'place'],townships_or_subdivisions=count[st,'cousubs']+count[st,'territory subdivisions'],source='https://dcmap.us/states/' if d else 'Not listed in directory'))
    write('priority.csv',list(queue[0]),sorted(queue,key=lambda x:(x['count_rank'] or 999,x['state'])))
    c.dump(OUT/'audit.json',dict(state_levels=len(states),geographic_references=len(areas),layers=collections.Counter(r['layer'] for r in areas.values()),governments_by_sheet=collections.Counter(r['class_name'] for r in bodies),tribal_geographic_references=len(aux),roster_hash=hashlib.sha256(f.read_bytes()).hexdigest(),government_source=meta,territories=ISLAND,notes='Includes 50 states, DC and five inhabited territories. Minor Outlying Islands have no equivalent municipal permitting frame in these sources. Tribal polygons are not a list of sovereign governments; special districts require a separate authority check.'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');build(p.parse_args().fetch)
