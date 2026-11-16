"""Oregon Department of Environmental Quality (DEQ) air quality permits online (pre-November 2024 system): county register
pages and the permit PDFs they link, including the local land-use compatibility findings printed in each permit."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, R, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import argparse, csv, html, io, json, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode,quote
import fitz
from lib.archive import NamedArchive as Archive
A=Archive('OR');Q='https://deqonline.deq.state.or.us/aq/aqpermitsonline/SearchResult.asp';SS='https://www.oregon.gov/deq/aq/aqpermits/pages/default.aspx'
CODES={'25':'Morrow','34':'Washington','30':'Umatilla','7':'Crook','33':'Wasco','26':'Multnomah','9':'Deschutes'}
def plain(v):return ' '.join(html.unescape(re.sub('<[^>]*>',' ',v)).split())
def rows(s):
 for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>',s,re.S|re.I):
  dd=re.findall(r'<td\b[^>]*>(.*?)</td>',tr,re.S|re.I)
  if len(dd)!=15 or not re.fullmatch(r'\d{2}-\d{4}',plain(dd[0])):continue
  url=re.search('href="([^"]+)',dd[-1],re.I)
  if url:yield [plain(d) for d in dd[:-1]]+[html.unescape(url[1])]
def sectors(f):
 return re.search(r'data\s*cent|data\s*services|h5\s*data|cloudhq|stack infrastructure|vantage|facebook|prineville data|meta platforms|digital realty|qts|flexential|equinix|t5|taconic|winthrop|edgeconnex|server farm|google|beaver ventures|showers development|alcor|colocation|quality technology|ntt|enterprise information|amazon|design,? llc|vitesse|bricklayers|shute road|smdf|bcedge|greenberry',f,re.I)
def refresh():
 A.geom();counts={};candidates={}
 def query(code):
  allrows=[]
  for pg in range(1,100):
   url=Q+'?'+urlencode(dict(county=code,documenttype='1',pagenumber=pg));n=f'c{code}-{pg}.html.gz';s=A.fetch(n,url).decode(errors='replace');page=re.search(r'Page\s*(\d+)\s+of\s+(\d+)',s,re.I);assert page and int(page[1])==pg,(code,pg)
   page_rows=list(rows(s));assert page_rows and (pg==int(page[2]) or len(page_rows)==25),(code,pg,len(page_rows))
   for a in page_rows:
    if sectors(' '.join(a[:3])):candidates[a[-1]]=a
   allrows+=page_rows
   if pg==int(page[2]):break
  counts[code]=len(allrows)
 with ThreadPoolExecutor(3) as ex:list(ex.map(query,CODES))
 def pdf(task):
  url,fields=task;n='permit-'+lib.files.sha(url.encode())[:18]+'.pdf';b=A.fetch(n,url);assert b.startswith(b'%PDF');return n
 with ThreadPoolExecutor(3) as ex:list(ex.map(pdf,sorted(candidates.items())))
 A.seal({'document_type':'1 (Permit)','candidate_documents':len(candidates),'county_source_rows':counts})
def form(n,derived):
 with fitz.open(A.c/n) as doc:pgs=[' '.join(p.get_text().split()) for p in list(doc)[:3]]
 if n in derived:
  assert derived[n]['source_sha256']==A.files[n]['sha256'];pgs=[' '.join(i) for i in derived[n]['page_lines']]
 idx=max(range(len(pgs)),key=lambda i:('LAND USE COMPATIBILITY FINDING:' in pgs[i].upper(),'EXPIRATION DATE' in pgs[i].upper(),-i));return pgs,idx
def datestring(s):
 import datetime
 v=s.replace('.','').strip()
 for fmt in ['%m/%d/%Y','%m/%d/%y','%b %d, %Y','%B %d, %Y','%b %d %Y','%B %d %Y']:
  try:return datetime.datetime.strptime(v,fmt).date().isoformat()
  except ValueError:pass
 return None
def refresh_ocr():
 """Persist portable transcripts for image-only pages; replay needs no macOS OCR."""
 import subprocess, tempfile
 derived={}
 with tempfile.TemporaryDirectory(dir=A.c) as t:
  binary=Path(t)/'ocr';subprocess.run(['swiftc',str(R/'scripts/lib/ocr_vision.swift'),'-o',str(binary)],check=True)
  for n in sorted(A.files):
   if not n.startswith('permit-'):continue
   with fitz.open(A.c/n) as doc:probe=' '.join(doc[i].get_text() for i in range(min(2,len(doc))))
   if len(probe.strip())>100:continue
   lines=json.loads(subprocess.check_output([str(binary),str(A.c/n),'2']));derived[n]=dict(source_sha256=A.files[n]['sha256'],method='Apple Vision accurate recognition, pages 1–2; no inference from illegible dates',page_lines=lines)
 lib.files.dump(collector_data('oregon','ocr.json'),derived)
def events():
 A.verify();derived=json.loads((collector_data('oregon','ocr.json')).read_text());events={};held=[];reg=[];proven={}
 numdate=r'\d{1,2}/\d{1,2}/(?:\d{4}|\d{2})';monthdate=r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+20\d{2}'
 for n in sorted(A.files):
  if not (n.startswith('c') and n.endswith('.html.gz')):continue
  for a in rows(A.read(n).decode(errors='replace')):
   if not sectors(' '.join(a[:3])):continue
   f='permit-'+lib.files.sha(a[-1].encode())[:18]+'.pdf';pgs,i=form(f,derived);s=pgs[i]
   if re.search(r'\b518210\b|\bdata[ -]+cent(?:er|re)\b|\bdata processing\b',' '.join(pgs),re.I) and re.match(r'.*_P_\d{4}\.pdf$',a[-1],re.I):proven[a[0]]=a[-1]
   reg.append((a,n,f,i,s))
 for a,n,f,pg,s in reg:
  facility,name,site,addr,city,zip_,county,region,no,typ,document,year,other,curr,url=a
  if facility not in proven or not re.match(r'.*_P_\d{4}\.pdf$',url,re.I):held.append({'source_id':facility,'name':name,'url':url,'reason':'Generic master permit or no permit-document data-center sector confirmation for this source.'});continue
  where=county.title()+' County';base='or-deq-'+no;project=' — '.join(dict.fromkeys(v for v in [name,site] if v));pm=re.search(r'Expiration Date:\s*('+numdate+'|'+monthdate+')',s,re.I);expiration=datestring(pm[1]) if pm else None
  issu=re.search(r'ISSUED BY THE DEPARTMENT OF ENVIRONMENT\s*AL QUALITY(.+)',s,re.I);signed=issu[1] if issu else '';md=re.search(monthdate,signed,re.I);issue=datestring(md[0]) if md else None
  if issue and issue[:4]!=year:issue=None
  details=dict(county=where,issuer='Oregon Department of Environmental Quality',source_name=name,source_id=facility,source_locality=city.title(),address=addr,permit_year=year,archived_status_flag=curr or 'No historic flag shown',expiration_date=expiration,registry_archive='cache/history/or/'+n,archive='cache/history/or/'+f,identity_source=proven[facility],text_method='OCR' if f in derived else 'PDF text')
  source_url=A.files[n]['url'];identity=base+'-'+year;assert identity not in events
  events[identity]=dict(id=identity,state='OR',dataset='Oregon DEQ air permit documents',record_no=no,project=project,kind=typ,status='NOT CURRENT' if curr=='NOT CURRENT' else 'Issued permit',date=issue,date_role='Permit signature date' if issue else 'Exact signing date not verified; register supplies year',jurisdiction=where,url=url,source_url=source_url,source_sha256=A.files[f]['sha256'],locator=f'Air permit {no}, registry year {year}; permit cover p. {pg+1}',details=details)
  # Extract the separate local finding cited by the state; no local permit number is implied.
  l=re.search(r'Approving Authority:\s*(.{2,55}?)\s+Approval Date:\s*('+numdate+')',s,re.I)
  if not l:continue
  auth=' '.join(l[1].replace('ofHillsboro','of Hillsboro').replace('Hem1iston','Hermiston').split());date=datestring(l[2]);jur=re.sub(r'^(?:The )?City of ','',auth,flags=re.I)
  if not date or not re.fullmatch(r'[A-Za-z ]+',jur) or jur.lower() not in {'hillsboro','umatilla','hermiston','prineville','the dalles','morrow county','crook county','umatilla county','city of boardman','boardman','washington county','wasco county'}:continue
  k=f'or-lucs-{facility}-{date}-{quote(jur)}'
  if k in events:continue
  events[k]=dict(id=k,state='OR',dataset='Local land-use compatibility finding in DEQ permit',record_no=facility+' / LUCS '+date,project=project,kind='Land-use compatibility finding',status='Approved',date=date,date_role='Local land-use approval date',jurisdiction=jur,url=url+'#page='+str(pg+1),source_url=source_url,source_sha256=A.files[f]['sha256'],locator=f'Permit cover p. {pg+1}, Land Use Compatibility Finding; state source {facility}',details={**details,'issuer':auth,'local_permit_number':None,'identification':'State source number and finding date; not a local permit number.'})
 return events,held,reg
