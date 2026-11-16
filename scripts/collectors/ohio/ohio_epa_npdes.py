"""Ohio EPA Division of Surface Water NPDES permit registers (SurfaceWater/NPDES MapServer layers 0-7): facility-name screen."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt
from collectors.ohio.common import fetch_layer
def download(c,m,k,l):fetch_layer(c,m,k,l)
def utcday(ms):return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).date().isoformat() if ms is not None else None
def row(add,audit,state,k,l,meta,a,h0,hh,oid,url):
    npseen=state['npseen']
    num=a['ohio_epa_no'] or str(a.get('applicationid') or oid);dd=a.get('issue_date');ro='issue date' if dd is not None else 'effective date' if a.get('effective_date') is not None else 'date not reported'
    county=(a.get('county') or a.get('facility_county') or a.get('fp_county_name') or '').strip()
    if county and not county.lower().endswith(' county'):county+=' County'
    name=a.get('facility_name') or a.get('fp_place_name');tag=str(a.get('permit_id') or oid)
    # One permit ID can appear twice in different active/inactive layers. Keep distinct rows if status varies.
    fingerprint=(tag,num,a['permit_status'],dd,a.get('effective_date'))
    if fingerprint in npseen:audit['duplicates'].append(dict(source=k,object_id=oid,duplicate_of=npseen[fingerprint]));return
    key='epa-'+k+'-'+tag+'-'+str(oid);npseen[fingerprint]=key
    add(key,'Ohio EPA NPDES register',county or 'Ohio',num,name,meta['name'],a['permit_status'],utcday(dd if dd is not None else a.get('effective_date')),ro,url,meta['name']+'; '+num+'; object ID '+str(oid),l['url'],h0,{'authority':'Ohio Environmental Protection Agency, Division of Surface Water','county':county or None,'geography_basis':'reported facility county (municipal jurisdiction not inferred from mailing city)','reported_facility_city':a.get('facility_city'),'permit_id':a.get('permit_id'),'application_id':a.get('applicationid'),'permit_detail':a.get('permitdetail'),'effective_date':utcday(a.get('effective_date')),'expiration_date':utcday(a.get('expiration_date')),'screen':'facility name explicitly identifies data-center or related activity; may be accessory work'})
