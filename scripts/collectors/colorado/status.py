"""Colorado: differentiate received service requests, permit documents, certificates and project appeals."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='CO':return None
    ds,s=r['dataset'],r['status'];t=day(r.get('date'))
    if ds=='Colorado APCD air permit application tracker':
        if s.startswith('Received: '):return no('Date is receipt. Service (including Final Approval) is the service requested, not issuance.','application')
        if s=='Permit issued on' and t and t<=cutoff:return perm('CO:apcd-air','unconfirmed','Dated permitIssuedOn in state tracker. This date may predate a later application; continued validity is unconfirmed.',t)
    if ds=='Colorado APCD public notices':return no('Proposed air permit open for public comment.','notice')
    if ds=='Colorado Springs land-use appeals':return no('Appeal proceeding on land-use approval, not a building/operating permit.','decision')
    if ds=='Aurora Building Division issued permit and certificates':
        if 'certificate' in r['kind'].lower():return no('Accessory-building occupancy certificate tied to underlying building permit, not another independently numbered permit.','decision')
        if s=='Issued' and t and t<=cutoff:return perm('CO:aurora-bldg','unconfirmed','Issuing department signed building permit; no proof of continued validity.',t)
    if ds=='Denver commercial permits at a verified data-center site':
        x=det(r);f=day(x.get('final_date'));c=day(x.get('cancel_date'))
        if c and c<=cutoff:return perm('CO:denver-commcon','historical','City reports a cancellation date for this issued permit.',c)
        if f and f<=cutoff:return perm('CO:denver-commcon','historical','City records a final date for the issued construction permit.',f)
        if t and t<=cutoff:return perm('CO:denver-commcon','unconfirmed','Actual city permit at a verified site. No current state or work narrative given.',t)
    return None
