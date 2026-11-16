"""South Carolina DES air construction permits and statements of basis (Gannett Enterprises, Valara Holdings):
replay pinned PDF originals, not last-edited dates. Issuer: South Carolina Department of Environmental Services,
Bureau of Air Quality."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import re
import fitz
from lib.text import plain
base='https://des.sc.gov/sites/des/files/'
S={'val1.pdf':base+'2026-06/CP-50000316%20v1.0%20-%20AIR-Construction%20Permit.pdf','val2.pdf':base+'Documents/BAQ/Valara/ConstructionPermit.pdf','gan.pdf':base+'Documents/BAQ/DepartmentDecisions/GannettEnterprises/DepartmentDecision.pdf','ganbase.pdf':base+'Documents/BAQ/DepartmentDecisions/GannettEnterprises/StatementofBasis.pdf','valpage.html.gz':'https://des.sc.gov/community/community-engagement/environmental-sites-projects/valara-holdings-high-performance-compute-center'}
def download(A):
 for n,url in S.items():A.fetch(n,url)
def rows(A,add):
 """Adds events through add(); datefmt is the date regex the permit text uses."""
 datefmt=r'[A-Z][a-z]+ \d{1,2}, 20\d\d'
 for n in ['gan.pdf','val1.pdf','val2.pdf']:
  with fitz.open(A.c/n) as doc:s=' '.join(doc[0].get_text().split())
  no=re.search(r'Permit Number: (CP-\d+) v1.0',s)[1];what='Gannett Enterprises' if n=='gan.pdf' else 'Valara Holdings High Performance Compute Center';county='Dorchester County' if n=='gan.pdf' else 'Spartanburg County';dt=re.search('Issue Date: ('+datefmt+')',s)[1];add(n,no,what,county,'Synthetic minor air construction permit','Issued',dt,'Permit issue date','p. 1, permit number v1.0, issue date')
  if n=='gan.pdf':
   with fitz.open(A.c/'ganbase.pdf') as doc:t=' '.join(doc[0].get_text().split())
   for label,kind,stat in [('DATE APPLICATION RECEIVED','Air permit application','Received'),('DATE ACCEPTED INTO EXPEDITED REVIEW','Expedited application review','Accepted'),('DATE OF CZC APPROVAL','CZC finding in air permit basis','Approved')]:
    m=re.search(label+': ('+datefmt+')',t);assert m;add('ganbase.pdf',no,what,county,kind,stat,m[1],label.title(),'Statement of basis p. 1, '+label+'; air number used as project reference')
   m=re.search('public comment from ('+datefmt+'),? through ('+datefmt+')',s);assert m
   for dt,stat in zip(m.groups(),['Opened','Closed']):add(n,no,what,county,'Air permit public comment',stat,dt,'Public comment window '+stat.lower(),'Decision p. 1, public notice paragraph')
  else:
   dt=re.search(r'application received on ('+datefmt+')',s)[1];add(n,no,what,county,'Air permit application','Received',dt,'Application received date','Permit p. 1, application receipt')
   if n=='val2.pdf':
    t=plain(A.read('valpage.html.gz').decode());assert 'June 25, 2026' in t and 'May 26, 2026 through July 31, 2026' in t
    for dt,kind,status in [('May 26, 2026','Air permit public comment','Opened'),('June 25, 2026','Public meeting and hearing','Held'),('July 31, 2026','Air permit public comment','Closed')]:add('valpage.html.gz',no,what,county,kind,status,dt,'Public participation milestone','Response to request for additional public comment, second air permit')
