"""City of Phoenix plan reviews and permits (Phoenix GIS permit layers), screened for data centers.
Issuer: City of Phoenix Planning and Development Department."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
LAYERS=('phoenix_plan','phoenix_permit')
def download(query,queries):
    for k in LAYERS:gis_layer(k,query,queries)
def branch(b,k,n,x,a,oid,evidence):
    add=b.add;rows=b.rows;stats=b.stats;phx_seen=b.phx_seen
    ident=(k,a['PID']);as_record={k:v for k,v in a.items() if k not in ('OBJECTID','STREET_FULL_NAME')}
    if ident in phx_seen:
        assert phx_seen[ident]==as_record,('Conflicting Phoenix rows',ident)
        rows['az-'+k+'-'+a['PID']]['details'].setdefault('other_addresses',[]).append({'address':a['STREET_FULL_NAME'],'objectid':oid});stats['Phoenix linked address']+=1;return
    phx_seen[ident]=as_record
    no=a['PER_TYPE']+' '+a['PER_NUM'];dt=date(a['PER_ISSUE_DATE'],True) or date(a['PER_ENT_DATE'],True);plan=k=='phoenix_plan'
    role=('Plan record issue date' if plan else 'Issue date') if a['PER_ISSUE_DATE'] else ('Entry date' if dt else 'Date not stated')
    href=x['url']+'/query?'+urlencode({'where':"PID = '"+a['PID']+"'","outFields":x['fields'],'returnGeometry':'false','f':'pjson'})
    add(k,n,no,a['PERMIT_NAME'] or a['STREET_FULL_NAME'],a['PER_TYPE_DESC'] or a['PER_TYPE'],a['PERMIT_STAT'],dt,role,'Phoenix',href,'PID '+a['PID']+', '+no,dict(evidence,project_number=a['PROJECT'],source_scope=a['SCOPE_DESC'],entry_date=date(a['PER_ENT_DATE'],True),completion_date=date(a['PER_COMPL_DATE'],True),address=a['STREET_FULL_NAME'],source_pid=a['PID'],permit_type_code=a['PER_TYPE'],issue_date=date(a['PER_ISSUE_DATE'],True),expiration_date=date(a.get('PER_EXPIRE_DATE'),True)),key=a['PID'])
def rows(b):
    for k in LAYERS:scan(b,k,branch)
