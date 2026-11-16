import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day
def classify(r,cutoff,perm,no,app,obs):
 if r['dataset']!='Vermont Act 250 permit docket':return None
 k=r['kind']
 if k=='Act 250 land use permit amendment':return perm('VT:act250','unconfirmed','Signed Commission permit amendment; continued effectiveness not independently established.',day(r['date']))
 if k=='Low-risk construction stormwater discharge coverage':return perm('VT:dec-const','historical','Authorization states it expired April 11, 2019; a future reapplication would be a distinct record.',day(r['date']))
 if k=='Underground injection control applicability':return no('Agency found no reason to require this permit for the project.','determination')
 return app() if 'draft' in k.lower() or r['status'] in ('Received','Deemed complete') else no('Notice or response deadline, not an issued permit.','notice')
