import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import det, day
def classify(r,cutoff,perm,no,app,obs):
 if r['dataset']=='Hawaii environmental review notices':return no('Environmental review record; neither a grading nor building permit.','determination')
 if r['dataset']!='Honolulu historical building permits':return None
 d=det(r)
 if not d.get('issue_date'):return app()
 if r['status']=='Permit application closed' and d.get('completed_date'):return perm('HI:hnl-building','historical','Registry gives both issuance and completion and records closed status.',day(d['completed_date']))
 return perm('HI:hnl-building','unconfirmed','Numbered issued permit; historical registry ends 2025-06-30 and does not establish current validity.',day(r['date']))
