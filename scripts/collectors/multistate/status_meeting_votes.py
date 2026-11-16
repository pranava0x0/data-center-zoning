import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
 ds=r.get('dataset')
 if ds=='Susquehanna River Basin Commission consumptive use approvals' and r['status']=='Approved':return perm('PA:srbc-consumptive','unconfirmed','Interstate basin commission approval with conditions; continued validity not independently confirmed.')
 if ds=='Rhode Island DEM emergency generator permits' and r['status']=='Issued':return perm('RI:dem-generator','unconfirmed','Dated state generator permit; current validity not reported.')
 if ds=='Guam Hybrid Land Use Commission minutes' and r['status']=='Approved with conditions':
    if r['kind']=='Conditional use permit':return perm('GU:ghluc-cup','unconfirmed','Commission voted to approve the conditional use; subsequent validity was not reported.')
    if r['kind']=='Height variance':return no('Variance vote, distinct from the conditional use permit.','decision')
 if ds in ('Delaware Coastal Zone Act decisions','Lewiston City Council development agreements'):return no('Project decision, appeal or development-agreement vote; not an issued construction permit.','decision')
 if ds=='Palm Beach County Project Tango decisions':return no('County land-use proceeding, not an issued building permit.','decision')
 return None
