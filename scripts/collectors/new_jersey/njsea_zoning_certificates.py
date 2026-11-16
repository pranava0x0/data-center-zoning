"""New Jersey Sports and Exposition Authority (NJSEA, Meadowlands district) board books: zoning certificate case
reviews for data center projects (CoreSite NY3 and NY4, Evoque/Dawn US Holdings)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from urllib.parse import quote
import fitz
BOARD={'sec-22-jul.pdf':'https://njmc.s3.us-east-2.amazonaws.com/Final_Board_Book2_7_28_22.pdf','sec-22-dec.pdf':'https://njmc.s3.us-east-2.amazonaws.com/pdfs/meeting/2022/dec-agenda.pdf','sec-24-sep.pdf':'https://njmc.s3.us-east-2.amazonaws.com/pdfs/meeting/2024/sept-agenda.pdf'}
def download(A):
 for n,u in BOARD.items():A.fetch(n,u)
def rows(A):
 seen={}
 def add(ds,no,pr,kind,status,when,role,city,n,pg,d=None):
  url=A.files[n]['url'];uid='nj-'+quote('|'.join((ds,no,status,when)),safe='');r=dict(id=uid,state='NJ',dataset=ds,record_no=no,project=pr,kind=kind,status=status,date=when,date_role=role,jurisdiction=city,url=url+(f'#page={pg}' if pg else ''),source_url=url,source_sha256=A.files[n]['sha256'],locator=f'Page {pg} — {no}' if pg else no,details={'archive':'cache/history/nj/'+n,**(d or {})})
  if uid in seen:seen[uid]['details'].setdefault('repeated_in',[]).append({'archive':n,'page':pg});return
  seen[uid]=r
 for n,pg,no,proj,day in [('sec-22-jul.pdf',18,'22-235','CoreSite NY3, 2 Emerson Lane','2022-07-14'),('sec-22-dec.pdf',21,'22-439','Dawn US Holdings / Evoque, 15 Enterprise Avenue North','2022-12-05'),('sec-24-sep.pdf',18,'24-291','CoreSite NY4, 215 County Avenue','2024-09-11')]:
  with fitz.open(A.c/n) as doc:txt=' '.join(doc[pg-1].get_text().split())
  assert no in txt and 'received a zoning certificate application' in txt
  add('NJSEA zoning certificate case reviews',no,proj,'Zoning certificate application / suitability review','Suitability review',day,'Dated suitability review (not date received)','Secaucus',n,pg,{'county':'Hudson County','issuer':'New Jersey Sports and Exposition Authority'})
 return seen
