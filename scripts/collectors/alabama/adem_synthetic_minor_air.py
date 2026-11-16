"""Alabama Department of Environmental Management (ADEM) synthetic minor air permit files: Dotier LLC (Montgomery
County, facility 209-0108) engineering analyses and the DigiPower X (Shelby County, facility 411-0078) public notice."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import fitz
from lib.text import plain
S={'dot.pdf':'https://adem.alabama.gov/sites/default/files/2026-09/09-26dotier-analysis.pdf','dot25.pdf':'https://adem.alabama.gov/sites/default/files/2025-09/09-25dotier-analysis.pdf','dig.html.gz':'https://adem.alabama.gov/sites/default/files/2026-11/10-26digipower.html'}
def download(A):
 for n,u in S.items():A.fetch(n,u)
def rows(A):
 out={}
 def add(n,k,ds,no,title,j,kind,stat,date,role,loc,url=None,**d):
  src=A.files[n]['url'];key='al-'+k
  out[key]=dict(id=key,state='AL',dataset=ds,record_no=str(no),project=title,jurisdiction=j,kind=kind,status=stat,date=date,date_role=role,url=url or src,source_url=src,locator=loc,details={**d,'archive':'cache/history/al/'+n,'archive_sha256':A.files[n]['sha256']})
 docs={n:' '.join(' '.join(p.get_text().split()) for p in fitz.open(A.c/n)) for n in ['dot.pdf','dot25.pdf']};assert 'Synthetic Minor Operating Permit Nos. X001 - X003' in docs['dot.pdf'];assert all('X00'+str(x) in docs['dot.pdf'] for x in range(4,8));ds='Alabama ADEM synthetic minor air files';j='Montgomery County';project='Dotier LLC — Montgomery data center';info=dict(county=j,issuer='Alabama Department of Environmental Management',facility_no='209-0108')
 for i in range(1,7):
  no=f'209-0108-X00{i}';add('dot.pdf',no,ds,no,project,j,'Synthetic minor operating permit','Existing equipment under SMOP',None,'Existing permit cited; issue date not reported','Engineering analysis p. 1, Project Description and Existing Equipment, group '+str(i),**info)
 for n,dt,nums in [('dot25.pdf','2025-07-14',[5,6]),('dot.pdf','2026-06-04',[7])]:
  for i in nums:
   assert ('July 14, 2025' if i<7 else 'June 4, 2026') in docs[n];no=f'209-0108-X00{i}';add(n,no+'-app',ds,no,project,j,'Synthetic minor operating permit application','Complete applications received',dt,'Application receipt date','Engineering analysis p. 1, complete applications and proposed units',**info)
 n='dig.html.gz';s=plain(A.read(n).decode());assert '411-0078' in s and '29th day of October, 2026' in s;add(n,'411-0078-notice',ds,'411-0078','DigiPower X — Columbiana data center','Shelby County','Synthetic minor operating permit public notice','Request for comments','2026-10-29','Public notice date','Facility 411-0078; notice of application (not issued)',county='Shelby County',issuer=info['issuer'])
 return out
