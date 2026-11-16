"""Connecticut permit history: combines the sources below into output/history/connecticut/history.json. Offline by default;
--refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import argparse, re
from collections import Counter
from lib.archive import NamedArchive as Archive
from collectors.connecticut import hartford_building_permits as hartford, csc_siting_petitions as csc, norwalk_site_plan_decisions as norwalk
A=Archive('CT')
def refresh():
 A.geom();csc.download(A);hartford.download(A);norwalk.download(A);A.seal()
def build():
 A.verify();events=[]
 def add(ds,no,pr,j,kind,status,dt,role,url,loc,**d):
  events.append(dict(id='ct-'+re.sub('[^a-z0-9]+','-',no.lower())+'-'+str(len(events)),state='CT',dataset=ds,record_no=no,project=pr,jurisdiction=j,kind=kind,status=status,date=dt,date_role=role,url=url,locator=loc,details=d))
 held=hartford.rows(A,add);csc.rows(A,add);norwalk.rows(A,add)
 lib.files.dump(series_path('ct'),events);lib.files.dump(collector_data('connecticut','validation.json'),dict(events=len(events),datasets=dict(Counter(a['dataset'] for a in events)),held_hartford_ids=held,geography=A.rank()));print(len(events),'CT events')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
