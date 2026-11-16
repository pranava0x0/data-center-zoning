import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import det, day
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='NC':return None
 d=det(r);ds=r['dataset'];s=r['status'];dt=day(r['date']);n=r['record_no']
 if ds=='NC DEQ active air permit register':
  exp=day(d.get('expiration_date'));dated=bool(dt and exp and dt<=cutoff<=exp)
  return perm('NC:deq-air','active' if dated else 'unconfirmed','DEQ active register lists this permit; '+('its issue and expiration dates span the cutoff.' if dated else 'printed expiration does not establish continued validity.'),dt,int(n[-2:]),n[:-2])
 if ds=='NC DEQ air application reviews':
  if s=='Existing Permit':return perm('NC:deq-air','historical','Older permit revision identified by DEQ; a later revision is listed by the same agency.',dt,int(n[-2:]),n[:-2])
  return app()
 if ds in ('NC DEQ air hearing notices','Charlotte rezoning petitions'):return no('Government hearing or rezoning case, not evidence of a building or air permit.','decision' if s in ('Approved','Withdrawn') else 'notice')
 if ds=='Durham City-County building permits':
  if not d.get('issue_date'):return app()
  return obs('NC:durham-building',historical=('co issued','void'),issued=('issued',),when=day(d.get('co_signoff_date')) or dt)
 if ds=='Raleigh building permits':
  if not d.get('issue_date'):return app()
  if s in ('Complete','INACTIVE (INSPECTIONS COMPLETED)') or d.get('status_mapped') in ('Permit Finaled','Occupancy'):return perm('NC:raleigh-building','historical','City reports construction inspections completed or permit finaled; this is not a claim about operation.',day(d.get('co_issue_date')) or dt)
  return perm('NC:raleigh-building','unconfirmed','Issue date available; continuing validity not established.',dt)
 return None
