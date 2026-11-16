"""City and County of Honolulu historical building permit registry (data.honolulu.gov 4vab-c87q), screened for data
centers. Issuer: Honolulu Department of Planning and Permitting."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import json, re
from urllib.parse import urlencode
U='https://data.honolulu.gov/resource/4vab-c87q.json'
def params():
 cs=['applicant','proposeduse','otherwork','joblocation','ownershipassessed'];where=' OR '.join(f"lower({c}) like '{p}'" for c in cs for p in ['%data center%','%datacenter%','%data centre%','%server farm%','%drfortress%','%dr fortress%']);fields='buildingpermitno,buildingpermittype,issuedate,completeddate,createddate,statusdescription,coissued,finalcoissued,applicant,ownershipassessed,jobaddress,joblocation,proposeduse,otherwork,objectid,tmk,externalfilenum'
 return {'$select':fields,'$where':where,'$limit':5000,'$order':'objectid'}
def download(A):
 p=params();b=A.fetch('honolulu.json.gz',U+'?'+urlencode(p));assert len(json.loads(b))<5000
def rows(A):
 o=[];data=json.loads(A.read('honolulu.json.gz'));assert len(data)<5000;assert len({a['objectid'] for a in data})==len(data)
 for a in data:
  date=lambda f:(a.get(f) or '')[:10] or None
  issued=date('issuedate');num=a.get('buildingpermitno') or a['externalfilenum'];project=' — '.join(dict.fromkeys(x for x in [a.get('joblocation'),a.get('proposeduse')] if x));assert lib.terms.MATCH.search(project) or re.search(r'dr\s*fortress',a.get('applicant',''),re.I)
  o.append(dict(id='hi-hnl-'+num,state='HI',dataset='Honolulu historical building permits',jurisdiction='Honolulu',record_no=num,project=project,kind='Building permit' if issued else 'Building permit application',status=a['statusdescription'],date=issued or date('createddate'),date_role='Building permit issue date' if issued else 'Application created date',url=U+'?objectid='+str(a['objectid']),source_url='https://data.honolulu.gov/d/4vab-c87q',locator='Registry OBJECTID '+str(a['objectid'])+'; '+a['externalfilenum'],details=dict(issuer='City and County of Honolulu',county='Honolulu County',archive='cache/history/hi/honolulu.json.gz',archive_sha256=A.files['honolulu.json.gz']['sha256'],issue_date=issued,completed_date=date('completeddate'),application=a['externalfilenum'],co_issued=a.get('coissued'),final_co_issued=a.get('finalcoissued'),tax_map_key=a.get('tmk'),snapshot_scope='Historical city series through 2025-06-30; status as supplied, no later update inferred.')))
 return o
