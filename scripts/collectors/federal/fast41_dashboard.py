"""FAST-41 project actions, agency-reported actual dates only. No Dashboard entries create permit counts."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path, R, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import lib.net as netfetch
import argparse, json, re
from datetime import date
from collections import Counter
from urllib.parse import urlencode
from lib.text import plain
from lib.archive import NamedArchive as Archive
A=Archive('FAST',owner='federal/fast41_dashboard');API='https://data.permits.performance.gov/resource/mcm3-xbid.json';META='https://data.permits.performance.gov/api/views/mcm3-xbid';PORT='https://www.permitting.gov/projects/current-fast-41-portfolio';BASE='https://www.permits.performance.gov';CUT=date.fromisoformat('2026-11-15')
PF=['project_id','project_title','project_sector','project_sector_type','project_category','project_field_location_state'];SELECT=','.join(PF)
PHRASES=['data center','data centre','datacenter','data storage and data management','high-performance comput','high performance comput','server farm','server campus','compute campus','hyperscale','data hall'];PROJ={
 '124556':{'state':'VA','county':'Henrico County','sector_evidence':'QTS DC5 expansion and wetlands impacts in Corps Norfolk District notice','file':'NAO-2021-02695-RRS','slug':'qts-richmond-technology-park-data-center-5-ric5','district_doc':'https://www.nao.usace.army.mil/Media/Public-Notices/Article/4510991/nao-2021-02695-qts-ric-5-henrico-virginia/'},
 '126036':{'state':'OH','county':'Pike County','sector_evidence':'Two data center buildings explicitly identified in the Council executive director decision','file':'LRH-2026-00354-SCR','slug':'ports-technology-campus','district_doc':'https://www.permits.performance.gov/sites/permits.dot.gov/files/2026-09/PORTS%20Technology%20Campus%20Executive%20Director%20Determination%209-28-2026.pdf'}}
ACTION={'Section 404 Clean Water Act':'section-404-clean-water-act','Section 10 Rivers and Harbors Act of 1899 and Section 404 Clean Water Act':'section-10-rivers-and-harbors-act-1899-and-section-404-clean-water-act','Section 106 Review':'section-106-review','Environmental Assessment (EA)':'environmental-assessment-ea','Endangered Species Act Consultation (DOI-FWS)':'endangered-species-act-consultation-doi-fws'}
def url(**p):return API+'?'+urlencode(p)
def fetch(n,u):
 return A.save(n,u,netfetch.get(u,timeout=30))
def reload():
 # Use the public, read-only full-data export; the publishing/import API requires credentials and is not used.
 fetch('metadata.json.gz',META);fetch('portfolio.html.gz',PORT)
 projects=json.loads(fetch('projects.json.gz',url(**{'$select':SELECT+ ',count(*) as row_count','$group':SELECT,'$order':'project_id,project_title','$limit':5000})));assert 0<len(projects)<5000
 total=json.loads(fetch('count.json.gz',url(**{'$select':'count(*) as n'})));assert sum(int(p['row_count']) for p in projects)==int(total[0]['n']),'Source changed during refresh'
 where=' OR '.join(f"upper({field}) like '%{v.upper()}%'" for field in ['project_title','project_sector','project_sector_type','action_description'] for v in PHRASES)
 found=json.loads(fetch('candidate-projects.json.gz',url(**{'$select':'project_id','$where':where,'$group':'project_id','$order':'project_id','$limit':5000})));ids={x['project_id'] for x in found}
 assert ids==set(PROJ),('New or missing candidate; validate sector and project before publishing',sorted(ids))
 for pid in sorted(ids):
  rows=json.loads(fetch(pid+'.json.gz',url(**{'$where':f"project_id='{pid}'",'$order':'unique_id','$limit':5000})));assert 0<len(rows)<5000
 A.seal()
def classify(r,cutoff,perm,no,app,obs):
 if r['dataset'] not in ['FAST-41 federal permitting milestones','FAST-41 timetable decisions']:return None
 if r['dataset']=='FAST-41 timetable decisions':return no('Director extended a timetable only; this is not an environmental finding or an issued construction authorization.','decision')
 d=r['details'] if isinstance(r['details'],dict) else json.loads(r['details']);return no('Agency-reported '+str(d['action_type'])+' milestone. Only an independent issued permit could count.','determination' if d['milestone_final'] else ('application' if 'Applicant Action' in r['kind'] else 'notice'))
def actual(row):
 raw=row.get('action_milestone_completion_actual');target=row.get('action_milestone_completion_target')
 if not raw:return None,'Target date only' if target else 'No actual completion date'
 dt=date.fromisoformat(raw[:10])
 if dt>CUT:return None,'Completion after cutoff'
 if str(row.get('action_milestone_complete')).strip().lower() not in ['true','yes','1','complete','completed']:
  return None,'Actual date lacks completed flag'
 if str(row.get('action_milestone_na','')).strip().lower() in ['true','yes','1']:return None,'Marked not applicable'
 return dt.isoformat(),None
def build():
 A.verify();catalog=json.loads(A.read('projects.json.gz'));found=json.loads(A.read('candidate-projects.json.gz'));assert {r['project_id'] for r in found}==set(PROJ);total=int(json.loads(A.read('count.json.gz'))[0]['n']);assert total==sum(int(r['row_count']) for r in catalog)
 counts=Counter();seen=set();held=[];out={};allacts=set();meta=json.loads(A.read('metadata.json.gz'));portfolio=plain(A.read('portfolio.html.gz').decode());assert all(t in portfolio for t in ['Portsmouth Data Center','QTS Richmond Technology Park'])
 for pid,p in PROJ.items():
  state=p['state'];rows=json.loads(A.read(pid+'.json.gz'));assert len(rows)==sum(int(r['row_count']) for r in catalog if r['project_id']==pid)
  assert sum(r.get('project_canonical') is True for r in rows)==1
  assert all(sum(r.get('action_canonical') is True for r in rows if r['action_id']==a)==1 for a in {r['action_id'] for r in rows})
  for r in rows:
   mid=r['milestone_id'];aid=r['action_id'];assert mid not in seen,(pid,mid);seen.add(mid);allacts.add(aid);kind=r['action_milestone_name'];action=r['action_type'];dt,why=actual(r)
   if why:held.append(dict(project=pid,action=aid,milestone=mid,type=kind,reason=why,target=r.get('action_milestone_completion_target'),actual=r.get('action_milestone_completion_actual')));continue
   is_final=str(r.get('action_milestone_final_milestone')).lower() in ('true','1');st=r.get('action_outcome') if is_final else None;st=' '.join((st or 'Completed').split());src=url(milestone_id=mid);act=BASE+'/proj/'+p['slug']+'/'+ACTION[action];agency=r['action_agency']
   details={'issuer':agency,'federal_issuer':{'US Army Corps of Engineers - Regulatory':'U.S. Army Corps of Engineers','Fish and Wildlife Service':'U.S. Fish and Wildlife Service'}.get(agency,agency),'county':p['county'],'action_id':aid,'action_type':action,'program':action,'action_status_snapshot':r['action_status'],'action_outcome_snapshot':r.get('action_outcome'),'milestone_final':is_final,'milestone_id':mid,'project_id':pid,'corps_file':p['file'],'corps_crosswalk':'Civil Works ORM DA identifier, project context only; does not turn consultations into permits.','government_project':r['project_url']['url'],'agency_action_page':act,'corroborating_public_document':p['district_doc'],'archive':'cache/history/fast/'+pid+'.json.gz','sha256':A.files[pid+'.json.gz']['sha256'],'observed_as_of':CUT.isoformat()}
   out.setdefault(state,[]).append(dict(id='fast-'+mid,state=state,dataset='FAST-41 federal permitting milestones',jurisdiction=p['county'],record_no=mid,project=r['project_title'],kind=kind,status=st,date=dt,date_role='Dashboard actual milestone completion date',url=src,source_url=act,locator=f'FAST-41 project {pid}; action {aid}; milestone {mid} (administrative ID, not a permit number)',details=details))
  counts[pid]=len(rows)
 # The separate executive director determination is neither the Army permit nor NEPA completion.
 source=D/'federal_dashboard_review.json';review=json.loads(source.read_text());p=PROJ['126036'];row=dict(id='fast-ports-extension-20260928',state='OH',dataset='FAST-41 timetable decisions',jurisdiction=p['county'],record_no='PORTS / 2026-09-28',project='PORTS Technology Campus',kind='Executive Director timetable extension',status='Granted',date='2026-09-28',date_role='Executive Director determination date',url=p['district_doc'],source_url=BASE+'/permitting-project/fast-41-covered-projects/ports-technology-campus',locator='Executive Director determination pp. 1–2, table 1; extension covers environmental assessment and Corps permit decision schedule',details={'issuer':'Federal Permitting Improvement Steering Council','federal_issuer':'Federal Permitting Improvement Steering Council','county':'Pike County','archive':'data/federal_dashboard_review.json','extract_sha256':lib.files.sha(source.read_bytes()),'evidence_excerpt':review['extension']['anchor'],'new_final_target':'2027-01-29','note':'Target date, not a completed decision.'});out['OH'].append(row)
 for st,v in out.items():lib.files.dump(series_path('fast_'+st.lower()),sorted(v,key=lambda x:x['id']))
 d=dict(source='Permitting Dashboard Full Dataset '+meta['id'],reported_rows=total,distinct_projects=len({r['project_id'] for r in catalog}),unique_project_groups=len(catalog),candidate_projects=sorted(PROJ),candidate_milestones=len(seen),candidate_actions=len(allacts),event_counts={s:len(v) for s,v in out.items()},held_count=len(held),regulator_confirmed_issued_permits=0,cutoff=CUT.isoformat(),snapshot_updated_epoch=meta['rowsUpdatedAt']);lib.files.dump(D/'federal_dashboard_holds.json',held);lib.files.dump(D/'federal_dashboard_validation.json',d);print(d)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:reload()
 build()
