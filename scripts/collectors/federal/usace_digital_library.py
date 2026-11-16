"""Bounded CONTENTdm search, pinned original review, docket overlap and publication; offline by default."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, csv, re, collections
from datetime import date
from urllib.parse import quote
import fitz
import lib.discovery as c
from lib.url_archive import Archive
LIB='https://usace.contentdm.oclc.org/digital';CO='p16021coll15';REG='Army Corps Digital Library project actions'
SELECT=[8300,8406,11021,10863,8222,9780,3944,2705,6603,7282,1248,9379,6427,6976]
REV=[8406,9780,2705,3944,9379,10863,7282,1248,6976]
def search(coll,t):return f'{LIB}/api/search/collection/{coll}/searchterm/{quote(t,safe="")}/mode/exact/maxRecords/50'
def meta(n):return f'{LIB}/api/singleitem/collection/{CO}/id/{n}'
def original(n):return f'{LIB}/api/collection/{CO}/id/{n}/download'
ACTIONS=[
 (8406,'evergreen','OR','Hillsboro','Washington County','NWP-2024-484','Evergreen North Data Center','Public notice published','2025-02-27','notice publication date','p. 1, issue date, file, location, project purpose and description','Dated notice of an application for work in wetlands and a ditch. The applicant is Trammell Crow Portland Development Inc. No issuance is established.',['February 27, 2025','Evergreen North Data Center','Hillsboro, Washington County, Oregon']),
 (9780,'cmh205-verification','OH','Jeffersonville','Fayette County','LRH-2010-276-SCR','Amazon Web Services CMH 205 — Phase I','Previously authorized under a Nationwide Permit 39 verification','2025-02-06','prior verification date documented by district','p. 1, Project History; June 6 public notice','The Corps states it previously verified Phase I under NWP 39 for 0.46 acre of two wetlands under the same file. No present status, expiration, or further-phase approval is inferred.',['On February 6, 2025','0.46 acre','previously authorized under a Nationwide Permit 39 verification','with the same file number']),
 (9780,'cmh205-notice','OH','Jeffersonville','Fayette County','LRH-2010-276-SCR','Amazon Web Services CMH 205 — subsequent work','Public notice published','2025-06-06','notice publication date','p. 1, publication date, file, project location and §404 permit application','The district sought comments on additional work under Section 404. This notice is separate from the earlier Phase I verification.',['June 6, 2025','CMH 205 Data Center','Jeffersonville, Fayette County, Ohio','has received an application']),
 (2705,'elk-grove','IL','Elk Grove Village','Cook County','LRC-2021-849','Prime Data Centers — Elk Grove Village','Approved jurisdictional determination','2022-01-21','approved determination report completion date','p. 1, Sections I(A)–(C), report completion date and district file','This approved determination addresses aquatic jurisdiction at the site; it is not a permit authorizing construction or a discharge.',['January 21, 2022','Prime Data Centers','Elk Grove Village','APPROVED JURISDICTIONAL DETERMINATION']),
 (10863,'hut8-aggregate','LA','St. Francisville','West Feliciana Parish','MVN-2025-00741-CO','HUT 8 AI Data Center — temporary aggregate offloading','Public notice published','2026-02-09','notice publication date','pp. 1–2, date, permit application, location and Overall Project Purpose','The applicant proposed a temporary barge unloading and aggregate stockpile area for construction of the named campus. The location is the support work site, not an inferred data hall footprint. No permit issuance is stated.',['February 9, 2026','West Feliciana Parish','HUT 8 AI Data Center','Offload and temporarily store aggregate material'])]
def canonical(s):
 m=re.search(r'\b([A-Z]{3})[- ](\d{4})[- ](\d+)',str(s).upper())
 return f'{m[1]}-{m[2]}-{int(m[3]):05}' if m else ''
def classify(r,cutoff,perm,no,app,obs):
 if r.get('dataset')!=REG:return None
 if r['id']=='fed-library-cmh205-verification' and r['status']==ACTIONS[1][7] and r['record_no']=='LRH-2010-276-SCR':
    return perm('OH:USACE:ORM','unconfirmed','The district expressly records an earlier NWP 39 verification for Phase I, but does not certify current effectiveness.',date.fromisoformat(r['date']),stable_no='LRH-2010-00276-SCR')
 if r['status']=='Public notice published':return app()
 if r['status']=='Approved jurisdictional determination':return no('An approved jurisdictional determination is not authorization to build or discharge.','decision')
 return no('Unmapped library event.','unknown')
def run(fetch=False):
 a=Archive('corpslibrary',fetch,owner='federal/usace_digital_library');extra=Archive('corpslib_queries',fetch,owner='federal/usace_digital_library',name='queries_sources.json');aud=[];allitems={};meta_info={};docs={};out=collections.defaultdict(list)
 # Old project-management collection discovery is not added to permitting-only counts.
 for co in [CO,'p16021coll9']:
  for term in ['data center','datacenter','Amazon Data Services','Microsoft Corporation','QTS','Google LLC','Meta Platforms','hyperscale','server farm','cloud computing']:
   u=search(co,term);store=a if u in a.sources else extra
   d=store.json(u);f=d['fields']['queries'][0];assert f['mode']=='exact' and f['searchTerm']==term
   aud.append(dict(collection=co,term=term,total=d['totalResults'],examined_first_page=len(d['items']),url=u,sha256=store.sources[u]['sha256']))
   for v in d['items']:allitems[(v['collectionAlias'],int(v['itemId']))]=v['title']
 for n in SELECT:
  m=a.json(meta(n));m={z['key']:z['value'] for z in m['fields']};meta_info[n]=m
  if n in REV:
   b,h=a.get(original(n))
   if b.startswith(b'%PDF'):
    with fitz.open(stream=b,filetype='pdf') as pdf:docs[n]=[c.norm(p.get_text()) for p in pdf]
 with (c.OUT/'federal_history.csv').open() as f:others=[r for r in csv.DictReader(f) if not r['id'].startswith('fed-library-')]
 known={(canonical(r['record_no']),r['date']) for r in others if canonical(r['record_no'])};held=[]
 for n,tag,st,local,co,no,project,status,day,role,loc,scope,anchors in ACTIONS:
  if (canonical(no),day) in known:held.append([n,no,day]);continue
  text=' '.join(docs[n][:2])
  assert c.norm(no) in text and all(c.norm(v) in text for v in anchors),(tag,anchors)
  det=dict(federal_issuer='US Army Corps of Engineers',scope=scope,corps_file=no,document_id=n,library_record=meta(n),library_metadata_sha256=a.sources[meta(n)]['sha256'],association='off-site project support' if n==10863 else 'direct site action',district=meta_info[n]['distri'])
  out[st].append(dict(id='fed-library-'+tag,state=st,jurisdiction=local,county=co,dataset=REG,record_no=no,project=project,kind='Nationwide permit verification' if tag=='cmh205-verification' else 'Jurisdictional determination' if n==2705 else 'District public notice of application',status=status,date=day,date_role=role,url=original(n),source_url=original(n),source_sha256=a.sources[original(n)]['sha256'],locator=loc,details=det))
 for st in {v[2] for v in ACTIONS}:c.dump(series_path(f'corpslibrary_{st.lower()}'),out[st])
 judgments={8300:'Existing St. Joseph County AWS district file; no second event claimed.',11021:'Possible third-party mitigation bank; no reviewed site-specific federal approval for a named data center.',8222:'Missouri excluded.',3944:'Johnstown OH AJD duplicates LRH-2023-00824-MUS, 2023-12-01.',9379:'Hillsboro OR AJD duplicates NWP-2025-00021, 2025-05-16.',6427:'Forest Grove OR AJD duplicates NWP-2023-00301, 2024-04-09.',6603:'Florida metadata alone does not establish an eligible data-center project.',7282:'Osceola county project drawing labels a data center among other civic buildings. No independently identified hosting campus; held.',1248:'Compound library item; download response is not a verified PDF. Held.',6976:'iHeart Church expansion, weather data attributed to National Climatic Data Center; false positive.'}
 c.dump(c.R/'data/national/corps_library_audit.json',dict(cutoff='2026-11-15',queries=aud,distinct_first_page_items=len(allitems),metadata_inspected=len(meta_info),original_downloads_attempted=len(REV),readable_original_pdfs=len(docs),existing_same_day_docket_holds=held,events=sum(map(len,out.values())),items=[dict(collection=co,item_id=n,title=t,review=judgments.get(n,'Original verified; see result events') if co==CO and n in SELECT else 'Not substantively reviewed in bounded cohort; no conclusion') for (co,n),t in sorted(allitems.items())],scope='Exact-phrase, first 50 per query in two permitting collections. Metadata alone never publishes an action. No Virginia or Missouri records exported.'))
 print(len(aud),'queries;',len(allitems),'distinct first-page hits;',len(docs),'originals read;',sum(map(len,out.values())),'events')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
