"""Supplement row citations with verified archival receipts. A grouped case may span multiple source batches."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
from lib.paths import collector_data
import csv, collections, gzip, hashlib, io, json, re
import lib.discovery as c
import collectors.virginia.loudoun_county.building_and_zoning_gis as loud
def run():
 with (c.OUT/'permit_history.csv').open() as fp:events=list(csv.DictReader(fp))
 verified={}
 receipts=[];meth=collections.Counter();miss=collections.Counter()
 def add(r,method,url,sha,locator,archive_path=None):
    if not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError(r['id']+' invalid checksum')
    receipts.append(dict(id=r['id'],method=method,source_url=url,sha256=sha,locator=locator,archive_path=archive_path));meth[method]+=1
 cfg=c.read(loud.DEF_CONF,{})
 li={}
 for layer in cfg['layers']:
    oid=layer['oid'];index={}
    for batch in c.read(loud.INDEX,{})['layers'][layer['key']]['batches']:
        for f in loud.load_blob(batch)['features']:
            a=f['attributes'];assert a[oid] not in index;index[a[oid]]=(batch,str(a.get(layer['number']) or ''))
    li[layer['label']]=index
 monthly={z['url']:z for z in c.read(collector_data('virginia/loudoun_county/monthly_reports','manifest.json'),{})['reports'].values()}
 seen_pdf=set();water={};aud=c.read(collector_data('virginia/statewide/deq_water_permits','manifest.json'),{})['source_audits']
 for k,d in aud.items():
    if not d.get('csv_sha256'):continue
    b=gzip.decompress((c.R/'cache/history/water'/(k+'.csv.gz')).read_bytes());assert c.digest(b)==d['csv_sha256']
    with io.TextIOWrapper(io.BytesIO(b),encoding='utf-8-sig') as fp:
        ids={str(next(v for key,v in row.items() if key.upper()=='OBJECTID')) for row in csv.DictReader(fp)}
    water[d['dataset']]=(d,ids)
 import collectors.oregon.portland_maps as port
 po={}
 for ref in c.read(port.P,{})['batches']:
    for feat in port.S.read(ref)['features']:
        a=feat['attributes'];po[str(a['OBJECTID'])]=(ref,str(a['FOLDERKEY']))
 air=c.R/'cache/history/air'
 air_ref=air/'official-indexed-cells.json';cells=c.read(air_ref,[]);alt=air/'vpt-indexed-details.json';alts={x['record_no']:x for x in c.read(alt,[])}
 def receipt(path):
    if path not in verified:verified[path]=c.digest(path.read_bytes())
    return verified[path]
 def archived(r,d):
    if not d.get('archive'):return False
    path=(c.R/d['archive']).resolve()
    if c.R not in path.parents or not path.is_file():return False
    expected=d.get('archive_sha256') or d.get('extract_sha256')
    if not expected:return False
    if receipt(path)!=expected:
        if path.suffix!='.gz' or c.digest(gzip.decompress(path.read_bytes()))!=expected:raise ValueError('Archive hash mismatch: '+str(path))
    add(r,'collector archive verified on disk',r['source_url'] or r['url'],expected,r['locator'],d['archive']);return True
 vpt={}
 for name,path in [('Virginia Permit Transparency — environmental applications',c.R/'cache/history/water/vpt-search.json'),('Virginia Permit Transparency — DEQ air applications',air/'vpt-rolling-search.json')]:
    vpt[name]=(path,{str(x['id']):x for query in c.read(path,[]) for x in query['data']})
 for r in events:
    reg=r['dataset'];d=json.loads(r['details'])
    if r['source_sha256']:
        add(r,'collector receipt',r['source_url'] or r['url'],r['source_sha256'],r['locator'])
    elif archived(r,d):pass
    elif reg=='Virginia DEQ issued data-center air permits':
        num=r['record_no']
        if d['evidence_method']=='government application tracker (approval; not issuance)':
            entry=alts[num];assert entry['url']==r['source_url'];add(r,'matched official detail excerpt (not original PDF)',entry['url'],receipt(alt),r['locator'],str(alt.relative_to(c.R)))
        else:
            source=d.get('indexed_page') or r['source_url'];valid=[record for block in cells if block['source_url']==source for record in block['lines'] if len(record.split('|'))==6 and record.split('|')[1].strip()==num]
            assert valid,(num,source);add(r,'matched number in archived official register excerpts',source,receipt(air_ref),r['locator'],str(air_ref.relative_to(c.R)))
    elif reg in vpt:
        path,index=vpt[reg];i=r['url'].rsplit('/',1)[-1];x=index[i];assert r['record_no'] in (str(x.get('applicationNumber') or '').strip(),str(x.get('permitNumber') or '').strip())
        add(r,'matched application ID and number in official search response',r['url'],receipt(path),r['locator'],str(path.relative_to(c.R)))
    elif reg=='Norwalk site plan surety decisions':
        path=collector_data('connecticut','norwalk.json');assert any(x['url']==r['url'] and x['date']==r['date'] and x['status']==r['status'] for x in c.read(path,[]));add(r,'matched municipal minutes excerpt (not original PDF)',r['url'],receipt(path),r['locator'],str(path.relative_to(c.R)))
    elif reg in li:
        keys=collections.defaultdict(list);refs={}
        for oid in d['source_object_ids']:
            batch,num=li[reg][oid];assert not num or num==r['record_no']
            refs[batch['sha256']]=batch;keys[batch['sha256']].append(oid)
        for sha,oids in keys.items():add(r,'matched GIS objects in archived response',refs[sha]['url'],sha,'Object IDs: '+', '.join(map(str,oids)))
    elif reg=='Loudoun monthly building reports':
        z=monthly[r['source_url']];sha=z['sha256']
        if sha not in seen_pdf:
            b=(loud.CACHE/(sha+'.pdf')).read_bytes();assert len(b)==z['bytes'] and c.digest(b)==sha;seen_pdf.add(sha)
        add(r,'county monthly PDF used by parser',z['url'],sha,r['locator'])
    elif reg in water:
        z,ids=water[reg];m=re.search(r'OBJECTID\s+(\d+)',r['locator']);assert m and m[1] in ids and z['download_url']==r['source_url']
        add(r,'matched object in archived agency CSV',z['download_url'],z['csv_sha256'],r['locator'])
    elif reg=='PortlandMaps all permits':
        z,folder=po[str(d['object_id'])];assert folder==str(d['folderkey']);add(r,'matched GIS objects in archived response',z['url'],z['sha256'],r['locator'])
    else:miss[reg]+=1
 with (c.OUT/'receipts/evidence.csv').open('w',newline='') as fp:
    w=csv.DictWriter(fp,fieldnames=list(receipts[0]));w.writeheader();w.writerows(receipts)
 ids=set(r['id'] for r in receipts);assert len(ids)+sum(miss.values())==len(events)
 c.dump(c.OUT/'receipts/evidence_quality.json',dict(history_rows=len(events),with_receipt=len(ids),without_row_checksum=len(events)-len(ids),receipts=len(receipts),method_counts=meth,missing_by_register=miss,scope='A collector receipt can be an archived file, source response or excerpt. The capture method is recorded in the source-specific documentation. Rows absent here still carry a public citation and locator.'))
 print(len(ids),'of',len(events),'records linked to archived receipts')
 if miss:raise SystemExit('History records without archival receipts; see output/receipts/evidence_quality.json')
if __name__=='__main__':run()
