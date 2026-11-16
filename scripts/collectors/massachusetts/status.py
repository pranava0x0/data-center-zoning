import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='MA':return None
 ds,s,d,dt=r['dataset'],r['status'],det(r),day(r.get('date'))
 if ds=='Boston ISD approved building permits':
    if r['kind']=='Certificate of Occupancy':return no('The city designates this an occupancy certificate, not a construction permit.','decision')
    if not dt:return None
    if s not in ('Open','Closed','Issued','Stop work'):return None
    if s=='Closed':bucket,why='historical','Boston defines Closed as previously issued and expired.'
    elif s=='Open' and (day(d.get('expiration_date')) or cutoff)>=cutoff:bucket,why='active','Boston defines Open as issued and still valid, without a contradictory past expiration.'
    else:bucket,why='unconfirmed','Generic issuance, stopped work or Open with past printed expiration; current validity not confirmed.'
    return perm('MA:boston-isd',bucket,why,dt,stable_no=d.get('amends') or r['record_no'])
 if ds=='MassDEP Markley air approval and adjudication':
    if s=='issued' and dt:return perm('MA:massdep-air','unconfirmed','Dated agency decision establishes issuance; appeal affirmance does not issue another permit.',dt)
    return no('Air-permit appeal filing, recommendation or final disposition.','decision')
 if ds=='MassDEP prior certifications cited in MEPA':return no('Explicit state certification but no identified unique certification number.','unnumbered')
 if ds=='Massachusetts MEPA project certificates':return no('Environmental review notice or certificate for a multi-municipality distribution line.','notice' if s=='Notice of Project Change' else 'decision')
 return None
