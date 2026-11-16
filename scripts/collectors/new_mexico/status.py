"""Do not confuse a generator notification or air permit filing with an issued permit."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
    ds=r.get('dataset');s=r.get('status');role=r.get('date_role')
    if ds=='Albuquerque issued building permits' and s=='Issued' and role=='Issue date':
        return obs('NM:cabq-building',issued=('issued',))
    if ds=='Albuquerque air quality notifications' and s=='Notification issued':
        return no('City generator notification, not a construction or operating permit.','notice')
    if ds=='New Mexico Environment Department air proceedings':
        if s in {'Application complete','Application received','Application withdrawn','Application submitted','Application completeness letter'}:return app()
        if s in {'Hearing determination posted','Draft air permit','Preliminary determination'}:return no('Air docket notice or proposed decision; no final permit issued by this document.','notice')
    if ds=='EPA New Mexico construction stormwater coverage':
        from lib.status import details,iso
        d=details(r);when=iso(r.get('date'));end=iso(d.get('expiration_date'))
        if d.get('master_permit')!='NMR100000' or not when:return None
        if s in ('Terminated','Expired') and when<=cutoff:return perm('NM:epa-cgp','historical','EPA reports coverage '+s.lower()+'.',when,version=int(d['version']))
        if s=='Effective' and end and when<=cutoff<=end:return perm('NM:epa-cgp','active','EPA reports effective coverage within its stated permit term.',when,version=int(d['version']))
    return None
