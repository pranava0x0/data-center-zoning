import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day
def classify(r,cutoff,perm,no,app,obs):
 if r.get('dataset')=='South Carolina DHEC groundwater review':
  if r['kind']=='Groundwater withdrawal permit':return perm('SC:dhec-water','unconfirmed','State board names this groundwater permit; issuance date, term and current status not established.')
  return no('Challenge to permit withdrawn; review event, not permit revocation.','decision')
 if r.get('dataset')!='South Carolina DES air permitting files':return None
 if r['kind']=='Synthetic minor air construction permit':return perm('SC:des-air','unconfirmed','DES issued this numbered construction permit; operating approval and continued validity are not established.',day(r['date']))
 if r['kind']=='Air permit application' or r['kind']=='Expedited application review':return app()
 return no('Related decision or public notice; no separate permit number established.','determination' if r['status']=='Approved' else 'notice')
