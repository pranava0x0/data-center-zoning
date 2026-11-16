import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import det, day
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='OR':return None
 if r['dataset']=='Local land-use compatibility finding in DEQ permit':return no('Local compatibility determination cited by DEQ; not a separately numbered permit.','determination')
 if r['dataset']=='Oregon planning commission cases':
  if r['kind']=='Zoning permit' and r['status']=='Approved':return perm('OR:morrow-zoning','unconfirmed','Commission confirms prior approval of numbered zoning permit; continuing validity not confirmed.',day(r['date']))
  return no('Planning decision or hearing record, no separately demonstrated permit issuance.','determination' if r['status']=='Approved' else 'agenda')
 if r['dataset']!='Oregon DEQ air permit documents':return None
 d=det(r);year=int(d['permit_year']);rev=day(r['date'])
 if r['status']=='NOT CURRENT':return perm('OR:deq-acdp','historical','DEQ historical register marks this version NOT CURRENT.',rev,year)
 if r['status']=='Issued permit':return perm('OR:deq-acdp','unconfirmed','Issued state permit from the pre-November 2024 system; newer renewals and continuing validity are not established.',rev,year)
 return None
