"""Alabama permit history: combines the state and city sources below into output/history/alabama/history.json.
Offline replay by default; --refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import argparse
from collections import Counter
import lib.files
from lib.archive import NamedArchive as Archive
from collectors.alabama import adem_synthetic_minor_air as adem, huntsville_building_permits as huntsville
SOURCES=(adem, huntsville)
A=Archive('AL')
def refresh():
 A.geom()
 for s in SOURCES:s.download(A)
 A.seal()
def build():
 A.verify();out={**adem.rows(A),**huntsville.rows(A)}
 lib.files.dump(series_path('al'),sorted(out.values(),key=lambda r:r['id']));lib.files.dump(collector_data('alabama','validation.json'),dict(events=len(out),datasets=dict(Counter(r['dataset'] for r in out.values())),geography=A.rank()));print(len(out),'AL events')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
