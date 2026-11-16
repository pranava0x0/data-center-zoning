import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='UT':return None
    ds,s=r['dataset'],r['status'];t=day(r.get('date'))
    if ds=='Utah DAQ AOsIssuedAll' and s=='Approval Order issued' and t and t<=cutoff:
        return perm('UT:daq-approval-order','unconfirmed','Explicit numbered state order, including modifications; current validity not independently established.',t)
    if ds=='Utah DAQ AOsOutForCmt':return no('Intent to approve is a draft for public review.','notice')
    if ds in ('Utah DAQ NOI_Pub_H','Utah DAQ notice receipts cited in approval orders'):return app()
    if ds=='Bluffdale Planning Commission decisions':return no('Site plan approved with conditions; separate building, road and sewer approvals remain.','decision')
    if ds=='Salt Lake City building permit workflow' and not det(r).get('registered_issue_date'):return app()
    return None
