import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='WI':return None
 ds,s,role=r['dataset'],r['status'],r['date_role'];dt=day(r.get('date'))
 if ds=='Wisconsin DNR air permit tracking':
    if role.startswith('application '):return app()
    if role=='public notice date':return no('Public notice milestone.','notice')
    if role=='permit decision date' and dt and dt<=cutoff and s in ('Active','Inactive'):
        n=r['record_no'];base=re.sub(r'-F\d+$','',n) if det(r).get('permit_type')=='FESOP' else re.sub(r'-R\d+$','',n)
        return perm('WI:dnr-air','active' if s=='Active' else 'historical','Air program explicitly labels this numbered instrument '+s+'.',dt,stable_no=base)
 if ds=='Mount Pleasant Plan Commission minutes':return no('Commission site-plan vote; does not certify building permit issuance or village-board adoption.','decision')
 if ds=='Wisconsin DNR Lighthouse campus review':
    if s in ('submitted a request','plans & specifications','request for coverage'):return app()
    if s=='public hearing held':return no('Public hearing on draft air permits.','notice')
    if s=='conveyed':return no('Agency affirms project coverage, but individual certificate numbers not established; grouped action carries no unique permit identity.','unnumbered')
    return no('Environmental review, project exemption, or agency determination.','decision')
 return None
