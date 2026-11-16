"""Alaska permit history: combines the sources below into output/history/alaska/history.json. Default is hash-checked offline
replay from the sealed archive; --refresh re-downloads every source and reseals the archive."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import lib.files
import argparse
from collections import Counter
from collectors.alaska.evidence_store import A
from collectors.alaska import anchorage_permits as anchorage, dnr_land_decisions as dnr, ferc_preliminary_permits as ferc
def refresh():
 A.geom()
 dnr.download();ferc.download();anchorage.download()
 A.seal()
def build():
 A.verify();out=[];held=[]
 anchorage.rows(out,held);dnr.rows(out);ferc.rows(out)
 lib.files.dump(series_path('ak'),out);lib.files.dump(collector_data('alaska','validation.json'),dict(events=len(out),datasets=dict(Counter(a['dataset'] for a in out)),held=held,geography=A.rank()));print(len(out),'AK events')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
