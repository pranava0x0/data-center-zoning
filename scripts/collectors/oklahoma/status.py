import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='OK':return None
    ds=r['dataset'];k=r['kind'];day=date.fromisoformat(r['date']) if r.get('date') else None
    if ds=='Oklahoma DEQ final data-center instruments':
        if 'determination' in k:return no('Air applicability determination; no independent permit issuance inferred.','decision')
        reg='OK:state-npdes' if k.startswith('OPDES') else 'OK:deq-water-works' if 'line construction' in k.lower() else 'OK:deq-air'
        return perm(reg,'unconfirmed','DEQ lists this numbered instrument as issued; validity at cutoff unverified.',day)
    if ds=='Oklahoma DEQ permit applications':return app()
    if ds=='Tulsa Metropolitan Area Planning Commission staff reviews':return no('Staff recommendation, not a council or planning commission decision.','observation')
    return None
