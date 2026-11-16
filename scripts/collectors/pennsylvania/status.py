import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import details
def classify(r,cutoff,perm,no,app,obs):
 if r.get('dataset')!='Pennsylvania DEP data center permit tracker':return None
 d=details(r);cat=d.get('program');kind=d.get('authorization','');num=r.get('record_no');s=r['status']
 if s in ('Received','Pending','Returned','Withdrawn'):return app()
 if s!='Issued':return None
 if cat in ('Environmental Cleanup & Brownfields','WPC Act 537 Municipal Sewage Planning') or 'registration' in kind.lower():return no('DEP records a plan, registration or determination, not a separately identified issued permit.','decision')
 if not num:return no('Issued authorization without a permit number.','unnumbered')
 return perm('PA:dep-'+cat.lower(),'unconfirmed','DEP lists the instrument as issued; its current validity is not reported.')
