import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='WY':return None
    if r['dataset']=='City of Cheyenne public planning cases':return app()
    if r['dataset']=='Laramie County SmartGov planning permits':
        if r['status']=='Submitted':return app()
        return perm('WY:Laramie County:SmartGov-planning','unconfirmed','Portal identifies the issued permit or certificate. File closure and application expiry are not evidence of revocation or actual ongoing operation.',date.fromisoformat(r['date']))
    if r['dataset']=='Laramie County commissioners and planning commission':return no('Commission proceedings document a planning vote; separate from later portal issue events.','decision')
    return None
