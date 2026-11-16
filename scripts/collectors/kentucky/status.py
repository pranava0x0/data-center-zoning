import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='KY':return None
    if r['dataset']=='Louisville Metro development plans':return no('A development-plan record is not a building or environmental permit.','decision' if r['status']=='APPROVED' else 'observation')
    if r['dataset']=='Oldham County Project Lincoln withdrawals':return no('County reports the application withdrawn.','closed_file')
    if r['dataset']=='Kentucky PSC project information requests':return no('Request for evidence in an energy docket.','observation')
    return None
