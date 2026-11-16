import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='ND':return None
    if r['dataset']=='North Dakota DEQ air permits to construct':
        if r['status']=='Issued':return perm('ND:deq-air-ptc','unconfirmed','Issuer explicitly confirms numbered permit and issuance date; current validity not shown.',date.fromisoformat(r['date']))
        return app()
    if r['dataset']=='North Dakota DEQ discharge permit notices':return app()
    if r['dataset'] in ('Dickey County Water Resource District proceedings','City of Fargo commission proceedings'):return no('Local jurisdictional action or unnumbered permit report; not a distinct verified permit identity.','observation')
    return None
