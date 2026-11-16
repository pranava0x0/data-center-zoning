import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det

def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='IA':return None
    ds,s=r['dataset'],r['status'];d=det(r);dt=day(r.get('date'))
    if ds=='West Des Moines City Council site plans':return no('Site plan vote, distinct from building permit issuance.','decision')
    if not dt or dt>cutoff:return None
    if ds=='Iowa DNR air construction equipment permit history' and s in {'Rescinded','Date Issued'} and d.get('plant_number') and d.get('base_permit'):
        return perm('IA:dnr-equipment:'+d['plant_number'],'historical' if s=='Rescinded' else 'unconfirmed','The register explicitly labels this version rescinded.' if s=='Rescinded' else 'Equipment issue or revision; no current status asserted.',dt,stable_no=d['base_permit'])
    if ds=='Iowa DNR signed Title V operating permits' and s=='Issued':return perm('IA:dnr-title-v','unconfirmed','Signed operating permit; check renewal, amendments and current status with issuer.',dt)
    if ds=='Council Bluffs Building Division issued permits' and s=='Issued':return perm('IA:council-bluffs-building','unconfirmed','Issued on a monthly city report; trade entries can share the city permit number.',dt)
    return None
