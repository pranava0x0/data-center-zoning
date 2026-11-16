"""City and County of San Francisco building permits (data.sfgov.org dataset i98e-djp9). Issuer: San Francisco Department of Building Inspection."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from urllib.parse import urlencode
from collectors.california.evidence_store import ASOF, js, dt, so
def download_tasks():
 return [lambda:so(('sf','https://data.sfgov.org/resource/i98e-djp9.json','permit_number,permit_type_definition,description,status,status_date,filed_date,issued_date,completed_date,street_number,street_name,street_suffix,record_id,proposed_use,existing_use',['description','proposed_use','existing_use']))]
def rows(ctx):
 add=ctx.add;selected=ctx.selected;cols=['description','proposed_use','existing_use'];k='sf'
 ct=int(js(k+'-count.json')[0]['n']);seen=[]
 for i in range(0,ct,500):
  n=f'{k}-{i}.json.gz'
  for a in js(n):
   seen.append(a['src_row_id']);no=a.get('permit_number')
   if not selected(a,cols,no,k):continue
   issue=dt(a.get('issued_date'));fi=dt(a.get('filed_date'));when=issue or fi;status=a.get('status');last=dt(a.get('status_date'));detail={'issuer':'San Francisco Department of Building Inspection','issue_date':issue,'filed_date':fi,'status_date':last,'source_record_id':a.get('record_id') or a['src_row_id'],'scope':a.get(cols[0]),'address':' '.join(a.get(f,'') for f in ['street_number','street_name','street_suffix']).strip()}
   detail['county']='San Francisco County'
   if last and last>ASOF:detail['post_cutoff_status']=status;status='Issued' if issue and issue<=ASOF else 'Filed'
   typ=a.get('permit_type_definition') or 'Building permit';proj=a.get(cols[0]) or a.get(cols[1]) or 'Data center';base='https://data.sfgov.org/resource/i98e-djp9.json';url=base+'?'+urlencode({'$where':"permit_number="+repr(no)})
   add('San Francisco building permits',k,n,no,proj,typ,status or 'Not reported',when,'Permit issue date' if issue else 'Filing date','San Francisco',url,'Socrata record '+a['src_row_id']+'; permit '+no,detail,key=a['src_row_id'])
 assert len(seen)==len(set(seen))==ct
