"""Alaska shared evidence archive (cache/history/ak, sealed in data/history/alaska/manifest.json) and the record builder
every Alaska source module uses, so record ids stay sequential across sources."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import fitz
from lib.archive import NamedArchive as Archive
A=Archive('AK')
def adder(out):
 def add(n,ds,no,title,j,kind,status,dt,role,loc,**d):
  u=A.files[n]['url'];out.append(dict(id='ak-'+str(len(out)),state='AK',dataset=ds,record_no=no,project=title,jurisdiction=j,kind=kind,status=status,date=dt,date_role=role,url=u,source_url=u,locator=loc,details={'archive':'cache/history/ak/'+n,'archive_sha256':A.files[n]['sha256'],**d}))
 return add
def pdf(n):return ' '.join(' '.join(p.get_text().split()) for p in fitz.open(A.c/n))
