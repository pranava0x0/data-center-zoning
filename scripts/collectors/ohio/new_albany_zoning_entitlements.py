"""City of New Albany zoning-entitlement GIS (PublicZoning/ZoningEntitle): board cases with adoption dates."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.ohio.common import fetch_layer, cal
def download(c,m,k,l):fetch_layer(c,m,k,l)
def domain(meta,key,value):
    for f in meta['fields']:
        if f['name']==key:
            for e in (f.get('domain') or {}).get('codedValues',[]):
                if e['code']==value:return e['name']
    return value
def row(add,audit,state,k,l,meta,a,h0,hh,oid,url):
    n=a['CaseNumber'];status=domain(meta,'Status',a['Status']);typ=domain(meta,'Type',a['Type'])
    bd=[{field:cal(a[field]),'source_status':a.get(field.replace('HearingDate','Status'))} for field in a if field.endswith('HearingDate') and a[field]]
    details={'authority':'City of New Albany','raw_type':a['Type'],'raw_status':a['Status'],'description':a.get('Description'),'case_year':a['Year'],'recorded_field':'AdoptionDate','board_dates':bd,'matched_fields':list(hh),'source_object_id':oid}
    if n=='FDM-16-2026':details['date_note']='GIS date as recorded; not independently established as the board vote date.'
    add('na-'+n,'New Albany zoning entitlements','New Albany',n,a['Name'],typ,status,cal(a['AdoptionDate']),'recorded disposition date (GIS AdoptionDate)',url,'CaseNumber '+n+'; OBJECTID '+str(oid),l['url'],h0,details)
