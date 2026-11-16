"""California Energy Commission: small power plant exemption (SPPE) dockets for backup-generation at data centers (efiling docket log,
backup-generating-system project profiles, and Commission orders). Issuer: California Energy Commission."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import html, io, re
from datetime import datetime
from pypdf import PdfReader
from lib.text import plain
from collectors.california.evidence_store import cf, data, dt, fetch, rx
CEC='https://efiling.energy.ca.gov/Lists/DocketLog.aspx';CP='https://www.energy.ca.gov/powerplant/backup-generating-system/'
def docket(it):
  code,meta=it
  if meta.get('slug'):fetch(f'profile-{code}.html.gz',CP+meta['slug'])
  b=fetch(f'docket-{code}.html.gz',CEC,{'docketnumber':code});tn=meta['transactions'].get('order')
  if tn:
   row=next(tr for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',b.decode(),re.S) if re.search(r'<td>'+re.escape(tn)+r'</td>',tr));url=html.unescape(re.search(r'<strong><a href="([^"]+)',row)[1]);fetch(f'order-{code}.pdf',url)
def download_tasks():return [lambda v=v:docket(v) for v in sorted(cf['cec'].items())]
def rows(ctx):
 add=ctx.add
 for code,meta in cf['cec'].items():
  n=f'docket-{code}.html.gz';s=data(n).decode();trs=re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S);docket={};url=f'{CEC}?docketnumber='+code;place=meta.get('place');profile=None;stat=None;title=meta.get('name')
  if 'slug' in meta:
   profile=CP+meta['slug'];p=data(f'profile-{code}.html.gz').decode();ss=plain(p);assert code in ss and rx.search(ss);h=re.search(r'<h1[^>]*>(.*?)</h1>',p,re.S);title=plain(h[1]);where=re.search(r'Docket Number .*? Location (.{1,100}?) Technology Backup Generating System',ss);place=(where[1].split(',')[0].replace('San José','San Jose') if where else meta.get('place') or ('Santa Clara' if code in ['22-SPPE-01','20-SPPE-02'] and 'Santa Clara' in ss else 'California'));stat=re.search(r'Project Status (.{1,25}?) Project Type',ss)[1]
  for tr in trs:
   dd=re.findall(r'<td[^>]*>(.*?)</td>',tr,re.S)
   if len(dd)<3:continue
   a=re.search(r'<strong><a href="([^"]+)"[^>]*>(.*?)</a>',dd[2],re.S)
   if a:docket[plain(dd[0])]=(dt(plain(dd[1])),html.unescape(a[1]),plain(a[2]))
  for action,tn in meta['transactions'].items():
   date,link,doc=docket[tn];order=action=='order';assert not order or (stat in (None,'Exempted') and re.search(r'order|commission.*decision',doc,re.I));assert order or re.search(r'app|cover letter',doc,re.I)
   when=date;role='CEC document docketing date';extra={'docket_date':date};origin=n
   if order:
    origin=f'order-{code}.pdf';ordertext=' '.join(' '.join(p.extract_text().split()) for p in PdfReader(io.BytesIO(data(origin))).pages)
    assert re.search(r'\bGRANTS\b.{0,125}Small Power Plant Exemption|(?:is|are) GRANTED.{0,100}(?:exempt|Small Power Plant Exemption)',ordertext,re.I),(code,'No explicit exemption grant')
    meeting=re.search(r'adopted at a meeting of the (?:CEC|California Energy Commission) held on ([A-Z][a-z]+ \d{1,2}, \d{4})',ordertext,re.I);assert meeting,code
    when=datetime.strptime(meeting[1],'%B %d, %Y').date().isoformat();role='Commission adoption date';assert when<=date
    if 'City of Santa Clara' in ordertext and place=='California':place='Santa Clara'
    if 'County of Santa Clara' in ordertext:extra['county']='Santa Clara County'
    if 'Contra Costa County' in ordertext:extra['county']='Contra Costa County'
    extra['docket_archive']='cache/history/ca/'+n
   add('CEC small power plant exemption docket','cec',origin,code,title,'Backup-generation exemption '+('decision' if order else 'application'),'Exemption granted' if order else 'Application docketed',when,role,place or 'California',link,f'Docket {code}, TN {tn}',dict(**extra,issuer='California Energy Commission',transaction_number=tn,filing_title=doc,profile=profile,project_status_on_profile=stat,scope='Generator licensing jurisdiction; not a permit for the data center building.'),key=code+'-'+tn)
