"""Register a checked history state or supplement and a named browser smoke test.
python3 scripts/pipeline/register_release.py SERIES STATE [CASE_NUMBER EXPECTED_HOST] [--path history/<collector path>.json]
A new series is added to data/history/series.csv with its path under output/ (the path column is what series_path() reads).
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, csv, json
from urllib.parse import urlsplit
import lib.discovery as c
def register(series,st,path='',case='',host=''):
 source=c.OUT/path if path else series_path(series);records=c.read(source,[])
 if not records or {r.get('state') for r in records}!={st}:raise ValueError('State source missing/inconsistent')
 if case and not any(r.get('record_no')==case and urlsplit(r['url']).hostname==host for r in records):raise ValueError('Source case not found')
 reg=c.R/'data/history/series.csv'
 with reg.open() as f:entries=list(csv.DictReader(f))
 if not any(e['series']==series and e['state']==st for e in entries):
    if any(e['series']==series for e in entries):raise ValueError('Series reused')
    if not path:raise ValueError('A new series needs --path (relative to output/, e.g. history/texas/history.json)')
    with reg.open('a') as f:csv.writer(f,lineterminator='\n').writerow([series,st,path])
 if case:
    path=c.R/'data/history/pipeline/uat_cases.json';items=c.read(path,[]);key='case_'+series
    if not any(x[2]==key for x in items):items.append([st,case,key,host]);c.dump(path,items)
    p=c.R/'tests/uat-budgets.json';b=c.read(p,{});b['journeys'][key]=dict(actions=5,swipes=0,navigations=0);c.dump(p,b)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('series');ap.add_argument('state');ap.add_argument('case',nargs='?',default='');ap.add_argument('host',nargs='?',default='');ap.add_argument('--path',default='');a=ap.parse_args();register(a.series,a.state,a.path,a.case,a.host)
