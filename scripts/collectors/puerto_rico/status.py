import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r['state']!='PR':return None
    if r['dataset']=='Puerto Rico Planning Board location consultations':return no('Location consultation clarification; not a new authorization.','decision')
    if r['dataset']!='Puerto Rico OGPe SuperSIP case register':return None
    c=r['details']['procedure_code']
    if c in ('PCO','PCOC','PGE','PCT','PU'):
        if r['status']=='EXPIRED':return perm('PR:OGPe:SuperSIP','historical','Issuer register explicitly marks this distinct instrument expired.',date.fromisoformat(r['date']))
        if r['status']=='PERMIT_APPROVED':return perm('PR:OGPe:SuperSIP','unconfirmed','Official OGPe register approves this numbered permit; continued validity not established.',date.fromisoformat(r['date']))
    if c in ('SRS','SRI','PCD','PCE','PCM'):return no('Recommendation or pre-consultation workflow; an approved referral is not permission to build.','decision')
    if c=='DEC':return no('Environmental categorical-exclusion determination; not itself a permit to construct.','decision')
    return None
