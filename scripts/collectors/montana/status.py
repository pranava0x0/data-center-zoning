import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='MT':return None
    if r['dataset']=='Missoula County Bonner project review':return app() if r['status']=='Deemed incomplete' else no('Owner withdrew; county says project will not move forward.','decision')
    if r['dataset']=='Montana DEQ public water supply review':return app()
    if r['dataset']=='Montana Sage Grouse Habitat Conservation Program consultations':return no('Program consultation or completion of habitat review; not a well or water right permit.','observation')
    if r['dataset']=='Yellowstone County commission project agenda':return no('Road-use agreement recommendation, not an issued construction permit.','observation')
    return None
