"""Tennessee status adapter: current records vs dated actions; do not infer a permit from an application number."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='TN':return None
    ds=r['dataset'];s=r['status'];day=date.fromisoformat(r['date']) if r.get('date') else None
    if ds=='EPA ICIS-NPDES permit versions':
        from lib.status import epa
        mapped=epa(r,cutoff,perm,no)
        if mapped:return mapped
        if s=='ADC' and day:return perm('TN:npdes','unconfirmed','ICIS administratively continued version; count permit identity, not as confirmed active.',day)
        return no('ICIS status not mapped.','unknown')
    if ds=='Metro Nashville Codes Permit History':
        if not day:
            if s in ('DONE','EXPIRED'):return no('The city closed the file but supplies no issue date.','closed_file')
            if s in ('OPEN','HOLD','APPLIED','PENDING'):return app()
            return no('No issue date. Even DONE or EXPIRED can occur on an application file.','unknown')
        if s in ('DONE','EXPIRED','CANCELLED'):return perm('TN:nashville-codes','historical','Issue date and terminal city register status '+s+'.',day)
        if s=='ISSUED':return perm('TN:nashville-codes','unconfirmed','Metro documents issuance, but does not independently report continued validity.',day)
        return no('Unmapped Metro Codes status.','unknown')
    if ds=='Franklin Municipal Planning Commission site plans':return no('Project site-plan vote, not an issued building permit.','decision')
    if ds=='Shelby County Health Department air permits' and s=='Issued':return perm('TN:shelby-air','unconfirmed','Signed, time-limited construction authorization; later operating status not established.',day)
    return None
