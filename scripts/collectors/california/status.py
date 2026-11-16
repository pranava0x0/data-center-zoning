"""Conservative status of a California permit, distinguished from votes and CEC generator exemptions."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='CA':return None
    ds=r['dataset'];s=r['status'];d=det(r);when=day(r.get('date'));issue=day(d.get('issue_date'))
    if ds=='CEC small power plant exemption docket':
        return app() if s=='Application docketed' else no('State generator-licensing exemption decision filing; not a local permit.','decision')
    if ds.endswith(' public land-use proceedings'):
        return no('Agenda entry; no substantive decision verified.','agenda') if s=='On agenda' else no('Motion on a land-use matter; inspect motion text for the actual recommendation, appeal or decision.','decision')
    if ds=='San José C.3 stormwater project tracking':return no('Stormwater project phase, not a discharge authorization.','tracking')
    if ds=='San José planning register':return app() if s in ('New','Pending','Under Review') else no('Planning case/status can reflect entitlements, zoning or review; an issued instrument is not independently established.','decision')
    if ds=='San José building permit registers':
        if not issue or issue>cutoff:return app()
        if s=='Active' and not day(d.get('final_date')):return perm('CA:san-jose-building','active','City current source explicitly lists an issued permit as Active; duplicate inspection-list entry is not counted twice.',issue)
        return obs('CA:san-jose-building',historical=('expired',),held=('underinspection','active'),when=issue)
    if ds=='Los Angeles issued building and trade permits':
        if not issue:return no('Issued-register event without a documented issue date.','unknown')
        return obs('CA:los-angeles-building',historical=('permit finaled','permit expired','permit closed','cofo issued'),issued=('issued',),held=('cofo in progress',),when=day(d.get('status_date')) or issue)
    if ds=='San Francisco building permits':
        if not issue:return app()
        return obs('CA:san-francisco-building',historical=('complete','expired','withdrawn','cancelled','revoked'),issued=('issued',),when=day(d.get('status_date')) or issue)
    return None
