"""Utah Department of Environmental Quality, Division of Air Quality (DAQ): Approval Orders (issued and out for public
comment) and current Notice of Intent applications, from DAQ's public permitting registers (see daq_submissions.py for the
register download) and the approval-order PDFs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import sys, re, json, fitz
from lib.paths import CACHE, ROOT
from lib.terms import EX
from lib.files import unpack
from lib.net import get_simple as get
from lib.records import rec
from collectors.utah.daq_submissions import BASE,PAGES,getpage
from concurrent.futures import ThreadPoolExecutor
D=CACHE/'ut'
def hit(r):return bool(EX.search(' '.join(str(r.get(k) or '') for k in ['masterAiName','masterOrgName','comments'])))
def doclink(num):return BASE+'DocViewer?IntDocID='+str(num)+'&contentType=application%2Fpdf'
def download():
    D.mkdir(exist_ok=True,parents=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(getpage,PAGES))
    ids={r['intDocID'] for pg in ['AOsIssuedAll','AOsOutForCmt'] for r in unpack(D/(pg+'.json.gz'))['rows'] if hit(r)}
    def fetch(i):
        p=D/('air-'+str(i)+'.pdf');p.write_bytes(get(doclink(i)))
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(fetch,ids))
from datetime import datetime
from lib.epa_icis import digest
def rows():
    """Records plus the per-register row counts the validation file reports."""
    rows=[];qc={}
    for pg in PAGES:
        f=D/(pg+'.json.gz');arr=unpack(f)['rows'];qc[pg]=len(arr)
        for r in arr:
            if not hit(r):continue
            facility=r['masterAiName'].split('(Site ID:')[0].strip();loc=r['physicalAddressMunicipality'].strip(' ,') or r['county']+' County';county=r['county']+' County';id=str(r.get('intDocID') or r.get('masterAiId'));u=doclink(id) if pg!='NOI_Pub_H' else BASE+pg;p=f
            if id=='164894':continue # misleading site name; underlying Uinta Wax order modifies gas-processing dehydrators
            site=re.search(r'Site ID:\s*(\d+)',r['masterAiName']);site=site[1] if site else str(r.get('masterAiId') or '')
            if pg=='NOI_Pub_H':
                day=r['completedDate'];n='site '+site+' / '+day;st='Listed current application';role='register completedDate (application workflow)';kind='Air permit application'
                locator='NOI current applications / site '+site+'; application workflow date is not issuance or decision.'
            elif pg in ('AOsIssuedAll','AOsOutForCmt'):
                p=D/('air-'+id+'.pdf');t=' '.join(fitz.open(p)[0].get_text().split())
                ref=re.search(r'DAQE-[AI]N\d{9}-\d{2}',t)
                if ref:n=ref[0]
                elif id=='155764' and digest(p)=='1507a4175829e337639c91684555497c9dabd89453c227a7e6f48d6fc1529ed2':n='DAQE-AN162380001-25'
                else:raise ValueError('No verified UT approval order number '+id)
                st='Approval Order issued' if pg=='AOsIssuedAll' else 'Intent to Approve';day=r['aoIssuedDate'] or r['aoOutForPublicCommentStartDate'];role='approval order issue date' if pg=='AOsIssuedAll' else 'public comment period opens';kind='Air quality approval order' if pg=='AOsIssuedAll' else 'Draft air approval order';locator='DAQ doc '+id+', cover and '+pg+' table; '+n
                md=re.search(r'NOI\) received on ([A-Za-z]+ \d{1,2}, \d{4})',t)
                prev=datetime.strptime(md[1],'%B %d, %Y').date().isoformat() if md else '2024-11-07' if id=='155764' else None
                if prev and pg=='AOsIssuedAll':
                    rows.append(rec('UT','air-recv-'+id,'Utah DAQ notice receipts cited in approval orders',n,'Air permit application','Notice of Intent received',prev,'application received',u,'Cover p. 1, Notice of Intent received for project',facility,loc,county,p,site_id=site,issuer='Utah Division of Air Quality'))
            else:raise ValueError('New operating-permit match requires schema review '+pg)
            rows.append(rec('UT','air-'+pg+'-'+id,'Utah DAQ '+pg,n,kind,st,day,role,u,locator,facility,loc,county,p,issuer='Utah Division of Air Quality',site_id=site,register_url=BASE+pg,document_id=id if pg!='NOI_Pub_H' else None,scope='May cover dedicated power or equipment at the named site; order issuance is not campus land-use approval.'))
    return rows,qc
