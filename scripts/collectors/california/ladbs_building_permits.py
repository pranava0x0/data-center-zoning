"""City of Los Angeles issued building and trade permits (data.lacity.org Socrata resources). Issuer: Los Angeles Department of Building and Safety."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from urllib.parse import urlencode
from collectors.california.evidence_store import ASOF, cf, js, dt, so
def download_tasks():
 tasks=[]
 for res in cf['los_angeles']:
  cols='permit_nbr,primary_address,permit_group,permit_type,permit_sub_type,use_desc,issue_date,status_desc,status_date,work_desc';tasks.append(lambda r=res,c=cols:so(('la-'+r,'https://data.lacity.org/resource/'+r+'.json',c,['work_desc','use_desc'])))
 return tasks
def rows(ctx):
 add=ctx.add;selected=ctx.selected;cols=['work_desc','use_desc']
 for k in ['la-'+r for r in cf['los_angeles']]:
  ct=int(js(k+'-count.json')[0]['n']);seen=[];pages=[];per=__import__('collections').Counter()
  # Record identity comes from the permit number (the issuer's id). Socrata's :id row id is renumbered on refresh, so it is never used in an id, link or locator.
  for i in range(0,ct,500):
   n=f'{k}-{i}.json.gz';pages.append(n)
   for a in js(n):
    if selected(a,cols,a.get('permit_nbr'),k+'-prescan'):per[a.get('permit_nbr')]+=1
  ctx.exc[:]=[e for e in ctx.exc if not e['source'].endswith('-prescan')]
  for n in pages:
   for a in js(n):
    seen.append(a['src_row_id']);no=a.get('permit_nbr')
    if not selected(a,cols,no,k):continue
    issue=dt(a.get('issue_date'));fi=dt(a.get('filed_date'));when=issue or fi;status=a.get('status_desc');last=dt(a.get('status_date'));detail={'issuer':'Los Angeles Department of Building and Safety','issue_date':issue,'filed_date':fi,'status_date':last,'portal_row_id_at_capture':a['src_row_id'],'scope':a.get(cols[0]),'address':a.get('primary_address')}
    if last and last>ASOF:detail['post_cutoff_status']=status;status='Issued' if issue and issue<=ASOF else 'Filed'
    typ=a.get('permit_type') or 'Building permit';proj=a.get(cols[0]) or a.get(cols[1]) or 'Data center';base='https://data.lacity.org/resource/'+k[3:]+'.json';url=base+'?'+urlencode({'permit_nbr':no})
    # A permit number with several rows gets the status and dates of the row added; otherwise the permit number alone is the key.
    stable=no if per[no]==1 else '-'.join([no,status or 'none',issue or 'none',last or 'none']);loc='permit '+no+('' if per[no]==1 else '; status '+str(status)+'; issued '+str(issue)+'; status date '+str(last))
    # Different permits may cover one hall. Multiple address records may refer to the same permit; retain native record identity for status reconciliation.
    add('Los Angeles issued building and trade permits',k,n,no,proj,typ,status or 'Not reported',when,'Permit issue date' if issue else 'Filing date','Los Angeles',url,loc,detail,key=stable)
  assert len(seen)==len(set(seen))==ct
