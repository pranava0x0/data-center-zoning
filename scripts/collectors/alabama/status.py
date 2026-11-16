import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
 ds=r['dataset'];k=r['kind'];dt=day(r['date']);d=det(r)
 if ds=='Alabama ADEM synthetic minor air files':
  if k=='Synthetic minor operating permit':return perm('AL:adem-smop','unconfirmed','State analysis identifies a numbered permit on existing equipment; issue date and continuing validity are not established.')
  return app() if k.endswith('application') else no('Application public notice; no issuance established.','notice')
 if ds=='Huntsville building permits':
  if d.get('certificate_observed'):return perm('AL:huntsville-building','historical','City issued a subsequent numbered certificate of occupancy for this building permit.',day(d['co_date']))
  return perm('AL:huntsville-building','unconfirmed','City provides an issuance date but no current permit status.',dt)
 if ds=='Huntsville occupancy certificates':return perm('AL:huntsville-occupancy','unconfirmed','City records a distinct occupancy certificate number and date; present validity not confirmed.',dt)
 return None
