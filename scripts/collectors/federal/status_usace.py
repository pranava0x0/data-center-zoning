"""Classify affirmative USACE decisions at DA-file resolution; e.g. an AJD is not a project authorization."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    ds=r.get('dataset')
    if ds=='US Army Corps of Engineers district public notices':return app()
    if ds!='US Army Corps of Engineers regulatory public actions':return None
    d=r.get('details') or {};view=d.get('orm_view','');s=r['status']
    if d.get('superseded_original') and view=='issued':return perm(r['state']+':USACE:ORM','historical','The district expressly describes the original permit as expired.',date.fromisoformat(r['date']))
    if view=='issued' and s in ('Issued With Special Conditions','Issued Without Special Conditions') or view=='wrda' and s in ('Verified With Special Conditions','Verified Without Special Conditions'):
        return perm(r['state']+':USACE:ORM','unconfirmed','USACE records an issued individual permit or verified general permit under this DA file. Current effectiveness is not reported.',date.fromisoformat(r['date']) if r.get('date') else None)
    if view=='pending':return app()
    if view=='jds':return no('Jurisdictional determination establishes geographic scope, not authorization to conduct the work.','decision')
    if view=='nepa_ea':return no('Environmental assessment milestone; publication, completion or a permit-end workflow date alone does not establish permit issuance.','observation')
    return no('Unmapped Corps status; not promoted to a permit.','unknown')
