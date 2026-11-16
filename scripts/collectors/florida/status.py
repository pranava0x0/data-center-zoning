"""Florida issued instruments vs application, local agenda and project events."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='FL':return None
    ds=r['dataset'];s=r['status'];d=r.get('details') or {};day=date.fromisoformat(r['date']) if r.get('date') else None
    if ds=='City of Miami iBuild permits':
        if d.get('permit_no') and day and s in ('Expired','Final','Revoked'):return perm('FL:miami-ibuild','historical','City issued permit with explicit terminal status '+s+'.',day)
        if not d.get('permit_no'):return app()
    if ds=='Miami-Dade County building permits' and s=='Finalized':return perm('FL:miami-dade-building','historical','Issued permit with BPSTATUS F (Finalized in county metadata).',day)
    if ds=='South Florida Water Management District permit register' and s=='Approved':
        exp=date.fromisoformat(d['expires']) if d.get('expires') else None
        if exp and exp<cutoff:return perm('FL:sfwmd','historical','District approved permit with recorded permit expiration before cutoff; not proof of project closure.',day)
        return perm('FL:sfwmd','unconfirmed','Approved, numbered instrument in district permit register. Continued validity not independently verified.',day)
    if ds=='South Florida Water Management District application actions':return no('District application action; older amendments and pending files do not establish a separate issued permit.','observation')
    if ds=='Town of Eatonville council agendas':return no('Council agenda, not a development agreement vote or an issued permit.','observation')
    return None
