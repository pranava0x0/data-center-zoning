"""Pennsylvania DEP’s published data-center project and authorization tables. Offline by default.
Single source, so not split: Pennsylvania Department of Environmental Protection data center permit tracker."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import csv, io, re, argparse, datetime as dt, collections
import lib.discovery as c
from lib.url_archive import Archive,place_rank
ROOT='https://gis.dep.pa.gov/DataCenterPermitTracker/'
PROJECT=ROOT+'static/DataCenterProjectTrackingAllProjects.csv';PERMIT=ROOT+'static/DataCenterPermitTracking.csv'
def run(fetch):
 a=Archive('pa',fetch,owner='pennsylvania')
 config=a.json(ROOT+'globalConfigs/config.json')
 if not all(x in str(config) for x in ('/static/DataCenterProjectTrackingAllProjects.csv','/static/DataCenterPermitTracking.csv')):raise ValueError('DEP portal changed dataset')
 def rows(u):return list(csv.DictReader(io.StringIO(a.get(u)[0].decode('utf-8-sig'))))
 projects=rows(PROJECT);events=rows(PERMIT);by={r['ProjectID']:r for r in projects};h=a.get(PERMIT)[1];found=[];held=[]
 if len(by)!=len(projects):raise ValueError('Duplicate project ID')
 for r in events:
  p=by[r['ProjectID']];cat=r['AuthorizationCategory'].strip();typ=r['AuthorizationType'].strip();status=r['Status'];no=r['PermitNumber'].strip()
  if status=='Not Yet Submitted' or cat=='U.S. Fish & Wildlife Service':
   held.append((r['ProjectID'],cat,typ,status));continue
  if p['ProjectType']!='Data Center' or status not in ('Issued','Pending','Withdrawn','Returned','Received'):raise ValueError('Unknown project/status')
  try:day=dt.datetime.strptime(r['Submitted'],'%m/%d/%y').date().isoformat() if r['Submitted'] else None
  except ValueError:
   day=dt.datetime.strptime(r['Submitted'],'%m/%d/%Y').date().isoformat()
  if day and day>'2026-11-15':continue
  co=p['County'].strip();place=p['Municipality'].strip()
  county=(co+' County') if co and '/' not in co else ''
  if '/' in place:place=county or 'Multiple municipalities'
  key='|'.join([p['ProjectID'],cat,typ,status,no,r['eFactsAuthID'],r['Submitted'],r['ApplicationType']])
  rec=dict(id='pa-dep-'+c.digest(key.encode())[:17],state='PA',dataset='Pennsylvania DEP data center permit tracker',jurisdiction=place or county or 'Pennsylvania',county=county,record_no=no,project=p['ProjectName'],kind=cat+' · '+typ,status=status,date=day,date_role='Application submitted' if day else 'Submission date not reported',url=PERMIT,source_url=PERMIT,source_sha256=h,locator=f"DataCenterPermitTracking.csv · project {p['ProjectID']} · {r['eFactsAuthID'] or no or typ}",details=dict(agency_project_id=p['ProjectID'],efacts_authorization_id=r['eFactsAuthID'],application_type=r['ApplicationType'],authorization=typ,program=cat,source_municipality=p['Municipality'],source_county=p['County'],project_table=PROJECT,project_table_sha256=a.get(PROJECT)[1],tracker=ROOT))
  found.append(rec)
 seen=set();distinct=[]
 for r in found:
  if r['id'] in seen:raise ValueError('Duplicate agency event '+r['locator'])
  distinct.append(r);seen.add(r['id'])
 c.dump(series_path('pa'),distinct);c.dump(collector_data('pennsylvania','audit.json'),dict(projects=len(projects),raw=len(events),published=len(distinct),held=collections.Counter(x[3] for x in held),gov_source=ROOT,counties_in_permit_table=collections.Counter(r['county'] for r in distinct)))
 c.dump(collector_data('pennsylvania','rank.json'),place_rank(a,'PA','42'));print(len(distinct),'Pennsylvania DEP records')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
