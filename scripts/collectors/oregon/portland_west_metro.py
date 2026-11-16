"""West metro source archive and replay; see docs/westmetro.md."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path, R
import argparse, hashlib, io, json, re, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pypdf import PdfReader
from lib.archive import Store
from lib.text import htmltext
import lib.discovery as collect
S=Store('westmetro');D=R/'cache/westmetro';D.mkdir(parents=True,exist_ok=True);M=R/'data/westmetro_sources.json'
SOURCES={
'ca_sc_code':('pdf','https://www.santaclaraca.gov/home/showpublisheddocument/85006/638623530602619763'),
'ca_sc_publish':('html','https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/zoning'),
'ca_sj_manual':('html','https://www.sjeconomy.com/how-we-help/programs-and-services/powering-san-jos-energy-infrastructure-for-data-centers'),
'ca_sj_projects':('html','https://www.sanjoseca.gov/your-government/departments-offices/planning-building-code-enforcement/planning-division/data-center-and-other-large-energy-use-projects'),
'ca_fremont_manual':('html','https://www.fremont.gov/government/departments/community-development/planning-building-permit-services/data-centers'),
'or_hil_code':('pdf','https://hillsboro-oregon.civicweb.net/document/264817/'),
'or_hil_review_2024':('pdf','https://www.hillsboro-oregon.gov/home/showpublisheddocument/31197/638647612663370000'),
'or_hil_review_2023':('pdf','https://www.hillsboro-oregon.gov/home/showpublisheddocument/31221/638647629167830000'),
'or_hil_moratorium':('html','https://www.hillsboro-oregon.gov/Home/Components/News/News/17551/'),
'or_hil_projects':('pdf','https://hillsboro-oregon.civicweb.net/document/260495/Handouts.pdf?handle=CD1D771D248940AC8DDA9686CF1E6A7D'),
'or_umatilla_22':('pdf','https://www.umatilla.gov/sites/default/files/fileattachments/planning/meeting/7536/january_24_2022_planning_commission_packet.pdf'),
'nh_portsmouth_review':('html','https://www.portsmouthnh.gov/planportsmouth/land-use-and-zoning-regulations')}
SOURCES.update({
'ca_sc_staff':('html','https://santaclara.legistar.com/LegislationDetail.aspx?ID=8260886&GUID=2791DE9D-56B5-49B5-9998-BC1264149D06&FullText=1'),
'ca_sc_gen':('html','https://santaclara.legistar.com/LegislationDetail.aspx?FullText=1&GUID=25408312-6834-469E-B545-48CCFFBD1814&ID=7404898'),
'ca_sj_appeal':('html','https://sanjose.legistar.com/LegislationDetail.aspx?ID=8279316&GUID=8B6AFBDB-F05D-48C6-B7E5-AAB309025968'),
'ca_sj_nod':('html','https://ceqanet.lci.ca.gov/2021020002/6'),'ca_sc_nod':('html','https://ceqanet.lci.ca.gov/2023030248/2'),
'ca_sj_holger':('html','https://ceqanet.lci.ca.gov/2026070652'),
'or_state_reporting':('html','https://db.lcd.state.or.us/papa_website_reports/PublicNoticeAdoptedAmendments.aspx'),
'or_hillsboro_historic':('pdf','https://www.oregon.gov/energy/get-involved/Documents/2026-04-24-3-Dan-Dias-City-of-Hillsboro-OR-DCAC-Land-Use-Presentation.pdf'),
'or_boardman_decision':('pdf','https://mccmeetingspublic.blob.core.usgovcloudapi.net/boardmanor-meet-51eb5a08bc0f4218a1eeb8b8c76eb90f/ITEM-Attachment-001-9ee6d76af3754084a0249b0cfc3f22ef.pdf'),
'or_boardman_agenda':('html','https://meetings.municode.com/adaHtmlDocument/index?cc=BOARDMANOR&ip=True&me=ef21ab3c77a344fbb5bddb4b57a9a1f7'),
'or_hermiston_state':('pdf','https://www.oregon.gov/lcd/Commission/Documents/2026-02Item%209_Exhibit_1.pdf'),
'or_state_morrow':('pdf','https://www.oregon.gov/lcd/Commission/Documents/2023-11_Item_4_Combined.pdf'),
'or_umatilla_cu':('pdf','https://yourwater.oregon.gov/docs/prletters/00914-pr-2024-16-ca.pdf')})
SOURCES.update({
'nh_durham_codeindex':('html','https://www.durhamnh.gov/686/Zoning-Ordinance'),
'nh_portsmouth_code':('pdf','https://files.portsmouthnh.gov/files/planning/ZoningOrd.pdf'),
'nh_portsmouth_siteplan':('pdf','https://files.portsmouthnh.gov/files/planning/SitePlanReviewRegs.pdf'),
'or_morrow_court':('pdf','https://www.oregon.gov/luba/Docs/Opinions/2024/01-24/23074.pdf'),
'or_morrow_public':('pdf','https://www.morrowcountyor.gov/sites/default/files/fileattachments/planning/page/16600/ordinance_ord-2023-6_and_final_findings_with_attachment_-_signed.pdf'),
'or_morrow_index':('html','https://www.morrowcountyor.gov/planning/page/2020-current'),
'ca_sc_walsh':('pdf','https://files.ceqanet.lci.ca.gov/249865-4/attachment/FL8y_k0VIfPhCjjKdh4TiF_mbXE52HbyrJkA-tbh0vtWLEvD427XJxmTU_f7mpDT-d7rkDVBsjtIP1G00')})
SOURCES.update({'ca_sj_zen':('pdf','https://sanjose.legistar.com/View.ashx?GUID=45405DAD-B2C3-48A7-9925-7BD4A88945E4&ID=5502798&M=F'),'ca_sj_current':('pdf','https://sanjose.legistar.com/View.ashx?M=F&ID=16056352&GUID=FBC5B377-0586-4942-ADF2-E1751F5B1119'),'ca_sj_attachment':('pdf','https://sanjose.legistar.com/View.ashx?M=F&ID=16056383&GUID=BF0EDB0E-476A-4856-AA8E-F3CF50BE805F'),'nh_durham_table':('pdf','https://www.durhamnh.gov/DocumentCenter/View/20818/Section-175-53-Table-of-Uses')})
SOURCES.update({'or_morrow_2025':('pdf','https://www.morrowcountyor.gov/sites/default/files/fileattachments/planning/page/16600/signed_ord-2025-02_w_attachments.pdf'),'or_hillsboro_engage':('html','https://engage.hillsboro-oregon.gov/data-centers'),'or_open_hillsboro':('html','https://www.portland.gov/ppd/portlandmaps-help-guides/portlandmaps-general-search')})
SOURCES.update({'nh_nottingham':('pdf','https://www.nottingham-nh.gov/sites/g/files/vyhlif3611/f/pages/2026_nottingham_special_town_election_results.pdf')})
SOURCES.update({'ca_hay_minutes':('pdf','https://hayward.legistar.com/View.ashx?GUID=6A816E4B-3966-4A72-AB46-DD485402E725&ID=1306703&M=M'),'ca_hay_staff':('html','https://hayward.legistar.com/LegislationDetail.aspx?From=RSS&FullText=1&GUID=4C37C260-C950-440F-B68C-826967AFB56C&ID=7400268'),'ca_sac_nod':('html','https://ceqanet.lci.ca.gov/1996122010/10')})
def existing(p):return json.loads(p.read_text()) if p.exists() else {}
def fetch():
 m=existing(M);hp=R/'data/westmetro_fetch_holds.json';h=existing(hp)
 def one(k):
  if k in m:return k,m[k],None
  if k in h and '--retry-holds' not in sys.argv:return k,None,h[k]
  ext,url=SOURCES[k]
  try:
   r=S.get(url,ext);b=S.read(r)
   if ext=='pdf' and not b.startswith(b'%PDF'):raise ValueError('No PDF signature')
   p=D/(r['sha256']+'.'+ext);p.write_bytes(b);return k,dict(**r,path=str(p.relative_to(R)),retrieved=datetime.now(timezone.utc).isoformat()),None
  except Exception as exc:return k,None,dict(url=url,error=str(exc))
 with ThreadPoolExecutor(max_workers=6) as ex:
  for k,r,e in ex.map(one,SOURCES):
   if e:h[k]=e
   else:m[k]=r;h.pop(k,None)
   collect.dump(M,m);collect.dump(hp,h);print(k,(e or {}).get('error','OK'),flush=True)
if __name__=='__main__' and '--fetch' in sys.argv:fetch()

# No date is inferred for independently confirmed rules without an enactment date.
RULES=[
('ca-sc-west-cup','CA','Santa Clara','city','0669084','conditional use','ca_sc_staff',0,'2026 City Council report 26-1037, Zoning Code','only ancillary data centers are allowed','Lists stand-alone data centers as conditional uses in LO-RD, LI and HI. Only ancillary data centers are allowed in HO-RD. The report separately identifies a site-specific 2025 rule for the Related Santa Clara project; check site overlays.'),
('ca-sc-west-ancillary','CA','Santa Clara','city','0669084','definition','ca_sc_staff',0,'2026 City Council report 26-1037, Zoning Code','a maximum power draw of 9MW','An ancillary data center serves the private needs of the industrial user and is subordinate to the primary use; it is limited to 20% of the building square footage on the site and 9 MW maximum draw.'),
('ca-sc-west-architecture','CA','Santa Clara','city','0669084','site plan','ca_sc_staff',0,'2026 City Council report 26-1037, Zoning Code','an Architectural Review Permit through a Development Review Hearing','The updated code requires a stand-alone facility to obtain a Planning Commission conditional use permit and an architectural review permit through a development review hearing.'),
('ca-sc-west-generator','CA','Santa Clara','city','0669084','backup generation','ca_sc_gen',0,'City staff report 25-448; Updated Zoning Code, Light Industrial','back-up generators require a minor use permit','The city distinguishes the conditional use permit for a data center in LI from the minor use permit for backup generators under the updated code. The staff report separately describes the prior rule, which governed the reviewed application.'),
('ca-sc-west-recycled','CA','Santa Clara','city','0669084','water supply','ca_sc_staff',0,'City Code §13.15.160 as described in report 26-1037','to use recycled water for approved uses, where it is available','Development projects including data centers must use recycled water for approved uses where it is available. This is a generally applicable local rule, distinct from a state water permit.'),
('ca-sj-west-ip','CA','San Jose','city','0668000','conditional use','ca_sj_attachment',1,'Planning Director’s July 8, 2026 Holger permit record, Attachment A p. 1; IP district','which allows “data center” use subject to approval of a SUP','The city interprets the Industrial Park (IP) zoning district as allowing data centers subject to a special use permit. The cited decision does not determine other districts or the outcome for another site.'),
('or-hillsboro-west-interim','OR','Hillsboro','city','4134100','moratorium','or_hillsboro_engage',0,'City Community Development Code Amendments, July 27, 2026 action','120-day land use moratorium','The city enacted a 120-day moratorium on new applications for data center and battery energy storage system development on July 27, 2026. The city describes a possible six-month extension; no later vote is inferred as of November 16. This is separate from Oregon enterprise-zone incentives.'),
('nh-nottingham-west-moratorium','NH','Nottingham','town','3301557460','moratorium','nh_nottingham',1,'Special Town Election, Sept. 8, 2026, official result PDF, ballot question','establishment, construction, expansion, or operation of data centers','By 1,335 yes to 143 no, voters adopted a 12-month moratorium on acceptance, processing, approval or issuance of permits or approvals for establishing, building, expanding or operating data centers. The official results are handwritten on the ballot; the measure is town-wide.'),
('nh-portsmouth-west-site','NH','Portsmouth','city','3362900','site plan','nh_portsmouth_siteplan',6,'Portsmouth Site Plan Review Regulations, October 2026, §§1.2.1–1.2.2','Nonresidential development or redevelopment including alterations, additions or extensions','The general site-plan regulations cover nonresidential development and redevelopment, including alterations, additions or extensions. Section 1.2.2 separately permits the Director to exempt small projects meeting its three criteria. This does not classify a data center as a permitted use.'),
('nh-portsmouth-west-pease','NH','Portsmouth','city','3362900','zoning authority','nh_portsmouth_review',0,'City planning department, Pease Development Authority Land Use Controls','are subject to the requirements of the Pease Development Authority Land Use Controls','Within the Pease International Tradeport the Pease Development Authority land-use controls are distinct from Portsmouth municipal land-use rules. Do not apply the city rules to a parcel merely because it has a Portsmouth address.')]
def original(key,m):
 s=m[key];raw=(R/s['path']).read_bytes();assert len(raw)==s['bytes'] and hashlib.sha256(raw).hexdigest()==s['sha256']
 return raw
def passage(key,m,page):
 s=m[key];raw=original(key,m)
 if page:
  if s.get('ocr_path'):
   o=(R/s['ocr_path']).read_bytes();assert hashlib.sha256(o).hexdigest()==s['ocr_sha256'];return ' '.join(' '.join(json.loads(o)[page-1]).split())
  return ' '.join(PdfReader(io.BytesIO(raw)).pages[page-1].extract_text().split())
 return htmltext(raw)
def build():
 from collectors.oregon.portland_maps import replay
 m=existing(M);out=[]
 for id,st,ju,lv,g,topic,k,page,loc,ev,summ in RULES:
  assert ev in passage(k,m,page),(id,ev)
  r=dict(id=id,state=st,jurisdiction=ju,level=lv,geoid=g,topic=topic,scope='generally applicable' if id in ['ca-sc-west-recycled','nh-portsmouth-west-site','nh-portsmouth-west-pease'] else 'data center specific',summary=summ,status='adopted',locator=loc,url=m[k]['url'],authority=ju,evidence=ev)
  if page:r['source_page']=page
  if k=='nh_nottingham':r['evidence_method']='OCR checked against election officials’ marked results image'
  if k in ['ca_sc_staff','ca_sc_gen','ca_sj_attachment','nh_portsmouth_review','or_hillsboro_engage']:r.update(source_type='government interpretation of adopted rule',status='agency_guidance')
  out.append(r)
 collect.dump(R/'data/westmetro_rules.json',out)
 h={'OR':replay(),'CA':[]}
 def event(st,jur,k,key,number,name,kind,status,date,role,loc,ev,page=0,**detail):
  assert ev in passage(k,m,page),(key,ev)
  detail.update(source_sha256=m[k]['sha256'],evidence=ev)
  if page:detail['source_page']=page
  h[st].append(dict(id='westmetro-'+key,state=st,jurisdiction=jur,dataset='Municipal land-use case records' if st=='CA' else 'Oregon land-use ordinance and review records',record_no=number,project=name,kind=kind,status=status,date=date,date_role=role,url=m[k]['url'],locator=loc,details=detail))
 event('CA','Hayward','ca_hay_minutes','hayward-spr23-0036','SPR-23-0036','STACK Data Center, 26062 Eden Landing Road','Major site plan review and administrative use permit','Approved','2025-05-22','Planning Commission vote','Action Minutes, public hearing PH 25-022, p. 1','approve the proposed Major Site Plan Review and Administrative Use Permit',1,action_scope='Six ayes; approves the joint application. This is not a building permit.',related_url=m['ca_hay_staff']['url'])
 event('CA','Sacramento County','ca_sac_nod','sacramento-prime','SCH 1996122010 / NOD 10','Prime Data Centers expansion, 2407 Ak Street, McClellan Park','Special development permit and design review','Approved','2026-02-05','County project approval','County-filed CEQAnet NOD, project description and Approving Agency','County of Sacramento Approving Agency Role Lead Agency Approved On 2/5/2026',county='Sacramento County',action_scope='Approval of project including setback relief and design review, identified by state clearinghouse number and filing version. Local permit number not given.')
 event('CA','San Jose','ca_sj_current','holger-env-appeal','ER25-243 / SP25-029','300 Holger Way data center environmental appeal','Environmental appeal filing','Received','2026-07-10','Appeal received','Planning Director memorandum, Environmental Appeals, p. 4','The appeal was received on July 10, 2026',4,action_scope='Challenge to the environmental determination, not a new issuance or an appeal of the special use permit. Prior July 8 permit decision already represented in San José planning register 2159664.')
 event('OR','Morrow County','or_morrow_index','morrow-2023','ORD-2023-6','Rowan Percheron: data center zone change on 274 acres','Parcel-specific plan and zoning amendment','Adopted','2023-09-20','Board adoption','County ordinance register, 2023, ORD-2023-6','adopted by the Morrow County Board of Commissioners on September 20, 2023',county='Morrow County',related_url=m['or_morrow_public']['url'],action_scope='Linked plan files AC-145-23, ACM-146-23, AZM-147-23; one county adoption, not three permits. Subject to individual construction approvals, see signed ordinance §1.')
 event('OR','Oregon','or_morrow_court','luba-2023-074','LUBA 2023-074','Rowan Percheron / Morrow County zone-change appeal','Land use appeal disposition','DISMISSED','2024-01-03','LUBA order','LUBA case 2023-074, pp. 1, 3','Petitioner requests that this appeal be dismissed.',3,county='Morrow County',action_scope='State board dismissed at petitioner’s request, not a county permit or decision on the merits.')
 event('OR','Morrow County','or_morrow_index','morrow-2025','ORD-2025-02','Data center and farm use overlay, 1,298-acre parcel','Parcel-specific plan and zoning amendment','Adopted','2025-07-16','Board adoption','County ordinance register, 2025, ORD-2025-02','adopted by the Morrow County Board of Commissioners on July 16, 2025',county='Morrow County',related_url=m['or_morrow_2025']['url'],action_scope='Also redesignates a separate 1,623-acre parcel for agriculture. Underlying four plan files constitute one county adoption; not permission to build four campuses.')
 for st,rows in h.items():
  assert len(rows)==len({r['id'] for r in rows});collect.dump(series_path('westmetro_'+st.lower()),sorted(rows,key=lambda r:r['id']))
 print(len(out),'rule provisions;',[(s,len(v)) for s,v in h.items()])
if __name__=='__main__' and '--fetch' not in sys.argv:build()
