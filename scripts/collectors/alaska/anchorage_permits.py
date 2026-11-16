"""Municipality of Anchorage Building Safety (bsd.muni.org Inspection and Review site): permit case pages, discipline
reviews and inspections for the data-center parcels."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.terms
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from lib.text import plain
from collectors.alaska.evidence_store import A, adder
B='https://bsd.muni.org/Inspandreview/'
PAR=['00320119000','00420209000','01237160000','00124202000'];SEEDS=['355517','469523']
def links(s):
 for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S|re.I):
  cells=[plain(v) for v in re.findall(r'<td[^>]*>(.*?)</td>',tr,re.S|re.I)];m=re.search(r'href="([^"]*PermitInfo.aspx\?apbldgkey=(\d+))"',tr,re.I)
  if m and lib.terms.MATCH.search(' '.join(cells)) and len(cells)>=4:yield m[2],cells
def download():
 ids=set(SEEDS)
 for k in PAR:
  f='parcel-'+k+'.html.gz';s=A.fetch(f,B+'ParcelInfo.aspx?parcelno='+k).decode(errors='replace');ids.update(key for key,c in links(s))
 def get(k):A.fetch('permit-'+k+'.html.gz',B+'PermitInfo.aspx?apbldgkey='+k)
 with ThreadPoolExecutor(3) as e:list(e.map(get,sorted(ids)))
def rows(out,held):
 add=adder(out);aliases={}
 for pn in PAR:
  n='parcel-'+pn+'.html.gz'
  for key,cells in links(A.read(n).decode(errors='replace')):aliases[key]=(cells[3],n)
 ds='Anchorage permit records';statuses='Anchorage inspection and review actions'
 for n in sorted(A.files):
  m=re.match(r'permit-(\d+)\.html.gz$',n)
  if not m:continue
  k=m[1];s=A.read(n).decode(errors='replace');t=plain(s);m=re.search(r'Permit Number: (.*?) Permit Type: (.*?) Address: (.*?) Location: (.*?)Work Description: (.*?) Parcel: (.*?) Legal: .*?Status: (.*?) Subpermit',t);assert m,n
  no,kind,addr,_,desc,parcel,stat=m.groups();alias,pn=aliases.get(k,('',None));assert lib.terms.MATCH.search(desc+' '+alias)
  if 'PAS-to-HAN Conversion' in desc:held.append([no,'Administrative parent to hold converted reviews; no independent permit.']);continue
  title=alias or desc;d=dict(issuer='Municipality of Anchorage',county='Anchorage Municipality',permit_no=no,address=addr,parcel=parcel,work_description=desc)
  if pn:d.update(project_name_archive='cache/history/ak/'+pn,project_name_source=A.files[pn]['url'])
  add(n,ds,no,title,'Anchorage',kind,stat,None,'Permit issuance date not shown on case page','Permit Information: number, work description, Status',**d)
  for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S|re.I):
   c=[plain(v) for v in re.findall(r'<td[^>]*>(.*?)</td>',tr,re.S|re.I)]
   if len(c)==6 and re.fullmatch(r'\d+',c[1]) and re.fullmatch(r'\d+/\d+/\d{4}',c[3]):
    role='Discipline review completion date';dte=c[3];work=c[0]+' review';result=c[4];ref=no+' / '+c[0]+' review '+c[1];loc='Reviews / '+c[0]+' #'+c[1]
   elif len(c)==7 and re.fullmatch(r'\d+/\d+/\d{4}(?: .*)?',c[3]) and c[6].isdigit():
    role='Inspection completion date';dte=c[3].split()[0];work=c[0]+' inspection';result=c[4];ref=no+' / inspection '+c[6];loc='Inspections / '+c[6]
   else:continue
   add(n,statuses,ref,title,'Anchorage',work,result,datetime.strptime(dte,'%m/%d/%Y').date().isoformat(),role,loc,**d)
