"""Federal and territorial reference review. DOI/NTIA grants and terms are distinct from siting permits."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import lib.net as netfetch
import hashlib, io, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pypdf import PdfReader
import lib.discovery as collect
from lib.paths import R
from lib.text import htmltext
from pathlib import Path
from lib.archive import Store
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser
import json, re
STORE=Store('territory_grants');D=R/'cache/territory-grants';D.mkdir(parents=True,exist_ok=True);M=R/'data/territory_grant_sources.json'
SOURCES={'as_doi':('html','https://www.doi.gov/node/35000'),'as_just':('pdf','https://www.doi.gov/sites/default/files/fy2022-oia-budget-justification.pdf'),'as_fcc':('pdf','https://docs.fcc.gov/public/attachments/DA-26-578A1.pdf'),'as_btop':('html','https://www2.ntia.doc.gov/grantee/american-samoa-government'),'vi_fonsi':('pdf','https://www2.ntia.doc.gov/sites/default/files/grantee/4816_virgin_islands_fonsi_040411.pdf'),'vi_letter':('pdf','https://www.doi.gov/sites/default/files/usvi-receives-3417256.33-in-tap-map-and-cares-act-funds-for-fy-2021.pdf'),'vi_schedule':('pdf','https://omb.vi.gov/wp-content/uploads/2023/01/FY23-FY24-Executive-Budget-Book.pdf'),'vi_operating':('pdf','https://energy.vi.gov/wp-content/uploads/2025/01/USVI-Territory-Energy-Security-Plan-2024-Final.pdf'),'mp_bead':('html','https://bpd.cnmi.gov/about-us/b-e-a-d-documents/'),'mp_cpf':('html','https://bpd.cnmi.gov/about-us/capital-projects-fund/'),'mp_stats':('html','https://www.census.gov/about/partners/sdc/member-network/northern-mariana-islands.html'),'mp_business':('html','https://www.eda.gov/archives/2022/grants/2021/'),'mp_project':('html','https://opd.gov.mp/cnmi-broadband-project.html'),'vi_service':('pdf','https://cdbgdr.vihfa.gov/wp-content/uploads/2024/05/3.-Business-Technology-Group-Contract-No.-2022-CDBG-DR-006-DC-SIGNED.pdf')}
SOURCES.update({'as_tx':('json','https://api.usaspending.gov/api/v2/awards/ASST_NON_D20AP00079_014/'),'vi_tx':('json','https://api.usaspending.gov/api/v2/awards/ASST_NON_D21AP10148_014/'),'mp_master':('pdf','https://bpd.cnmi.gov/wp-content/uploads/2026/06/CNMI-BPD-BEAD-Subgrant-Agreement-Master.pdf'),'mp_exa':('pdf','https://bpd.cnmi.gov/wp-content/uploads/2026/05/Exhibit-A_-Project-Description-and-Scope-of-Work-MASTER.pdf'),'mp_exd':('pdf','https://bpd.cnmi.gov/wp-content/uploads/2026/05/Exhibit-D_-Environmental-Review-Forms-MASTER.pdf')})
SOURCES.update({'samoa_other':('pdf','https://regulator.gov.ws/images/Spectrum/Digital_Samoa_Project.pdf')})
SOURCES.update({'vi_ea':('pdf','https://www2.ntia.gov/sites/default/files/grantee/4816_virgin_islands_executive_summary.pdf'),'vi_cd450':('pdf','https://www2.ntia.gov/sites/default/files/grantees/virginislands_infrastructure_cd-450.pdf')})
def j(p):return json.loads(p.read_text()) if p.exists() else {}
def pin(url,b,ext,**more):
 s=hashlib.sha256(b).hexdigest();p=D/(s+'.'+ext);p.write_bytes(b);return dict(url=url,sha256=s,ext=ext,path=str(p.relative_to(R)),bytes=len(b),retrieved=datetime.now(timezone.utc).isoformat(),**more)
def cnmi_curl(url):
 # System curl supports the public server's TLS settings; require a successful robots check and respect the published rules.
 assert url.startswith('https://bpd.cnmi.gov/')
 return netfetch.get(url,transport='curl',timeout=45,limit=40000000)
def fetch():
 m=j(M);hp=R/'data/territory_grant_fetch_holds.json';hold=j(hp)
 def one(item):
  k,(ext,url)=item
  if k in m:return k,m[k],None
  try:
   if url.startswith('https://bpd.cnmi.gov/'):b=cnmi_curl(url)
   else:
    s=STORE.get(url,ext);b=STORE.read(s) if ext!='json' else __import__('gzip').decompress((STORE.d/(s['sha256']+'.json.gz')).read_bytes())
   if ext=='pdf':assert b.startswith(b'%PDF')
   return k,pin(url,b,ext),None
  except Exception as e:return k,None,dict(url=url,error=str(e))
 with ThreadPoolExecutor(max_workers=5) as ex:
  for k,r,e in ex.map(one,SOURCES.items()):
   if e:hold[k]=e
   else:m[k]=r;hold.pop(k,None)
   collect.dump(M,m);collect.dump(hp,hold);print(k,str(e or 'ok')[:120],flush=True)
def usas():
 api='https://api.usaspending.gov/api/v2/search/spending_by_award/';collect.policy(api);m=j(M)
 for code,state,yr,kw in [('as','AS','2020','data'),('vi','VI','2021','data')]:
  key=code+'_usa_search';q={'filters':{'award_type_codes':['02','03','04','05'],'time_period':[{'start_date':str(int(yr)-1)+'-10-01','end_date':yr+'-09-30'}],'place_of_performance_locations':[{'country':'USA','state':state}],'keywords':[kw]},'fields':['Award ID','Description','Recipient Name','Award Amount','Start Date','Awarding Agency','Awarding Sub Agency'],'page':1,'limit':100};req=Request(api,data=json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':collect.AGENT})
  try:
   b=netfetch.request(api,json_body=q,timeout=40).body;v=json.loads(b);assert 'results' in v;print(state,len(v['results']),[(r['Award ID'],r['Description'][:110]) for r in v['results']][:15]);m[key]=pin(api,b,'json',method='POST',body=q);collect.dump(M,m)
  except Exception as e:print(state,e)
if __name__=='__main__':
 if '--fetch' in sys.argv:fetch()
 if '--usas' in sys.argv:usas()
def mp_bounded():
 # One bounded award screen for each exact physical-computing term; covers grants and cooperative agreements.
 api='https://api.usaspending.gov/api/v2/search/spending_by_award/';collect.policy(api);m=j(M)
 for kw in ('data center','data centre','colocation'):
  key='mp_usa_'+kw.replace(' ','_');q={'filters':{'award_type_codes':['02','03','04','05'],'time_period':[{'start_date':'2007-10-01','end_date':'2026-11-16'}],'place_of_performance_locations':[{'country':'USA','state':'MP'}],'keywords':[kw]},'fields':['Award ID','Description','Recipient Name','Award Amount'],'page':1,'limit':100}
  b=netfetch.request(api,json_body=q,timeout=45).body;v=json.loads(b);assert 'results' in v and not v['page_metadata']['hasNext'];m[key]=pin(api,b,'json',method='POST',body=q);collect.dump(M,m);print(kw,len(v['results']),[(r['Award ID'],r['Description'][:75]) for r in v['results']][:9])
if __name__=='__main__' and '--mp-screen' in sys.argv:mp_bounded()

def build_review():
 m=j(M)
 def source(k):
  s=m[k];b=(R/s['path']).read_bytes();assert len(b)==s['bytes'] and hashlib.sha256(b).hexdigest()==s['sha256'];return b
 def pages(k,p):
  s=m[k];b=source(k)
  if s['ext']=='html':return htmltext(b)
  if s.get('ocr_path'):
   o=(R/s['ocr_path']).read_bytes();assert hashlib.sha256(o).hexdigest()==s['ocr_sha256'];return ' '.join(json.loads(o)[p-1])
  return ' '.join(PdfReader(io.BytesIO(b)).pages[p-1].extract_text().split())
 ledger=[]
 def e(st,k,page,anchor,result,why,date=None):
  assert anchor in pages(k,page),(k,page,anchor)
  ledger.append(dict(state=st,source_id=k,source_url=m[k]['url'],source_sha256=m[k]['sha256'],page=page,anchor=anchor,disposition=result,reason=why,action_date=date))
 e('AS','as_just',36,'procure a back-up data center','grant funding, not permit','Federal budget identifies backup data-center procurement in addition to an upgrade. No named locality, lot, or new building authorization.')
 e('AS','as_btop',None,'Data Collection, Integration, and Validation','excluded: broadband planning','NTIA state broadband planning and data collection are not data-center development.')
 e('AS','samoa_other',1,'resilient government data centre','excluded: wrong sovereign','The Office of the Regulator, Samoa, described its proposed Digital Samoa Project; it does not identify a facility in American Samoa.')
 e('VI','vi_letter',2,'the Data Center Maintenance Management Solution Project','grant funding, not permit','The Interior award letter names BIT and the project, with $175,000; neither a parcel-specific grant nor a permit.','2021-06-15')
 e('VI','vi_operating',18,'St. Croix Data Center','operating context only','The territorial energy plan names St. Croix and St. Thomas data centers operated by BIT. The grant does not allocate its award to either site; do not count two projects.')
 e('VI','vi_fonsi',14,'Issued: 04/04/2011','excluded: network-only environmental decision','The FONSI is for the viNGN territory-wide middle-mile fiber system and enclosed fiber access points described on pp. 1–2; not a data center approval.','2011-04-04')
 e('VI','vi_ea',11,'middle mile network','excluded: network-only scope','The NTIA environmental executive summary identifies the network and anchor institutions. Co-location of network access equipment is not a hosting facility.')
 e('VI','vi_service',1,'Network Infrastructure Upgrade','excluded: infrastructure service contract','VIHFA procured a network upgrade. Exhibit scope includes main, private cloud and disaster recovery functions; an executed technology services contract is not a site, construction, grant or NEPA approval for a hosting facility.')
 e('MP','mp_master',1,'Agreement Date: May 13, 2026','excluded: signed broadband award','Executed Government of the CNMI–IT&E master agreement; the named grantee and its Saipan office are not a data-center project.','2026-05-13')
 e('MP','mp_exa',2,'The Subgrantee must deploy, operate, and maintain the network','excluded: network access scope','Exhibit A establishes network deployment within project funding areas and service obligations. No named data center or hosting site identified.','2026-05-13')
 e('MP','mp_exa',4,'prohibited from commencing construction','excluded: prospective clearance','Exhibit A conditions construction on environmental and historic-preservation review. It does not itself grant project-specific NEPA clearance.','2026-05-13')
 e('MP','mp_exd',2,'complete the attached forms/checklists','excluded: environmental review form','Exhibit D is a review process and forms, not a signed NEPA finding.','2026-05-13')
 e('MP','mp_cpf',None,'Cable Landing Station, conduits, and supporting infrastructure','excluded: cable landing','The CNMI describes capital-fund cable landing assets. Evidence does not establish a compute or hosting facility.')
 e('MP','mp_stats',None,'Department of Commerce Central Statistics Division','excluded: statistics office','The Census State Data Center partner is the central statistics division; it is not evidence of a server facility.')
 for key in ('mp_usa_data_center','mp_usa_data_centre','mp_usa_colocation'):
  q=json.loads(source(key));assert not q['results'] and not q['page_metadata']['hasNext']
  ledger.append(dict(state='MP',source_id=key,source_url=m[key]['url'],source_sha256=m[key]['sha256'],disposition='bounded federal grant query: 0 hits',filters=m[key]['body']['filters'],reason='No match in this federal award-text query; confidential network designs, local permits, subawards and records without matched terminology are not covered.'))
 collect.dump(R/'data/territory_grant_dispositions.json',ledger)
 for st,key,ref,title,verifier,info in [('AS','as_tx','D20AP00079','American Samoa Power Authority data center network upgrade','as_just','Upgrade and backup data center procurement. No specific island address or land-use authorization in the award.'),('VI','vi_tx','D21AP10148','USVI Bureau of Information Technology Data Center Maintenance Management Solution','vi_letter','Maintenance management funding. Prime recipient is the territorial Office of Management & Budget; the award explicitly identifies BIT. No attribution to one or both of the two named territorial data centers.')]:
  v=json.loads(source(key));assert v['description'] and ref in v['generated_unique_award_id'] and v['date_signed']
  detail=dict(federal_issuer='U.S. Department of the Interior — Office of Insular Affairs',federal_reference=ref,action_date=v['date_signed'],total_obligation_usd=v['total_obligation'],recipient=v['recipient']['recipient_name'],location_scope='territory only; no site address established',scope=info,source_sha256=m[key]['sha256'],government_corroboration=m[verifier]['url'],performance_period=v['period_of_performance'],record_class='Federal financial assistance, not a permitting or environmental decision')
  vout=dict(id='territory-grant-'+ref.lower(),dataset='Interior insular data-center financial assistance',state=st,jurisdiction='American Samoa' if st=='AS' else 'U.S. Virgin Islands',record_no=ref,project=title,kind='Federal financial assistance',status='Awarded',date=v['date_signed'],date_role='Federal award date_signed (USAspending)',url='https://www.usaspending.gov/award/'+v['generated_unique_award_id'],source_url=m[key]['url'],locator='Federal award / '+ref+'; description, recipient, date_signed and period_of_performance',details=detail)
  collect.dump(series_path('territorygrant_'+st.lower()),[vout])
 print(len(ledger),'dispositions; 2 federal grants, 0 construction/land-use/NEPA site approvals')
if __name__=='__main__' and not set(sys.argv[1:]):build_review()
