"""South Carolina permit history: combines the sources below into output/history/south_carolina/history.json. Offline by default;
--refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import argparse
from datetime import datetime
from collections import Counter
from lib.archive import NamedArchive as Archive
from collectors.south_carolina import des_air_permits as des, dhec_groundwater_permits as dhec
A=Archive('SC')
S={**des.S,**dhec.S}
def refresh():
 A.geom();des.download(A);dhec.download(A);A.seal()
def build():
 A.verify();out=[]
 def date(s):return datetime.strptime(s,'%B %d, %Y').date().isoformat()
 def add(n,no,proj,where,kind,status,dt,role,loc):
  out.append(dict(id='sc-'+no.lower()+'-'+str(len(out)),state='SC',record_no=no,project=proj,dataset='South Carolina DES air permitting files',jurisdiction=where,kind=kind,status=status,date=date(dt),date_role=role,url=S[n],source_url=S[n],locator=loc,details=dict(issuer='South Carolina Department of Environmental Services',county=where,archive='cache/history/sc/'+n,archive_sha256=A.files[n]['sha256'])))
 des.rows(A,add);out.extend(dhec.rows(A))
 lib.files.dump(series_path('sc'),out);lib.files.dump(collector_data('south_carolina','validation.json'),dict(events=len(out),kinds=dict(Counter(r['kind'] for r in out)),geography=A.rank()));print(len(out),'SC events')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
