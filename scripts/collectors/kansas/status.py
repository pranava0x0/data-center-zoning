import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')=='KS' and r['dataset']=='City of De Soto project and planning records':return no('Municipal development agreement, site plan, plat, or agenda action; no building or environmental permit established.','observation' if r['status']=='On agenda' else 'decision')
    return None
