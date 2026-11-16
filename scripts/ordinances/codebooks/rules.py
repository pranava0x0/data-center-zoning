"""Join a fixed, manually reviewed document set to the ranked codebook archive, then verify each rule on its cited page."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, json, hashlib, re
from pathlib import Path
from pypdf import PdfReader
R=Path(__file__).resolve().parents[3]
BOOKS={
'd79c7f95':('Cherrytree Township','township','Ord. 01-2026, enacted Nov. 2, 2026; effective five days after enactment, §13, PDF p. 7.'),
'ebf717b0':('Summit Township','township','Amendment 2026-02, effective Sept. 26, 2026 (cover); Erie County.'),
'bf577bbe':('Trappe Borough','borough','Consolidated code amended Sept. 1, 2026 and linked on the Borough’s current code index; not the amendment’s separately established effective date.'),
'7df914a1':('Ligonier Township','township','Ord. 2026-OR-01 effective Aug. 25, 2026, per codifier note 22, PDF p. 51; Westmoreland County.'),
'4c4bccd1':('Hammond','city','City-published zoning compilation; amendment Ord. 9411. Original date of amendment not established by the two provisions.'),
'1f55287b':('Bowdon','city','City’s zoning department identifies September 8, 2025 as adoption date of the ordinance.'),
'8cc6dc0c':('Barry Township','township','Ordinance 2026-1 (2026 signed edition, verified on township index); Pine County. The discovery CSV mistakenly names Barry city.'),
'8d4a797d':('Hillman','village','Signed village ordinance, published Oct. 28 and effective Nov. 5, 2026, certification PDF p. 299.'),
'243e3564':('Sherburne County','county','Ord. 292 adopted July 14, 2026 as stated on the cover and enactment page; no date imputed from the blank effective-date line.')}
# Jurisdiction, topic, citation, source page, quoted anchor, bounded interpretation.
ROWS=[
('pa-cherrytree-conditional','d79c7f95','conditional use','§4.03(C)(7), (D)(5)',4,'Premises must be entirely contained within the Commercial District.','Lists data centers as conditional uses subject to Board of Supervisors review and action. The entire premises must be within the Commercial District.'),
('pa-summit-erie-special','ebf717b0','conditional use','§311.10 Industrial table, §401.41(A), PDF pp. 74, 127',127,'Prior to the commencement of the Special Exception hearing','The industrial district table assigns data centers and data center accessory uses to the special-exception route; §401.41 imposes submissions before that hearing.'),
('pa-summit-erie-water','ebf717b0','water supply','§401.41(H), PDF p. 132',132,'A Water Utilization Report shall be submitted with the zoning application','The zoning application must include an engineer-certified water report documenting daily volume and sources, discharge volumes and destinations, and cooling design. Approval requires adequate supply; the service provider must document capacity.'),
('pa-summit-erie-cooling','ebf717b0','cooling','§401.41(K), PDF p. 133',133,'All new data centers and qualifying expansions must employ closed-loop cooling','Requires closed-loop cooling for server racks and IT equipment in new facilities and qualifying expansions. An alternate system requires a showing of infeasibility, a conditional exemption and applicable state permits.'),
('pa-summit-erie-emissions','ebf717b0','backup generation','§401.41, emissions standards, PDF p. 131',131,'EPA Tier 4 emissions standards, or equivalent, must be achieved','The township requires backup generators, if used, to meet EPA Tier 4 or equivalent standards. It requires annual testing and reporting to the township and relevant agencies. This is a local zoning condition.'),
('pa-trappe-setback','bf577bbe','setback','§340-254(A)(1)',139,'or 500 feet, whichever is greater','The minimum setback from all property lines is the larger of 500 feet or the maximum setback requirement for the zoning classification. It applies to listed impact sources, including generators and substations.'),
('pa-trappe-sound','bf577bbe','noise','§340-254(B)(1)',139,'operation of emergency generators under load','An application must include a certified consultant’s sound study evaluating the use at the property line. The study includes measurements during normal operations, peak cooling load and emergency-generator operation under load.'),
('pa-ligonier-conditional','7df914a1','conditional use','§120-50A(B)–(C)',52,'Highway Commercial; and, (I-1) Industry.','Newly proposed data centers are conditional uses in C-2 Highway Commercial and I-1 Industry.'),
('pa-ligonier-setback','7df914a1','setback','§120-50A(D)',52,'2000 feet to any property line and 4000 feet to any neighboring residence','The ordinance requires at least 50 acres. A data center building, including fencing as worded in the ordinance, must be at least 2,000 feet from any property line and 4,000 feet from any neighboring residence.'),
('pa-ligonier-permits','7df914a1','building permit','§120-50A(E)(1)–(2)',52,'A building permit is required for construction of any Data Center','New data centers and additions need an approved land-development plan and zoning permit. Data center construction also requires a building permit.'),
('pa-ligonier-water','7df914a1','water supply','§120-50A, utilities (b), PDF p. 53',53,'Each Data Center Building shall be served by Township-approved public water service.','Each data center building must be served by township-approved public water service. The water provision also calls for written confirmation about groundwater, surface water and wells.'),
('in-hammond-i1','4c4bccd1','use permission','Title XI §11.10(28), PDF pp. 79–80',80,'28. Data Center (Am.Ord.9411)','Data centers are a listed permitted use in I-1 Light Industrial. Other applicable environmental, building and site requirements may still apply.'),
('in-hammond-parking','4c4bccd1','parking','§20.45.04, PDF p. 144',144,'One parking space for each employee plus 10% for visitors/customers.','The data center parking formula is one space per employee plus 10 percent for visitors and customers.'),
('ga-bowdon-hi','1f55287b','conditional use','Ch. IV Heavy Industrial, printed p. 50; Table 4.3, PDF p. 30',56,'wireless communications facilities c) data center','Lists a data center as a Communications/Utilities use requiring a special exception in the Heavy Industrial district.'),
('mn-barry-pine-prohibition','8cc6dc0c','use prohibition','Ord. 2026-1 §§4, 20, PDF pp. 5, 23',23,'prohibited in all zoning districts within the Township','The township prohibits the defined data center use in every township zoning district. This is Barry Township, Pine County; it does not apply to the City of Barry in Big Stone County.'),
('mn-sherburne-industrial','243e3564','conditional use','Ord. 292 §7, use matrix, printed p. 58',66,'Data Centers / Server Farms N N N N N C C N','The county table designates data centers/server farms conditional in Industrial and Heavy Industrial and not allowed in the six other listed districts. Applies where the county ordinance governs, not automatically within incorporated cities.'),
('mi-hillman-impact','8d4a797d','environmental review','§7.33(I), printed p. 7-69',262,'the applicant shall provide an environmental and community impact analysis','The applicant must provide an environmental and community impact analysis before the public hearing.'),
('mi-hillman-noise','8d4a797d','noise','§7.33(J), printed p. 7-70',263,'Pre-Development Sound Modeling Study including sound isolines','The application must include a site plan and a sound-modeling study showing sound contours out to all lot lines and dwellings on nonparticipating properties within 500 feet of the lot boundary.')]
HOLDS={
'c144d0ba':'Pending: planning hearing scheduled Nov. 17, 2026; printed enactment language does not show a completed decision.',
'6385ddd6':'Draft 3 Final; adoption of this edition not corroborated.',
'ba77603a':'Draft ordinance has blank adoption date and ordinance number.',
'7efd784d':'Has operative-looking standards but exact enactment not independently confirmed in this review.',
'd6cd5610':'Generic category reference; not enough to establish a route for a data center.',
'64cabfa5':'Amendment annotation in an earlier-dated compilation; independently confirm before promotion.',
'6120b5a0':'Proposed text; latest enactment not verified here.',
'802215da':'HT overlay is explicit; independent adoption/current version check pending.',
'f5bba2b7':'Mentions data center within chip manufacturing planned development; no jurisdiction-wide route established.',
'd2c5defe':'Redline of project-specific planned development.',
'bd1241dc':'Presentation, not adopted code.',
'2874f5a9':'Draft text.',
'9afe0fdc':'Planning comments, not independently enacted section.',
'2d1de617':'Project context is a mixed-use corporate development, not independently verified zoning route.',
'1047cb7f':'Official index labels book under consideration.',
'd0d9cb14':'Government referral labels this a draft.',
'90fe1f4f':'Effective-date blanks and DRAFT mark on cover conflict with neutral referral label.',
'78d99d89':'Explicitly a draft.',
'086207dc':'Wrong discovery geography (actual Hopkins Township, not village); adoption/effective dates blank and no signed certification.',
'9c0511e0':'Draft project-specific PUD.',
'8c6b3fb9':'Definition excludes data centers from another use; no independently confirmed project permission.',
'e60ccbdd':'Use-list reference; effective version and district cross-check not completed.',
'889a0e2b':'Computer server farm table; district columns and current version require verification.',
'48fc4413':'Date-limited order; check successor activity before publishing current applicability.',
'8bef67f4':'Candidate deferred: incorporated rules warrant separate adoption/date and district verification.',
'61453277':'Candidate deferred: township provides revised compilation; verify adopting amendment and changes.',
'3b59c591':'Time-limited amendments require checking later enactments and continuation.'}
DUP=('1793d51c','c5e6e8d8','aa9e6862','4e0333ba','6d1bf627')
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 cat={x['url']:x for x in csv.DictReader((R/'data/national/codebooks.csv').open())}
 targets=set(BOOKS)|set(HOLDS)|set(DUP);checked={}
 for p in (R/'cache/codebooks/checks').glob('*.json'):
  x=read(p);prefix=x.get('sha256','')[:8]
  if prefix in targets and x.get('url') in cat:checked[prefix]=(x,cat[x['url']])
 assert set(checked)==targets,targets-set(checked)
 manifest_path=R/'data/national_rules_astra_sources.json';m=read(manifest_path);outpath=R/'data/national_rules_astra.json';out=read(outpath);byid={x['id']:x for x in out};docs={};rev=[]
 for prefix,(x,b) in sorted(checked.items()):
  s=x['sha256'];p=R/'cache/codebooks/files'/(s+'.pdf')
  if prefix in BOOKS:
   assert hashlib.sha256(p.read_bytes()).hexdigest()==s
   docs[prefix]=PdfReader(p);rec=dict(url=x['url'],sha256=s,bytes=p.stat().st_size,ext='pdf',path=str(p.relative_to(R)),retrieved=x['checked'],referral=b['referral'],referral_sha256=b['referral_sha256']);m['book_'+prefix]=rec
  rev.append(dict(state=b['state'],discovery_jurisdiction=b['jurisdiction'],discovery_geoid=b['geoid'],sha256=s,url=x['url'],referral=b['referral'],state_rank=b['state_rank'],disposition='published' if prefix in BOOKS else 'already published' if prefix in DUP else 'held',reason=BOOKS[prefix][2] if prefix in BOOKS else HOLDS.get(prefix,'Existing base codebook review.'),rows=sum(r[1]==prefix for r in ROWS)))
 for id,k,topic,loc,page,ev,summary in ROWS:
  x,b=checked[k];jur,level,note=BOOKS[k];raw=' '.join(docs[k].pages[page-1].extract_text().split())
  assert ev in raw,(id,ev)
  geoid='2711503736' if k=='8cc6dc0c' else b['geoid']
  r=dict(id=id,state=b['state'],jurisdiction=jur,level=level,topic=topic,scope='data center specific',summary=summary,status='adopted',locator=loc,url=x['url'],authority=jur,evidence=ev,geoid=geoid,source_page=page,version_note=note,related_url=b['referral'])
  if id not in byid:out.append(r)
  else:assert byid[id]==r,id
 save(manifest_path,m);save(outpath,out);save(R/'data/national_rules_astra_codebook_review.json',rev)
 print(f'{len(ROWS)} provisions; {len(BOOKS)} new jurisdictions; {len(rev)} reviewed files; {len(out)} total supplement provisions')
if __name__=='__main__':main()
