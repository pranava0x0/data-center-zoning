"""Government CKAN catalogue -> published CSV -> numbered permit files, with optional dates.
Blank permit-case fields remain inventory-only; never substitute a planning case for an issued permit.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.net as netfetch
import argparse, csv, datetime as dt, io, json, re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode,urlsplit
import lib.discovery as c
def clean(value):
    s=(value or '').strip()
    return '' if s.casefold() in ('<null>','null','n/a','none') else s
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=Path,default=collector_data('multistate/ckan_catalog_csv','config.json'));ap.add_argument('--fetch',action='store_true');ap.add_argument('--output',type=Path,default=series_path('pwc'));args=ap.parse_args()
    cfg=json.loads(args.config.read_text());slug=cfg['slug']
    if not re.fullmatch('[a-z0-9-]+',slug):raise ValueError('Invalid feed slug')
    directory=c.R/'cache/history'/slug;directory.mkdir(exist_ok=True,parents=True);manifest=directory/'manifest.json'
    def save(url):
        b=netfetch.get(url,timeout=25,limit=c.LIMIT)
        if len(b)>c.LIMIT:raise ValueError('size limit')
        h=c.digest(b);(directory/h).write_bytes(b);return dict(url=url,sha256=h)
    def body(ref):
        raw=(directory/ref['sha256']).read_bytes()
        if c.digest(raw)!=ref['sha256']:raise ValueError('Archive mismatch')
        return raw
    if args.fetch:
        cat=None;links=[cfg['download_url']] if cfg.get('download_url') else []
        if not links:
            cat=save(cfg['catalog']);data=json.loads(body(cat))
            links=[r['url'] for r in data['result']['resources'] if r['format'].lower()=='csv']
        if len(links)!=1 or urlsplit(links[0]).hostname!=cfg['allowed_download_host']:raise ValueError('unexpected export: inspect updated catalogue')
        m=dict(catalog=cat,csv=save(links[0]),captured_utc=c.now());c.dump(manifest,m)
    m=json.loads(manifest.read_text());rdr=csv.DictReader(io.StringIO(body(m['csv']).decode('utf-8-sig')));keys=cfg['map']
    if not set(keys.values())<=set(rdr.fieldnames):raise ValueError('source columns changed')
    records=list(rdr);groups=defaultdict(list)
    for row in records:
        case=clean(row[keys['case']])
        if case:groups[case].append(row)
    out=[]
    for case,rr in sorted(groups.items()):
        values=lambda k:sorted({clean(r[keys[k]]) for r in rr if clean(r[keys[k]])})
        dates=[dt.date.fromisoformat(d[:10].replace('/','-')).isoformat() for d in values('date')]
        if any(d>cfg['edition_date'] for d in dates):raise ValueError('post-edition occupancy; version the export')
        ids=values('object_id')
        src=cfg['layer']+'/query?'+urlencode(dict(objectIds=','.join(ids),outFields=','.join(keys.values()),returnGeometry='false',f='pjson'))
        out.append(dict(id=slug+'-'+case,dataset=cfg['dataset'],jurisdiction=cfg['jurisdiction'],record_no=case,project=' / '.join(values('title')) or case,kind=cfg['kind'],status=' / '.join(values('status')) or 'Not supplied',date=dates[0] if len(dates)==1 else None,date_role=cfg['date_role'],url=src,source_url=m['csv']['url'],locator=keys['case']+' '+case,details=dict(object_ids=ids,occupancy_dates=dates,planning_cases=values('land_use_file'),sha256=m['csv']['sha256'])))
    if not out:raise ValueError('No named permit files; inspect edition before publishing')
    c.dump(args.output,out);c.dump(args.output.with_name(args.output.stem+'_coverage.json'),dict(source=m['csv']['url'],catalog=cfg['catalog'],inventory_rows=len(records),without_permit_number=sum(not clean(r[keys['case']]) for r in records),distinct_permit_files=len(out),capture=m['captured_utc']))
    print(len(out),'numbered permits from',len(records),'building inventory rows')
if __name__=='__main__':main()
