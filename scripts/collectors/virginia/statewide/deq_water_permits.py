import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
#!/usr/bin/env python3
"""Rebuild Virginia DEQ GIS/permit tracker project histories. Default is offline."""
import lib.net as netfetch
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / 'cache/history/water'
DEFAULT_CONFIG = collector_data('virginia/statewide/deq_water_permits','sources.json')
CFG = None
CURRENT = re.compile(r'\bdata[\s-]*cent(?:er|re)s?\b', re.I)
VPT = 'https://permits.virginia.gov/Permit/'
COLS = 'applicationNumber applicantName agent facility agency programType permitType permitNumber locality applicationReceivedDate status'.split()

def dump(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def get(url, form=None):
    headers = {'Accept': '*/*'}
    if form is not None:
        headers.update({'X-Requested-With':'XMLHttpRequest','Referer':VPT+'Search'})
    return netfetch.request(url, data=form, headers=headers, timeout=120).body

def urls(item, layer):
    return (f'https://www.arcgis.com/home/item.html?id={item}',
            f'https://hub.arcgis.com/api/v3/datasets/{item}_{layer}/downloads/data?format=csv&spatialRefId=4326')

def get_vpt(term):
    # Public /Permit/Search table, all agencies and all statuses. Its search also
    # covers agents; association is independently tested on facility/applicant below.
    form = dict(primarySearch=term, applicationStatus='', start=0, length=100, draw=1)
    form.update({'order[0][column]':0,'order[0][dir]':'asc',
                 'search[value]':'','search[regex]':'false'})
    for i, col in enumerate(COLS):
        for k,v in [('data',col),('name',col[:1].upper()+col[1:]),('orderable','true'),('searchable','true'),('search][value',''),('search][regex','false')]:
            form[f'columns[{i}][{k}]'] = v
    rows = []
    while True:
        page=json.loads(get(VPT+'SearchDatatable',form))
        count=int(page['recordsFiltered'])
        if count > 10000: raise RuntimeError('VPT result unexpectedly large; review search')
        batch=page['data']
        rows.extend(batch)
        if len(rows) == count: break
        if not batch or len(rows)>count: raise RuntimeError('inconsistent VPT pagination')
        form.update(start=len(rows),draw=form['draw']+1)
    if len({r['id'] for r in rows}) != count: raise RuntimeError('VPT repeated rows during pagination; retry')
    return {'query':term, 'count':count,'data':rows}

def fetch():
    CACHE.mkdir(parents=True,exist_ok=True)
    for key,(item,layer,_) in CFG['sources'].items():
        _,url=urls(item,layer)
        meta=json.loads(get(f'https://www.arcgis.com/sharing/rest/content/items/{item}?f=json'))
        if meta.get('id')!=item or 'deq' not in (meta.get('owner') or '').lower(): raise RuntimeError('unrecognized publisher/item')
        raw=get(url)
        if b'OBJECTID' not in raw[:256]: raise RuntimeError('unexpected GIS export: '+key)
        (CACHE/(key+'.csv.gz')).write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
        dump(CACHE/(key+'.item.json'),meta)
    dump(CACHE/'gis-retrieval.json', {'retrieved_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'source': 'official ArcGIS Hub CSV snapshots'})
    fetch_vpt()

def fetch_vpt():
    raw=[get_vpt(term) for term in CFG['vpt_search']]
    dump(CACHE/'vpt-search.json',raw)
    dump(CACHE/'vpt-retrieval.json', {'retrieved_utc': dt.datetime.now(dt.timezone.utc).isoformat()})

def iso(s):
    return dt.date.fromisoformat(s[:10].replace('/','-')).isoformat() if s else None

def matches(fields, locality):
    for field,value in fields:
        if CURRENT.search(value or ''): return field, 'direct text'
        for name,alias in CFG['aliases'].items():
            if re.search(r'\b'+re.escape(name)+r'\b',value or '',re.I) and alias['locality'].lower() in locality.lower():
                return field,alias['url']
    return None

def agency_geo(authority):
    if not authority or authority=='DEQ': return 'Virginia (local jurisdiction unverified)'
    return authority.replace(' Co.', ' County')+', VA'

def build():
    records=[]; audits={}
    for key,(item,layer,kind) in CFG['sources'].items():
        meta=json.loads((CACHE/(key+'.item.json')).read_text())
        raw=gzip.decompress((CACHE/(key+'.csv.gz')).read_bytes())
        ds=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        if not ds or len({r['OBJECTID'] for r in ds})!=len(ds):raise ValueError('GIS source identity '+key)
        url,download=urls(item,layer)
        dataset='VA DEQ — '+' '.join(meta['title'].split())
        matches_by_number={}
        for r in ds:
            if key=='stormwater':
                cols=['SWC_LOC_NAME','SWC_NATURE','SWC_OPE_NAME'];num=r['SWC_PERMIT_NO']
                loc=r['VSMP_AUTHORITY']+' '+r['SWC_LOC_CITY']
            else:
                cols=['FAC_NAME']+(['APPLICANT'] if key=='sswd' else []);num=r.get('PERMIT_NO') or r.get('SSWD_NP_PERMIT_NO') or r.get('VAP_PMT_NO')
                loc=r.get('FIC_DESCRIPTION') or r.get('COUNTY') or ''
            hit=matches([(k,r[k]) for k in cols],loc)
            if hit and num:matches_by_number.setdefault(num,{})[r['OBJECTID']]=hit
        n0=len(records); linked=0
        for r in ds:
            oid=r['OBJECTID'];n=r.get('SWC_PERMIT_NO') or r.get('PERMIT_NO') or r.get('SSWD_NP_PERMIT_NO') or r.get('VAP_PMT_NO')
            if not n or n not in matches_by_number:continue
            hit=matches_by_number[n].get(oid); detail={}
            if hit:detail.update(match_field=hit[0],match_basis=hit[1],match_value=r[hit[0]])
            else:
                linked+=1
                detail.update(match_basis='same source permit number as a matching row',first_matching_object_id=next(iter(matches_by_number[n])))
            date=None;role='date not supplied in register'; ident=oid
            if key=='stormwater':
                status=r['SWC_APP_STATUS_CD']; name=r['SWC_LOC_NAME'];ident=r['SWC_ID'];loc=agency_geo(r['VSMP_AUTHORITY'])
                detail.update(authority=r['VSMP_AUTHORITY'],site_city_label=r['SWC_LOC_CITY'],action_code=r['SWC_ACTIVITY'],classification_code=r['SWC_CLASSIFICATION'])
                # Use explicit signature and receipt fields; neither proves an issue date.
                for col,lt in [('SWC_TERM_DATE','termination date'),('SWC_COVERAGE_LETTER_SENT_DATE','issue date (coverage letter sent)'),('SWC_APP_RECD_DT','application received') if status.endswith(('IN_PROG','SUBMIT')) else ('SWC_APP_SIGNED_DT','signed date'),('SWC_APP_RECD_DT','application received')]:
                    if r[col]:date=iso(r[col]);role=lt;break
                detail['dates']={k:iso(r[k]) for k in ('SWC_APP_EFF_DT','SWC_APP_EXP_DT','SWC_APP_RECD_DT','SWC_APP_SIGNED_DT','SWC_TERM_DATE','SWC_COVERAGE_LETTER_SENT_DATE') if r[k]}
                for k in ('SWC_DISTURB_ACRES','SWC_DEVEL_ACRES'):
                    if r[k]:detail[k]=r[k]
            else:
                name=r['FAC_NAME'];loc=r.get('FIC_DESCRIPTION') or r.get('COUNTY') or ''
                loc=loc+', VA' if loc else 'Virginia (local jurisdiction unverified)'
                status=r.get({'vwp_gp':'VWP_GP_CLASSIFICATION','vwp_ip':'VWP_CLASSIFICATION','sswd':'SSWD_CLASSIFICATION','vwp_np':'VWP_NP_IS_OPEN','vpdes_outfalls':'VAP_TYPE'}[key]) or ''
                ident=n if key!='vpdes_outfalls' else r['OUTFALL_ID']
                if key=='sswd' and r['APPROVAL_DATE']:date=iso(r['APPROVAL_DATE']);role='determination approval'
                if key=='vpdes_outfalls':
                    detail.update(outfall=r['OUTFALL_ID'],permit_type=r['VAP_TYPE']);status=''
            detail['portal_row_id_at_capture']=oid
            records.append(dict(id='va-water-'+key+'-'+ident,dataset=dataset,jurisdiction=loc,record_no=n,project=(name or '(unnamed)').strip(),kind=kind,status=status or 'Not supplied',date=date,date_role=role,url=url,source_url=download,locator=f'Layer {layer}; {n}',details=detail))
        audits[key]=dict(dataset=dataset,url=url,download_url=download,rows_scanned=len(ds),matched_source_rows=len(records)-n0-linked,rows_linked_by_number=linked,unique_record_numbers=len(matches_by_number),csv_bytes=len(raw),csv_sha256=hashlib.sha256(raw).hexdigest())
    cache=(CACHE/'vpt-search.json').read_bytes()
    searches=json.loads(cache);unique={a['id']:a for group in searches for a in group['data']}
    kept=0
    for idx,r in sorted(unique.items()):
        if r['programType'] not in CFG['vpt_environmental_programs']:continue
        hit=matches([(k,r[k]) for k in ('facility','applicantName')],r['locality'] or '')
        if not hit:continue
        kept+=1
        records.append(dict(id=f'va-water-vpt-{idx}',dataset='Virginia Permit Transparency — environmental applications',jurisdiction=(r['locality']+', VA') if r['locality'] else 'Virginia (local jurisdiction unverified)',record_no=r['applicationNumber'] or r['permitNumber'] or str(idx),project=r['facility'] or '(unnamed)',kind=r['permitType'],status=r['status'] or 'Not supplied',date=iso(r['applicationReceivedDate']),date_role='application received',url=VPT+'Details/'+str(idx),source_url=VPT+'Search',locator=f'Application ID {idx}; '+(r['programType'] or ''),details=dict(program=r['programType'],agency=r['agency'],permit_number=r['permitNumber'],application_number=r['applicationNumber'],permit_status=r['permitStatus'],match_basis=hit[1],match_field=hit[0],match_value=r[hit[0]])))
    audits['vpt']=dict(url=VPT+'Search',queries={q['query']:q['count'] for q in searches},distinct_returned=len(unique),environmental_matches=kept,sha256=hashlib.sha256(cache).hexdigest())
    assert len({r['id'] for r in records})==len(records), 'Duplicate source record identity'
    assert all(r['url'].startswith('https://') and r['locator'] and r['record_no'] for r in records)
    records.sort(key=lambda r:r['id'])
    digests={k:v.get('csv_sha256') or v.get('sha256') for k,v in audits.items()}
    return records, dict(records=len(records), source_audits=audits, source_sha256=digests, retrieval={k:json.loads((CACHE/(k+'-retrieval.json')).read_text()) for k in ('gis','vpt')})

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--refresh',action='store_true');ap.add_argument('--refresh-vpt',action='store_true')
    ap.add_argument('--config',type=Path,default=DEFAULT_CONFIG,help='Virginia source mapping, aliases, VPT filters')
    ap.add_argument('--cache',type=Path,default=CACHE,help='Source snapshot directory')
    ap.add_argument('--output',type=Path,default=series_path('water'),help='Output record array')
    ap.add_argument('--manifest',type=Path,default=collector_data('virginia/statewide/deq_water_permits','manifest.json'),help='Audit, hash and retrieval-time JSON')
    ap.add_argument('--verify',action='store_true',help='Fail on stale output or source hashes; no writes')
    opt=ap.parse_args()
    CFG=json.loads(opt.config.read_text()); CACHE=opt.cache
    if opt.verify and (opt.refresh or opt.refresh_vpt): ap.error('--verify cannot refresh')
    if opt.refresh:fetch()
    elif opt.refresh_vpt:fetch_vpt()
    records, manifest=build()
    for path,obj in ((opt.output,records),(opt.manifest,manifest)):
        if opt.verify:
            if obj!=json.loads(path.read_text()): raise SystemExit(f'Source/content differs from {path.name}; rebuild and review')
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            dump(path,obj)
    print(f'{len(records)} records; '+('verified from cached source bytes' if opt.verify else 'built'))
