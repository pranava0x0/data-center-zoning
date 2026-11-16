"""Hawaii environmental review documents for the University of Hawaii at Manoa Information Technology Center
(HRS chapter 343). Issuer: State of Hawaii DBEDT Environmental Review Program (The Environmental Notice and EA/EIS
library)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import fitz
BASE='https://files.hawaii.gov/dbedt/erp/';S={'uhnotice.pdf':BASE+'The_Environmental_Notice/2011-02-08-TEN.pdf','uhdraft.pdf':BASE+'EA_EIS_Library/2009-04-08-OA-DEA-UH-Manoa-Information-Technology.pdf','uhfinal.pdf':BASE+'EA_EIS_Library/2011-02-08-OA-FEA-UH-Information-Tech-Center.pdf'}
def download(A):
 for n,u in S.items():A.fetch(n,u)
def rows(A):
 o=[]
 with fitz.open(A.c/'uhnotice.pdf') as doc:t=' '.join(doc[2].get_text().split()).split('3. Information Technology Center',1)[1];assert 'Permits: Building, Grading' in t[:300] and 'Finding of No Significant Impact' in t[:1000]
 for n,k,stat,dt,role,loc in [('uhdraft.pdf','Environmental assessment','Draft environmental assessment',None,'Draft dated February 2009; exact issuance date not verified','Draft assessment title and p. 20, full floor dedicated to data center'),('uhnotice.pdf','Environmental review determination','Finding of No Significant Impact','2011-02-08','State Environmental Notice publication date','Environmental Notice p. 3, Oahu item 3; lists building and grading permits, not evidence of their issuance')]:
  o.append(dict(id='hi-uh-'+n.split('.')[0],state='HI',dataset='Hawaii environmental review notices',jurisdiction='Honolulu',record_no='UH Manoa ITC / HRS 343',project='University of Hawaii at Manoa — Information Technology Center',kind=k,status=stat,date=dt,date_role=role,url=S[n],source_url=S['uhfinal.pdf'],locator=loc,details={'issuer':'University of Hawaii, Office of Capital Improvements','county':'Honolulu County','archive':'cache/history/hi/'+n,'archive_sha256':A.files[n]['sha256']}))
 return o
