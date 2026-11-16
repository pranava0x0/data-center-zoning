import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
 ds=r['dataset']
 if ds=='Hartford building and trade permits':
  if not det(r).get('issue_date'):return app()
  return obs('CT:hartford',historical=('closed','final inspection complete','closed - complete'),issued=('issued',),when=day(r['date']))
 if ds=='Connecticut Siting Council data center docket':return no('Fuel-cell siting petition, no-certificate ruling, or commissioning notice; no siting certificate issued.','determination')
 if ds=='Norwalk site plan surety decisions':return no('Release of project surety; not issuance of a new building permit.','decision')
 return None
