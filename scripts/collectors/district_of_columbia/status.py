import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
 if r['dataset']=='District of Columbia building permit register' and r['date_role']=='Issue date':
    return obs('DC:dob-building',historical=('completed','expired'),issued=('permit issued',))
