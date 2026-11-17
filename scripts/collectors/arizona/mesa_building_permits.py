"""City of Mesa building permit register (data.mesaaz.gov Building Permits, Socrata), screened for data centers.
Issuer: City of Mesa Development Services."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
def download(save,query,queries):
    k='mesa';x=conf[k];w=lib.terms.patterns(x['search'],'lower');count=int(js(lib.net.req(x['url'],{'$select':'count(*) as n','$where':w}))[0]['n']);ids=[]
    for start in range(0,count,500):
        rr=query(f'mesa-{start}.json.gz',x['url'],{'$where':w,'$select':x['fields'],'$limit':500,'$offset':start,'$order':':id'});ids.extend(a['src_id'] for a in rr)
    assert len(ids)==len(set(ids))==count;queries[k]=count;print(k,count,flush=True)
def branch(b,k,n,x,a,oid,evidence):
    add=b.add;rows=b.rows;stats=b.stats;mesa_seen=b.mesa_seen
    no=a['permit_number'];detail_identity={k:v for k,v in a.items() if k!='src_id'}
    if no in mesa_seen:
        assert mesa_seen[no]==detail_identity,'Conflicting Mesa permit rows '+no
        rows['az-mesa-'+quote(no,safe='')]['details'].setdefault('duplicate_source_rows',[]).append(oid);stats['Mesa identical duplicate']+=1;return
    mesa_seen[no]=detail_identity;title=a.get('application_name') or a.get('property_address') or no
    dt=date(a.get('issued_date')) or date(a.get('opened_date'));role='Issue date' if a.get('issued_date') else ('Opened date' if dt else 'Date not stated')
    kind=' / '.join(v for v in [a.get('record_type'),a.get('type_of_work')] if v) or a.get('permit_type') or 'Building permit record'
    if not a.get('status'):raise ValueError(('Missing Mesa status',no))
    add(k,n,no,title,kind,a['status'],dt,role,'Mesa',x['url']+'?'+urlencode({'permit_number':no}),f'permit_number={no}',dict(evidence,work_description=a.get('description_of_work'),permit_type=a.get('permit_type'),opened_date=date(a.get('opened_date')),status_date=date(a.get('status_date')),finaled_date=date(a.get('finaled_date')),cofo_date=date(a.get('cofo_date')),portal_row_id_at_capture=oid),source='https://data.mesaaz.gov/Development-Services/Building-Permits/dzpk-hxfb')
def rows(b):scan(b,'mesa',branch)
