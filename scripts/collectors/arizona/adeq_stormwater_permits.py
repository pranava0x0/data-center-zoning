"""Arizona Department of Environmental Quality water authorizations (myDEQ and legacy construction stormwater,
industrial stormwater and de minimis discharge registers), screened for data centers. Issuer: Arizona Department of
Environmental Quality (ADEQ)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
def download(query,queries):
    for k in WATER:gis_layer(k,query,queries)
def branch(b,k,n,x,a,oid,evidence):
    add=b.add;rows=b.rows;reject=b.reject;stats=b.stats
    no=a['AZNPDES_NUMBER'] or a.get('WQDB_NOI_NUMBER')
    if not no:reject.append([k,str(oid),'No state authorization/NOI number']);return
    kind={'storm':'Construction stormwater general permit','industrial':'Industrial multi-sector stormwater general permit','demin':'De minimis discharge general permit'}[k.split('_')[0]]
    if str(a.get('WAIVER') or '').strip().upper() in ('Y','YES','TRUE','1') or no.startswith('AZWV'):kind='Construction stormwater waiver register'
    loc=(a['CITY'] or 'Arizona').title();url=x['url']+'/query?'+urlencode({'where':"AZNPDES_NUMBER = '"+no+"'","outFields":x['fields'],'returnGeometry':'false','f':'pjson'})
    detail=dict(evidence,issuer='Arizona Department of Environmental Quality',source_layer=k,activity_code=a.get('ACTIVITY'),application_status_code=a.get('APPLICATION_STATUS'),waiver_field=a.get('WAIVER'),ltf_number=a.get('LTF_NUMBER'),wqdb_noi=a.get('WQDB_NOI_NUMBER'),received_date=date(a['RECEIVED_DATE']),end_date=date(a['TERM_CANCEL_DATE']))
    events=[('APPROVAL_DATE','Approval recorded','Approval date'),('TERM_CANCEL_DATE','Termination/cancellation recorded','Termination/cancellation date')]
    if not any(a[f] for f,_,_ in events):events=[('RECEIVED_DATE','Received' if a['RECEIVED_DATE'] else 'Not stated','Received date' if a['RECEIVED_DATE'] else 'Date not stated')]
    for f,status,role in events:
        if not a[f] and len(events)>1:continue
        event_key=no+'-'+f+'-'+str(date(a[f]))
        existing=rows.get('az-'+k+'-'+quote(event_key,safe=''))
        if existing:
            existing['details'].setdefault('linked_facility_rows',[]).append({'objectid':oid,'facility':a['FACILITY_NAME'],'city':loc});stats['ADEQ same number/action/date']+=1
            continue
        add(k,n,no,a['FACILITY_NAME'],kind,status,date(a[f]),role,loc,url,'AZNPDES_NUMBER='+no+'; '+f,dict(detail,source_objectid=oid),key=event_key,source=x['url'])
def rows(b):
    for k in WATER:scan(b,k,branch)
