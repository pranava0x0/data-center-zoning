"""Minnesota city permit numbers and review-only proceedings are distinct."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='MN':return None
    d=r['dataset'];s=r['status']
    if d=='Minnesota EQB environmental review notices':return no('EQB environmental-review document or notice; adoption and final environmental review do not authorize construction.','notice')
    if d=='Chaska Cloud HQ municipal decisions':return no('Project-specific council/commission planning action. No independently numbered construction permit supplied.','decision')
    if d=='Minneapolis CCS construction permits':
        x=det(r);t=day(x.get('issue_date'));end=day(x.get('completion_date'))
        if s=='Closed' and end and end<=cutoff:return perm('MN:minneapolis-ccs','historical','City reports Closed with completed final inspection.',end)
        if s=='Issued' and t and t<=cutoff:return perm('MN:minneapolis-ccs','unconfirmed','The dated city issue is verified; continued validity is not independently established.',t)
    return None
