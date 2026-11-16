import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='NJ':return None
 ds=r['dataset'];s=r['status'];dt=day(r['date'])
 if ds=='NJDEP NJPDES bulletin':return obs('NJ:njdep-njpdes',historical=('revoked',),issued=('issued',),when=dt)
 if ds=='NJDEP land resource permitting':
  if r['kind']=='Freshwater wetlands line verification':return no('Delineation/verification determination, not authorization of construction.','determination') if s=='Issued' else app()
  if s in ('Approved','Issued'):return perm('NJ:njdep-landresource','unconfirmed','NJDEP records approval of this numbered permit action; continued validity not confirmed. Combined action counts once.',dt)
  return app()
 if ds in ('NJDEP treatment works applications','NJSEA zoning certificate case reviews'):return app()
 if ds=='NJDEP NJPDES proposed actions':return no('Draft/proposed stormwater action opened to public comment.','notice')
 if ds=='Bridgewater Township planning agenda':return no('Planning hearing agenda does not establish a decision.','agenda')
 return None
