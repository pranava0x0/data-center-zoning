import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='AR':return None
 ds,s,d,dt=r['dataset'],r['status'],det(r),day(r.get('date'))
 if ds=='Arkansas DEQ air permitting and PDS':
    if s in ('Received','Admin Complete'):return app()
    if s=='Issued' and dt:return perm('AR:deq-air','active' if d.get('pds_status')=='Active' else 'unconfirmed','Signed underlying air permit; PDS status: '+str(d.get('pds_status') or 'not reported')+'.',dt,stable_no=re.sub('-R[0-9]+$','',r['record_no']))
 if ds=='Arkansas DEQ other air requests':return app() if s=='Received' else no('Miscellaneous request disposition, not a separately numbered final air operating permit.','decision')
 if ds=='Arkansas PDS regulated storage tank records':return no('Regulated storage tank facility/program entry; no issuance or current permit indicator.','registration')
 if ds=='Little Rock municipal permits' and dt and s=='Closed':return perm('AR:little-rock-construction','historical','City reports Closed, with an individual issue date.',dt)
 return None
