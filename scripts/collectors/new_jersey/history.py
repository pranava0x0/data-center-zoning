"""New Jersey permit history: combines the state, authority and township sources below into output/history/new_jersey/history.json.
Offline replay by default; --refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, D, R
import argparse
import lib.files
from lib.archive import NamedArchive as Archive
from collectors.new_jersey import njdep_bulletin_permits as njdep, njsea_zoning_certificates as njsea, bridgewater_planning_agenda as bridgewater
A=Archive('NJ')
def refresh():
 A.geom();meta=njdep.download(A);njsea.download(A);A.seal(meta)
def build():
 A.verify();seen,pages_scanned=njdep.rows(A);seen.update(njsea.rows(A));seen.update(bridgewater.rows())
 rows=sorted(seen.values(),key=lambda a:a['id']);lib.files.dump(series_path('nj'),rows);from collections import Counter
 lib.files.dump(collector_data('new_jersey','validation.json'),dict(events=len(rows),source_pages_screened=pages_scanned,datasets=dict(Counter(r['dataset'] for r in rows)),statuses=dict(Counter(r['status'] for r in rows)),geography=A.rank(),hashed_files=len(A.files)+1));print(len(rows),'events;',pages_scanned,'bulletin pages.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
