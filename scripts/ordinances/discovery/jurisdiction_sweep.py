"""Run the Virginia discovery pattern on a verified jurisdiction roster (CSV).
Required columns: jurisdiction,url; optional geoid (string). Isolated from VA edition.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, csv, hashlib, json, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import lib.discovery as c
import ordinances.discovery.virginia_directory_sweep as va
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('roster',type=Path)
    p.add_argument('--name',required=True);p.add_argument('--refresh',action='store_true');a=p.parse_args()
    if not re.fullmatch('[a-z0-9][a-z0-9_-]{0,60}',a.name):p.error('name must be a lowercase slug')
    digest=c.digest(a.roster.read_bytes());rows=list(csv.DictReader(a.roster.open()))
    entries=[(r['jurisdiction'].strip(),c.address(r['url']),[r['geoid']] if r.get('geoid') else []) for r in rows]
    if not entries or len({n for n,u,g in entries})!=len(entries):raise ValueError('Use unique issuing jurisdictions within each roster')
    va.BASE=c.R/'cache/roster-sweeps'/a.name/digest;va.BASE.mkdir(exist_ok=True,parents=True)
    with ThreadPoolExecutor(max_workers=4) as p:results=list(p.map(lambda e:va.sweep(e,a.refresh),entries))
    c.dump(c.OUT/f'roster_{a.name}.json',dict(roster_sha256=digest,results=results))
if __name__=='__main__':main()
