"""Nebraska Department of Water, Energy, and Environment (DWEE) air files: public-record viewer documents (applications, draft and issued permits, public notices) for the data-center facilities."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT, CACHE
from lib.records import rec, CUT
from lib.files import unpack
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from collectors.nebraska.dwee_document_viewer import FACS,page as ecmlink,collect
from lib.epa_icis import digest
import json, re
import fitz
D=CACHE/'ne'
AIR='Nebraska DWEE facility air files'
def iso(v):return datetime.strptime(v.strip(),'%m/%d/%Y').date().isoformat() if v and v.strip() else None
def number(p):
 doc=fitz.open(p);t=' '.join(' '.join(doc[i].get_text().split()) for i in range(min(3,len(doc))))
 # Number must be on cover or explicit agency issuance letter; do not promote a mentioned predecessor.
 m=re.search(r'(?:PERMIT NUMBER:|Permit #)\s*((?:CP|OP)\d{2}(?:M\d+)?-\d+)',t)
 if m:return m[1], 'electronic cover'
 f=collector_data('nebraska','review.json')
 if f.exists():
    x=json.loads(f.read_text()).get(digest(p))
    if x:return x['permit_no'], x['method']
 return None,'Not verified on document'
def download():
 with ThreadPoolExecutor(max_workers=2) as t:list(t.map(collect,FACS))
def rows():
 rows=[];duplicates=0;seen=set();stats={};held=[]
 allowed={'DEQ Application','DEQ Draft Permit','DEQ Issued Permit','DEQ Public Notice'}
 for fid,(project,place) in FACS.items():
    path=D/('ecm-'+fid+'.json.gz');o=unpack(path);stats[fid]=len(o['rows'])
    for d in o['rows']:
        ds,st,descr,pid,program,fac=d['values'];dt=iso(ds)
        if st not in allowed and not (st=='DEQ Notification' and descr=='BEGIN CONSTRUCTION'):continue
        if dt>CUT:continue
        n,method=None,None;p=path
        if st=='DEQ Issued Permit':
            p=D/d['filename'];n,method=number(p)
            if not n and method.startswith('Cover is an applicant'):st='Applicant submittal (indexed as DEQ Issued Permit)'
            elif not n:held.append(dict(file=d['filename'],fid=fid,date=dt))
        sig=(fid,dt,st,descr,n or '',pid)
        if sig in seen:duplicates+=1;continue
        seen.add(sig);ref=n or 'FID '+fac+' / '+pid+' / '+st+' / '+descr+' / '+dt;kind='Air '+descr.lower();role='agency document date';source=ecmlink(fid)
        rows.append(rec('NE','dwee-'+fid+'-'+d['key'],AIR,ref,kind,st,dt,role,source,'AIR '+fid+'; '+st+' / '+descr+', '+ds+'; program '+pid+('; '+n if n else ''),project,('Springfield' if n in {'CP16-033','CP17-041','CP18-024','CP18-041'} else place),'Sarpy County',p,facility_id=fid,program_id=pid,record_number_is='verified agency permit number' if n else 'agency file locator; not a permit number',permit_number=n,verification=method,source_type=st,document_description=descr))
 return rows,stats,duplicates,held
