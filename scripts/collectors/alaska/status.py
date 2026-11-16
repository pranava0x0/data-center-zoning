import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day
def classify(r,cutoff,perm,no,app,obs):
 ds=r['dataset']
 if ds=='Anchorage permit records':
  if r['status']=='Deleted':return no('Deleted case; no independent evidence of issuance.','application')
  if 'changeordr' in r['kind'].lower() or 'change order' in r['kind'].lower():return no('Revision to an existing permit rather than a new instrument.','decision')
  return obs('AK:anchorage-building',historical=('closed',),issued=('issued',),when=day(r['date']))
 if ds=='Anchorage inspection and review actions':return no('Discipline review or inspection of the parent permit.','inspection')
 if ds=='Alaska DNR project decisions':return no('Application, lease offer, or unsigned proposed entry authorization; no executed instrument established.','decision' if r['status']=='Final finding and decision' else 'application')
 if ds=='FERC preliminary permit applications':return app()
 return None
