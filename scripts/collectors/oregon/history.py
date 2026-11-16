"""Oregon permit history: combines the DEQ air permit documents and the county planning commission casebook below into
output/history/oregon/history.json, with exclusions, rankings and validation in data/. Offline replay by default; --refresh
re-downloads the DEQ register and permits and rebuilds the OCR transcripts."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import argparse, json
from collections import Counter
import lib.files
from collectors.oregon import deq_air_permits as deq, planning_commission_casebook as casebook
A=deq.A
def build():
 events,held,reg=deq.events();events.update(casebook.rows())
 out=sorted(events.values(),key=lambda r:r['id']);lib.files.dump(series_path('or'),out);lib.files.dump(collector_data('oregon','exclusions.json'),held);lib.files.dump(collector_data('oregon','validation.json'),dict(events=len(out),datasets=dict(Counter(a['dataset'] for a in out)),undated=sum(not a['date'] for a in out),source_files=len(A.files),geography=A.rank(),candidate_rows=len(reg),excluded=len(held)));print(len(out),'events;',len(held),'excluded.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:deq.refresh();deq.refresh_ocr()
 build()
