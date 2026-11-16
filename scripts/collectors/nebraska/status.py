import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='NE':return None
 ds,s,d=r['dataset'],r['status'],det(r);dt=day(r.get('date'))
 if ds=='Nebraska DWEE facility air files':
    if s in ('DEQ Application','DEQ Draft Permit','Applicant submittal (indexed as DEQ Issued Permit)'):return app()
    if s=='DEQ Public Notice':return no('Published notice is not an issued authorization.','notice')
    if s=='DEQ Notification':return no('Owner notification of construction commencement, not authorization.','other')
    if s=='DEQ Issued Permit':
        if d.get('superseded_by') and day(d.get('supersession_date')) and day(d['supersession_date'])<=cutoff:return perm('NE:dwee-air:'+d['facility_id'],'historical','A later issued instrument expressly supersedes this permit in full: '+d['superseded_by']+'.',day(d['supersession_date']),stable_no=d['permit_number'])
        if d.get('permit_number') and dt:return perm('NE:dwee-air:'+d['facility_id'],'unconfirmed','Agency classifies as issued and the document identifies the permit number; current validity has not been established.',dt,stable_no=d['permit_number'])
        return no('Agency indexed an issued permit; underlying permit number not verified.','unnumbered')
 if ds=='Lincoln nonresidential building permits' and s=='Issued' and dt and d.get('issue_date'):return perm('NE:lincoln-building','unconfirmed','Explicit Issued status and issuance date; no current validity finding.',dt)
 if ds=='Papillion City Administrator permit reports':
    if s=='Issued':return no('City reports issuance but no stable number specific to the trade is published.','unnumbered')
    if s=='Revisions Required':return app()
 if ds=='Lincoln-Lancaster County air permits' and s=='issued' and dt:return perm('NE:llchd-air','unconfirmed','County health authority expressly cites a previous numbered issuance in its subsequent project document.',dt)
 return None
