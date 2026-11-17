"""City of San Jose building permit registers (data.sanjoseca.gov CKAN resources, downloaded as full CSV files and filtered locally). Issuer: City of San Jose."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, io, json, re
from collections import defaultdict
import lib.net
from collectors.california.evidence_store import keep_archived
from collectors.california.evidence_store import MAN, cf, data, dt, counts, PATS, fetch_download
# CKAN /api/ and /datastore/ are disallowed by robots.txt, so each register's full CSV is downloaded from its allowed
# /dataset/<dataset>/resource/<resource>/download/ link (found on the dataset page), archived whole, and filtered here.
PORTAL='https://data.sanjoseca.gov/dataset/'
DOWNLOADS={'761b7ae8-3be1-4ad6-923d-c7af6404a904':'fd9ceb0c-75e0-402e-9fe3-3f6e04f2c23f/resource/761b7ae8-3be1-4ad6-923d-c7af6404a904/download/buildingpermitsactive.csv',
 'df4b8461-0c7a-4d16-b85d-ff7f71c5fed5':'3b40d486-bd19-44c5-b854-5f0638c2afc3/resource/df4b8461-0c7a-4d16-b85d-ff7f71c5fed5/download/buildingpermitsexpired.csv',
 '89ccdad9-7309-4826-a5f3-2fcf1fcb20fa':'ca355e55-c651-4e00-9bde-2c014f229486/resource/89ccdad9-7309-4826-a5f3-2fcf1fcb20fa/download/buildingpermitsunderinspection.csv'}
SEARCH=['FOLDERDESC','FOLDERNAME','WORKDESCRIPTION','SUBTYPEDESCRIPTION']
FIELDS=['_id','Status','STATUS','gx_location','FOLDERNUMBER','FOLDERDESC','FOLDERNAME','SUBTYPEDESCRIPTION','WORKDESCRIPTION','PERMITAPPROVALS','ISSUEDATE','FINALDATE','FOLDERRSN']
# the SQL ILIKE patterns ('%data%center%'): case-insensitive, % = any run of characters
LIKE=[re.compile('.*'.join(map(re.escape,p.strip('%').split('%'))),re.I|re.S) for p in PATS]
def matching(raw):
  """(rows scanned, matching rows) of a register CSV: same search fields and ILIKE patterns the datastore SQL used."""
  rd=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')));cols=rd.fieldnames;search=[x for x in SEARCH if x in cols];assert len(search)>=2 and 'FOLDERNUMBER' in cols and 'FOLDERRSN' in cols
  fields=[f for f in FIELDS if f in cols];scanned=0;out=[]
  for r in rd:
    scanned+=1
    if any(p.search(r[f] or '') for f in search for p in LIKE):out.append({f:(r[f] if r[f]!='' else None) for f in fields})
  return scanned,out
def sj(resource):
  n='sj-'+resource+'.csv.gz'
  try:raw=fetch_download(n,PORTAL+DOWNLOADS[resource])
  except lib.net.Refused as e:return keep_archived('sj-'+resource,e)
  scanned,found=matching(raw);counts['sj-'+resource]=len(found);counts['sj-'+resource+'-rows-scanned']=scanned
def download_tasks():return [lambda r=r:sj(r) for r in cf['san_jose']]
def counts_of(k):return json.loads(MAN.read_text())['candidate_counts'][k]
def rows(ctx):
 add=ctx.add;selected=ctx.selected;dups=ctx.dups;sjset=defaultdict(list)
 for res,scope in cf['san_jose'].items():
  k='sj-'+res;n=k+'.csv.gz';scanned,found=matching(data(n));assert (scanned,len(found))==(counts_of(k+'-rows-scanned'),counts_of(k)),n
  for a in found:
    no=a['FOLDERNUMBER']
    if selected(a,['FOLDERNAME','FOLDERDESC','WORKDESCRIPTION','SUBTYPEDESCRIPTION'],no,k):sjset[no].append((n,res,a))
 for no,members in sjset.items():
  ss={a['Status'] for _,_,a in members};assert len({(a['FOLDERRSN'],a['ISSUEDATE']) for _,_,a in members})==1
  if len(members)>1:dups['San Jose overlapping source rows']+=len(members)-1
  if not ss<={'Active','UnderInspection','Expired'} or ('Expired' in ss and len(ss)>1):raise ValueError((no,ss))
  n,res,a=sorted(members,key=lambda e:e[2]['Status']!='Active')[0];when=dt(a['ISSUEDATE']);detail={'issuer':'City of San José','issue_date':when,'final_date':dt(a['FINALDATE']),'source_statuses':sorted(ss),'address':a['gx_location'],'subtype':a['SUBTYPEDESCRIPTION'],'matched_resources':[x[1] for x in members],'folder_rsn':a['FOLDERRSN']}
  add('San José building permit registers','sj',n,no,a['FOLDERNAME'] or a['SUBTYPEDESCRIPTION'],a['WORKDESCRIPTION'] or a['FOLDERDESC'],a['Status'],when,'Permit issue date','San Jose',PORTAL+DOWNLOADS[res],'FOLDERNUMBER '+no,detail)
