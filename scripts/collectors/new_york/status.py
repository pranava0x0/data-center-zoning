"""Classify New York source series separately; never turn a DOB job number or planning vote into a unique permit."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='NY':return None
    ds=r.get('dataset');s=r.get('status');t=day(r.get('date'))
    if ds in {'Somerset Planning Board project decisions','Niagara Falls project decisions'}:
        return no('Siting or environmental review action, distinct from issuance of a numbered construction/operating permit.','decision')
    if ds=='NYC DOB building job filings':
        return no('DOB job filing and document; actual permit must be verified in the issuance register.','application')
    if ds=='NYC DOB electrical job register':
        return no('Electrical filing ID, including amendments. An issue date on the job does not establish an independently identified permit.','application')
    if not t or t>cutoff:return None
    if ds=='NYC BIS permit issuance' and s in ('ISSUED','RE-ISSUED'):
        return perm('NY:nyc-bis','unconfirmed','Dated original issue or reissue. BIS does not establish a currently valid or closed permit.',t)
    if ds=='NYC DOB NOW approved building permits':
        if s=='Signed-off':return perm('NY:nyc-dob-now','historical','DOB reports Signed-off; a post-approval amendment may reopen work.',t)
        if s=='Permit Issued':return perm('NY:nyc-dob-now','unconfirmed','Issued in DOB NOW; expiration or a past issuance alone does not prove current validity.',t)
    if (ds,s) in {('New York DEC issued state facility air permits','Issued'),('New York DEC air permit modifications','Modification effective')}:
        return perm('NY:dec-air','unconfirmed','DEC issued or modified a numbered air permit. Current status is not independently certified by the register.',t)
    return None
