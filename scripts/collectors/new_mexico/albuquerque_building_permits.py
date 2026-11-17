"""City of Albuquerque issued building permits (CABQ City_Building_Permits feature layer), filtered to data-center work descriptions."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt, re
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
import collectors.new_mexico.sources as n
def rows(a,emit,held):
    """Emits records through emit and appends excluded candidates to held; returns the query URL and matched object IDs."""
    def norm(t):return ' '.join(t.casefold().split())
    terms=('DATA CENTER','DATA CENTRE','DATACENTER','SERVER FARM','COLOCATION','CO-LOCATION')
    where=' OR '.join("UPPER(WorkDescription) LIKE '%"+x+"%'" for x in terms)
    def query(**k):return n.ABQ+'/query?'+urlencode({'f':'json',**k})
    md=a.json(n.ABQ+'?f=json')
    if 'issued by the city of albuquerque' not in norm(md['description']):raise ValueError('Register no longer defines issued permits')
    ids=a.json(query(where=where,returnIdsOnly='true'))['objectIds']
    u=query(where=where,outFields='OBJECTID,PermitNumber,WorkDescription,CalculatedAddress,TypeofWork,DateIssued',returnGeometry='false')
    j=a.json(u)
    if j.get('exceededTransferLimit') or set(ids)!={f['attributes']['OBJECTID'] for f in j['features']}:raise ValueError('Truncated Albuquerque query')
    for f in j['features']:
        v=f['attributes'];no=v['PermitNumber'];desc=v['WorkDescription']
        if not re.search(r'\b(?:data\s*cent(?:er|re)|server farm)\b',desc,re.I):
            held.append(dict(record_no=no,reason='Telecom co-location; no explicit data center.'));continue
        day=dt.datetime.fromtimestamp(v['DateIssued']/1000,ZoneInfo('America/Denver')).date().isoformat()
        title='NOVA data center' if 'NOVA' in desc else 'Daytona Road data center' if 'DAYTONA' in (v['CalculatedAddress'] or '') else 'Data center building work'
        emit('Albuquerque issued building permits',no,'Albuquerque','Bernalillo County',title,'Commercial building permit','Issued',day,'Issue date',n.ABQ+'/query?'+urlencode({'where':f"PermitNumber='{no}'",'outFields':'*','f':'html'}),a.get(u)[1],'PermitNumber '+no,work_description=desc,address=v['CalculatedAddress'],work_class=v['TypeofWork'],portal_row_id_at_capture=v['OBJECTID'],source_url=u)
    return u,ids
