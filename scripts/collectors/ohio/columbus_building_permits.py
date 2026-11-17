"""City of Columbus building and trade permits (BuildingZoning/MapServer permit layer): parcel-linked candidates from the
site-engineering screen, each confirmed against the permit's own Accela project description."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json, re
from collectors.ohio.common import fetch_layer, records, hits, pull, sha, cal, keyurl, MAN, RX
from collectors.ohio import columbus_accela_portal as accela
def download(c,m,k,l):fetch_layer(c,m,k,l)
def download_parcel_joins(c,m):
    eng=c['layers']['engineering'];bld=c['layers']['building']
    parcels=sorted({str(a['B1_PARCEL_NBR']) for a,_ in records(m['layers']['engineering']['screen']) if hits(a,eng) and a.get('B1_PARCEL_NBR')})
    for i in range(0,len(parcels),25):
        chunk=parcels[i:i+25]
        if not all(re.fullmatch(r'[0-9A-Za-z-]+',p) for p in chunk):raise ValueError('Unexpected parcel ID')
        m['joins'].append(pull(bld['url'],"B1_PARCEL_NBR IN ("+','.join("'"+p+"'" for p in chunk)+")",bld['fields']))
def row(add,audit,state,k,l,meta,a,h0,hh,oid,url):
    # No published direct matches in this snapshot; additions should be reviewed, not silently lost.
    audit['held'].append(dict(source=k,object_id=oid,reason='Direct registry-text match: review work vs applicant field'))
def portal_rows(c,m,add,audit,eng):
    pdoc=json.loads(accela.PORTAL.read_text())
    if pdoc['gis_manifest_sha256']!=sha(MAN.read_bytes()):raise ValueError('Municipal detail crawl does not correspond to the GIS capture')
    pcs=pdoc['documents'];linked=0;active=0
    for j in m['joins']:
        for a,hash0 in records(j):
            n=a['B1_ALT_ID'];ref=pcs.get(n)
            if not ref:raise ValueError('Unaccounted permit candidate')
            desc=accela.portal_read(ref,n);links=[e['B1_ALT_ID'] for e in eng if e['B1_PARCEL_NBR']==a['B1_PARCEL_NBR']]
            if desc is None or not RX.search(desc):
                audit['held'].append(dict(source='Columbus building parcel search',number=n,site_plan_numbers=links,reason='detail unavailable or wrong record' if desc is None else 'no explicit facility phrase in matching permit description',url=ref['url']));continue
            linked+=1;oid=a['OBJECTID'];city='Columbus';l=c['layers']['building'];match=RX.search(desc);start=max(0,match.start()-60);end=min(len(desc),match.end()+100)
            add('col-bld-'+n,'Columbus building and trade permits',city,n,n+' — '+(a['GENERAL_TYPE'] or a['B1_PER_SUB_TYPE'] or 'permit'),(a['B1_PER_SUB_TYPE'] or 'Building')+' / '+(a['GENERAL_TYPE'] or 'not specified'),a['B1_APPL_STATUS'] or a['PERMIT_STATUS'],cal(a['ISSUED_DT']),'issue date',ref['url'],'Accela Record '+n+' → Project Description',keyurl(l['url'],'B1_ALT_ID',n),ref['sha256'],{'portal_row_id_at_capture':oid,'authority':'City of Columbus Building and Zoning Services','evidence_excerpt':desc[start:end],'parcel':a['B1_PARCEL_NBR'],'screen':'parcel links found candidate; explicit phrase in this numbered permit’s own project description','site_plan_numbers':links,'registry_sha256':hash0,'registry_permit_status':a['PERMIT_STATUS'],'registry_application_status':a['B1_APPL_STATUS'],'source_subtype':a['B1_PER_SUB_TYPE'],'last_status_date':cal(a['LAST_STATUS_DT'])})
    audit['columbus_portal']={'candidate_numbers':len(pcs),'explicit_numbered_permits':linked,'cached_documents':sum('sha256' in r for r in pcs.values())}
