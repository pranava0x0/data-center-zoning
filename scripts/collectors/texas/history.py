"""Texas government permit history and lab-point geography. Offline by default; --refresh fetches."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import argparse
from collections import Counter, defaultdict
from lib.files import dump, sha
from lib.net import req
from lib.terms import MATCH, patterns
from lib.text import isodate, Fields
import lib.arcgis as arcgis
import gzip, json, re
from urllib.parse import urlencode, quote
from collectors.texas.common import ROOT, C, CONFIG, MAN, cut, make_add
from collectors.texas import census_pnnl_rankings as geo, dallas_building_permits as dallas, austin_issued_construction_permits as austin, fort_worth_development_permits as fort_worth, san_antonio_building_permits as san_antonio, tdlr_accessibility_registrations as tdlr, abilene_site_plans as abilene
SOURCES=(geo, dallas, austin, fort_worth, san_antonio, tdlr, abilene)
def refresh():
    C.mkdir(parents=True,exist_ok=True);m={}
    for s in SOURCES:s.download(m)
    dump(MAN,{'cutoff':cut,'files':m})
def get_rows():
    m=json.loads(MAN.read_text())['files']
    for n,el in m.items():
        if sha((C/n).read_bytes())!=el['sha256']:raise ValueError('Archive changed: '+n)
    rows=[];counts=Counter();bykey={};exclusions=[]
    add=make_add(m,rows,counts,bykey)
    for s in (dallas, austin, fort_worth, san_antonio, tdlr, abilene):s.rows(m,add,exclusions)
    if len(rows)!=len({r['id'] for r in rows}):raise ValueError('Duplicate published identifiers')
    by=defaultdict(list)
    for r in rows:
        assert r['state']=='TX' and all(r[field] for field in ('dataset','jurisdiction','record_no','project','kind','status','url','locator','source_sha256'))
        if r['date'] and not ('1950-01-01' < r['date'] <= cut):raise ValueError('Date outside source range: '+r['id'])
        by[r['dataset']].append(r)
    fw=fort_worth.coverage(m)
    stats={}
    for label,rr in by.items():
        dates=sorted(r['date'] for r in rr if r['date']);stats[label]={'records':len(rr),'unique_record_numbers':len({r['record_no'] for r in rr}),'date_roles':dict(Counter(r['date_role'] for r in rr)),'first_date':dates[0] if dates else None,'last_date':dates[-1] if dates else None}
    dump(collector_data('texas','validation.json'),{'cutoff':cut,'rows':len(rows),'datasets':stats,'dropped_rows':dict(counts),'keyword_nonmatches':len(exclusions),'archive_files_verified':len(m),'fort_worth_candidate_ids_reconciled':len(fw)})
    dump(collector_data('texas','exclusions.json'),exclusions)
    dump(series_path('tx'),sorted(rows,key=lambda r:(r['date'] or '',r['id']),reverse=True))
    print(Counter(r['dataset'] for r in rows),dict(counts),len(exclusions),'broad nonmatches')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
    if args.refresh:refresh()
    get_rows();geo.rankings()
