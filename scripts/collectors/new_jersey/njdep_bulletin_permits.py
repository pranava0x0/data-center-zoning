"""New Jersey Department of Environmental Protection (NJDEP) DEP Bulletin: issue PDFs from the New Jersey State Library
DSpace archive, screened for data center permit entries (NJPDES general permit authorizations, land resource permitting
milestones, treatment works applications, NJPDES proposed actions and revocations)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json, re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode,quote
import fitz
import lib.net, lib.text
BASE='https://dspace.njstatelib.org/server/api'
QUERY='dc.title:"DEP Bulletin" AND dc.date.issued:[2024-01-01 TO 2026-11-15] AND ("data center" OR "data centre" OR "datacenter" OR "Equinix" OR "CoreWeave" OR "CoreSite")'
LAND={'1201-08-0002.2 - FWW - 230001':('Equinix NY11','Carteret Borough','Middlesex County','Freshwater wetlands general permit modification'),'0909-20-0002.1 - LUP - 250001':('Equinix NY10-1','Secaucus','Hudson County','Flood hazard individual permit'),'1101-10-0002.5 - FWW - 250001':('QTS Princeton site','East Windsor Township','Mercer County','Freshwater wetlands line verification'),'1101-10-0002.5 - LUP - 250001':('QTS Princeton data center','East Windsor Township','Mercer County','Combined flood hazard permit, wetlands general permit and transition area waiver'),'0909-26-0003.1 - LUP - 260001':('CoreSite NY4 data center','Secaucus','Hudson County','Flood hazard individual permit and verification')}
def download(A):
 u=BASE+'/discover/search/objects?'+urlencode(dict(query=QUERY,size=100,sort='dc.date.issued,DESC'));o=json.loads(A.fetch('issue-index.json.gz',u))['_embedded']['searchResult'];assert o['page']['totalPages']==1
 def one(v):
  a=v['_embedded']['indexableObject'];dt=a['metadata']['dc.date.issued'][0]['value'];uid=a['uuid'];bs=json.loads(lib.net.req(BASE+'/core/items/'+uid+'/bundles'))['_embedded']['bundles'];orig=next(b for b in bs if b['name']=='ORIGINAL');fs=json.loads(lib.net.req(orig['_links']['bitstreams']['href']))['_embedded']['bitstreams'];pdf=[f for f in fs if f['name'].lower().endswith('.pdf')];assert pdf,dt
  for item in pdf:
   link=item['_links']['content']['href'];b=A.fetch('issue-'+dt+'-'+item['uuid'][:8]+'.pdf',link);assert b.startswith(b'%PDF')
  print('issue',dt,flush=True)
 with ThreadPoolExecutor(3) as ex:list(ex.map(one,o['_embedded']['objects']))
 return {'query':QUERY,'candidate_issues':o['page']['totalElements']}
def rows(A):
 seen={};pages_scanned=0
 def add(ds,no,pr,kind,status,when,role,city,n,pg,d=None):
  url=A.files[n]['url'];uid='nj-'+quote('|'.join((ds,no,status,when)),safe='');r=dict(id=uid,state='NJ',dataset=ds,record_no=no,project=pr,kind=kind,status=status,date=when,date_role=role,jurisdiction=city,url=url+(f'#page={pg}' if pg else ''),source_url=url,source_sha256=A.files[n]['sha256'],locator=f'Page {pg} — {no}' if pg else no,details={'archive':'cache/history/nj/'+n,**(d or {})})
  if uid in seen:seen[uid]['details'].setdefault('repeated_in',[]).append({'archive':n,'page':pg});return
  seen[uid]=r
 for n in sorted(A.files):
  if not n.startswith('issue-') or not n.endswith('.pdf'):continue
  date=n[6:16]
  with fitz.open(A.c/n) as doc:
   for num,pg in enumerate(doc,1):
    pages_scanned+=1;s=' '.join(pg.get_text().split());ly=pg.get_text(sort=True)
    if 'General Permit Authorizations Issued' in s:
     for line in ly.splitlines():
      if not re.search(r'data[ -]?cent[er]{2}|coreweave|equinix|coresite',line,re.I):continue
      ma=re.match(r'\s*(.*?)\s{2,}(\S.*?\S)\s{2,}(NJG\d+)\s+(\d+/\d+/\d+)\s+([\w]+)',line)
      if not ma:continue
      p,city,no,d,cat=ma.groups();add('NJDEP NJPDES bulletin',no,p.strip(),'NJPDES general permit authorization ('+cat+')','Issued',lib.text.isodate(d),'Issue date',city,n,num,{'issuer':'New Jersey Department of Environmental Protection','discharge_category':cat})
    for no,(p,city,co,kind) in LAND.items():
     if no not in s:continue
     seg=s.split(no,1)[1].split('Activity Number Project Location',1)[0]
     if 'Milestone Completed Date' not in seg:continue
     for stat,raw in re.findall(r'(Application Received|Application Administratively Complete|Amended Application Received|Technical Information Requested|Technical Deficiency Information Received|Issued|Approved)\s+(\d{2}/\d{2}/\d{4})',seg):
      add('NJDEP land resource permitting',no,p,kind,stat,lib.text.isodate(raw),'Agency milestone completion date',city,n,num,{'county':co,'issuer':'New Jersey Department of Environmental Protection'})
    if 'EQUINIX NY11' in s and 'NJG0338079' in s and 'revoked effective 6/11/25' in s:add('NJDEP NJPDES bulletin','NJG0338079','Equinix NY11, 1400 Federal Boulevard','NJPDES administrative revocation','Revoked','2025-06-11','Revocation effective date','Carteret Borough',n,num,{'county':'Middlesex County','issuer':'New Jersey Department of Environmental Protection'})
    if all(q in s for q in ['26-0421','Equinix NY03','08/28/2026']):add('NJDEP treatment works applications','26-0421','Equinix NY03, 600 Jefferson Avenue','Treatment works approval application','Application Received','2026-08-28','Application received date','Secaucus',n,num,{'county':'Hudson County','issuer':'NJDEP Division of Water Quality'})
    if 'NJ0382728' in s and 'EQUINIX NY10-1' in s and 'Public Notice of Proposed Permit Actions' in s:add('NJDEP NJPDES proposed actions','NJ0382728','Equinix NY10-1, 275 Hartz Way','Individual stormwater construction permit','Proposed permit action',date,'Bulletin publication date','Secaucus',n,num,{'county':'Hudson County','issuer':'NJDEP Bureau of NJPDES Stormwater Permitting'})
 return seen,pages_scanned
