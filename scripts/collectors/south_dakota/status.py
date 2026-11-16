import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='SD':return None
    if r['dataset']=='Sioux Falls City Council published minutes and resolutions':return no('Council adopted rezoning or preliminary subdivision plan, not a construction permit.','decision')
    if r['dataset']=='South Dakota Public Utilities Commission electric dockets':return app() if r['status']=='Filed' else no('Electric provider assignment vote/order only; no land or building permit issued.','decision')
    if r['dataset']=='McPherson County conditional use proceedings':return app() if r['status']=='Application supplied' else no('Conditional use board discussed deferral in unapproved minutes; no permit issued.','observation')
    return None
