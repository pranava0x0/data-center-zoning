"""New York State Department of Environmental Conservation issued state facility air permits (data.ny.gov; Title V and
air state facility registers)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from concurrent.futures import ThreadPoolExecutor
from collectors.new_york.source_store import D,STATE,ASF,TV,fetch_series,read,dataurl,eq,matched,iso,mk
def download():
    D.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(fetch_series,[ASF,TV]))
def rows():
    out=[]
    matches={'3-3924-00119/00005':'https://extapps.dec.ny.gov/data/dar/afs/permits/339240011900005_r0.pdf','3-3924-00493/00001':'https://extapps.dec.ny.gov/data/dar/afs/permits/339240049300001_r0_2.pdf'}
    for ds in (ASF,TV):
        for r in read(ds)['rows']:
            n=r['permit_id']
            if n not in matches:
                if matched(r.get('facility_name')):raise ValueError('New NY air permit requires county/program review: '+n)
                continue
            u=dataurl(STATE,ds,eq('permit_id',n));v=mk('New York DEC issued state facility air permits','air-'+re.sub(r'[^0-9]','',n),'State facility air permit','Issued',n,iso(r['issue_date']),'issue date',u,'permit_id '+n,r['facility_name'],r['facility_city'].title(),'Rockland County',D/(ds+'.json.gz'),issuer='New York State Department of Environmental Conservation',source_series=ds,permit_document=matches[n],address=r['facility_location'],expiration_date=iso(r.get('expire_date') or r.get('expiration_date')),identity_basis='DEC issued permit identifies data center explicitly.')
            if v:out.append(v)
    return out
