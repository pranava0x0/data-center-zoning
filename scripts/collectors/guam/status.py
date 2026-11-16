import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
    if r['dataset']=='Guam interagency land-use referrals':return no('Individual agency recommendation on a commission case. No independent authorization shown.','decision')
    return None
