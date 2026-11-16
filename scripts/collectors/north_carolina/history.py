"""North Carolina permit history: combines the Durham, Raleigh, NC DEQ air register and Charlotte/DEQ casebook sources
below into output/history/north_carolina/history.json. Offline replay by default; --refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import argparse
from collections import Counter
import lib.files
from collectors.north_carolina.evidence_store import A
from collectors.north_carolina import durham_building_permits as durham, raleigh_building_permits as raleigh, deq_air_permits as deq, charlotte_deq_casebook as casebook
SOURCES=(deq, durham, raleigh)
def refresh():
 A.geom()
 for s in SOURCES:s.download()
 A.seal()
def build():
 A.verify();events=[];held=[]
 durham.rows(events,held);raleigh.rows(events,held);deq.rows(events);casebook.rows(events)
 lib.files.dump(series_path('nc'),sorted(events,key=lambda r:r['id']));lib.files.dump(collector_data('north_carolina','exclusions.json'),held);lib.files.dump(collector_data('north_carolina','validation.json'),dict(events=len(events),datasets=dict(Counter(r['dataset'] for r in events)),held=len(held),geography=A.rank()));print(len(events),'events',len(held),'held')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
