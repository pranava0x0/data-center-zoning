import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='ID':return None
    if r['dataset']=='Idaho DEQ issued air permits and notices':
        if r['status']=='Issued':return perm('ID:DEQ-air-PTC','unconfirmed','Named in issued register with a number and issue date; no current disposition supplied.',date.fromisoformat(r['date']))
        return app()
    if r['dataset']=='City of Kuna planning and zoning cases':return app() if r['status'] in ('Staff report','Design review requested') else no('Design-review action; not an issued building permit.','decision')
    return None
