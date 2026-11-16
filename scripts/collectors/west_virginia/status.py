import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
 if r.get('dataset')!='West Virginia DEP project files':return None
 if r['kind']=='Construction stormwater enforcement':return no('Enforcement order on an unnamed stormwater coverage. Neither issuance of a new permit nor revocation.','enforcement')
 if 'application' in r['kind'].lower() and r['status']!='Public comment notice':return app()
 return no('Public participation milestone, not a final authorization.','notice')
