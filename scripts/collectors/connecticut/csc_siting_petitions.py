"""Connecticut Siting Council Petition No. 1292 (Digital Realty Trumbull data center, Bloom Energy fuel cells):
filing, declaratory ruling and completion notices. Issuer: Connecticut Siting Council."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import json, re, html
from urllib.parse import urljoin
import fitz
from lib.text import plain
IDX='https://portal.ct.gov/CSC/3_Petitions/Petition-Nos-1291-1300/Petition-No-1292-Bloom-Trumbull'
def download(A):
 s=A.fetch('bloom-index.html.gz',IDX).decode()
 for h,x in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',s,re.S):
  w=plain(x)
  if not any(t in w for t in ['Decision and','Notice of Completion','Petition Filing']):continue
  n='bloom.pdf' if 'Filing' in w else ('decision.pdf' if 'Decision' in w else 'completion.pdf');A.fetch(n,urljoin(IDX,html.unescape(h)))
def rows(A,add):
 dec=json.loads((collector_data('connecticut','decision.json')).read_text());assert A.files['decision.pdf']['sha256']==dec['sha256']
 project='Digital Realty Trumbull data center — Bloom Energy 2 MW fuel cells';ds='Connecticut Siting Council data center docket';n='completion.pdf';doc=fitz.open(A.c/n);s=' '.join(' '.join(p.get_text().split()) for p in doc);assert all(z in s for z in ('1292 Digital Realty','6/14/2018','6/15/2018'))
 idx=plain(A.read('bloom-index.html.gz').decode());assert 'Petition Filing received 2/27/2017' in idx
 for n,kind,status,dt,role,loc in [('bloom.pdf','Petition for declaratory ruling','Received','2017-02-27','Council receipt date','Council docket filing and petition p. 1'),('decision.pdf','Declaratory ruling','Certificate not required with conditions','2017-04-27','Council vote date; letter dated April 28','Council decision p. 1, conditional ruling'),('completion.pdf','1 MW unit commissioning','Commissioned','2018-06-14','First unit commissioning date','Completion list: first 1292 row'),('completion.pdf','1 MW unit commissioning','Commissioned','2018-06-15','Second unit commissioning date','Completion list: second 1292 row'),('completion.pdf','Notice of completion','Notice of completion','2021-05-10','Completion notice transmission date','Email p. 1; dates of commissioning differ')]:
  add(ds,'1292',project,'Trumbull',kind,status,dt,role,A.files[n]['url'],loc,issuer='Connecticut Siting Council',archive='cache/history/ct/'+n,archive_sha256=A.files[n]['sha256'],source_index=IDX)
