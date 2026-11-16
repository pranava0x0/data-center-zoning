"""Hawaii permit history: combines the sources below into output/history/hawaii/history.json. Offline by default;
--refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import argparse
from collections import Counter
from lib.archive import NamedArchive as Archive
from collectors.hawaii import honolulu_building_permits as honolulu, hawaii_environmental_notices as envnotices
A=Archive('HI')
SOURCES=(honolulu, envnotices)
def refresh():
 A.geom()
 for s in SOURCES:s.download(A)
 A.seal()
def build():
 A.verify();o=honolulu.rows(A)+envnotices.rows(A)
 lib.files.dump(series_path('hi'),o);lib.files.dump(collector_data('hawaii','validation.json'),dict(events=len(o),datasets=dict(Counter(x['dataset'] for x in o)),geography=A.rank()));print(len(o),'HI events')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
