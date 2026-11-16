"""Arkansas permit history: combines the DEQ Permit Data System / air-permit and Little Rock sources below into
output/history/arkansas/history.json and data/history/arkansas/validation.json. Offline replay by default; --refresh re-downloads every
source; --probe runs the DEQ facility-name search."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import json, sys
from lib.records import CUT, save
from collectors.arkansas import deq_permit_data_system as deq, little_rock_building_permits as little_rock
SOURCES=(deq, little_rock)
def make():
 rows,stats=deq.rows();lr,lr_counts=little_rock.rows();rows+=lr
 save('AR',rows);v=collector_data('arkansas','validation.json');o=json.loads(v.read_text());o.update(cutoff=CUT,**stats,municipal_source_rows=lr_counts);v.write_text(json.dumps(o,indent=2)+'\n')
if __name__=='__main__' and '--probe' in sys.argv:
 for t in ['Data Center','Datacenter','Data Centre','Server Farm','Willowbend']:
    print(t,deq.fetchterm(t),flush=True)
if __name__=='__main__' and '--probe' not in sys.argv:
 if '--refresh' in sys.argv:
    for s in SOURCES:s.download()
 make()
