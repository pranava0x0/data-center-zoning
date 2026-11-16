"""Conservative state + EPA permit interpretations; shared hook expected by permit_status."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det, epa
from datetime import date
import json, re
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='MS':return None
    ds=r['dataset'];s=r['status'];d=det(r);dayval=day(r.get('date'))
    if ds=='EPA ICIS-NPDES permit versions':return epa(r,cutoff,perm,no)
    if ds=='Southaven Board of Aldermen planning decisions':return no('Municipal subdivision/design vote rather than a construction permit.','decision')
    if ds!='Mississippi DEQ enSearch facility permits':return None
    if s=='Draft Permit Public Comment Period Ends':return no('Draft comment milestone, not a final decision.','notice')
    if s in ('Additional Information Requested from Applicant','Permit Application Received','Notice of Intent for General Permit Coverage Received'):return app()
    if s in ('Coverage Terminated','Permit Issued','Coverage Issued','Listed under Active Permits Available Online','Listed under Active Coverages Available Online'):
        n=r['record_no'];reg='MS:npdes' if n.startswith('MSR') else 'MS:deq-air'
        if s=='Coverage Terminated':
            if d.get('active_section_same_day'):return perm(reg,'unconfirmed','MDEQ lists coverage as both active and terminated on this date; conflicting federal EFF label is not proof of validity.',dayval)
            return perm(reg,'historical','MDEQ explicitly records termination.',dayval)
        if d.get('active_section_same_day'):return perm(reg,'active','MDEQ explicitly lists the issued number under Active Permits/Coverages.',dayval)
        return perm(reg,'unconfirmed','Issued, but continuing validity is unverified.',dayval)
    return None
