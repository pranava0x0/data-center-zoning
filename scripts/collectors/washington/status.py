import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
 if r['dataset']=='Washington Ecology Quincy air construction dockets':
    if r['kind']=='Air permit application':return app()
    if r['status']=='Rescinded':return perm('WA:ecy-noc','historical','Ecology labels this order rescinded.')
    if r['status']=='Issued':return perm('WA:ecy-noc','unconfirmed','Ecology identifies an approval order; continued validity is not established.')
 return None
