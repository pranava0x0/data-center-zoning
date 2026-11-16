"""Baltimore City Department of Housing and Community Development (DHCD): issued building and use permits, from the
Open Baltimore construction-permit register (city GIS FeatureServer)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import sys, re, json
from lib.paths import ROOT, CACHE
from lib.records import rec
from lib.arcgis import snapshot as arc
from lib.terms import pred, EX
from lib.files import unpack
from lib.text import ms
from lib.net import query
D=CACHE/'md';B='https://baltegis.baltimorecity.gov/mapping/rest/services/Housing/DHCD_Open_Baltimore_Datasets/FeatureServer/3'
F=['OBJECTID','CaseNumber','Description','ExpirationDate','IssuedDate','Address','ExistingUse','ProposedUse','csm_projname','IsPermitModification','PermitName'];LOOK=['Description','csm_projname','ProposedUse','ExistingUse']
def download():arc(B,pred(LOOK),F,D/'baltimore.json.gz')
CITY='Baltimore DHCD issued building and use permits'
def rows():
 """Records plus the audit counts the validation file reports."""
 rows=[];p=D/'baltimore.json.gz';city=unpack(p);seen={}
 for r in city['rows']:
    n=r['CaseNumber'];proj=' '.join(str(r.get(k) or '') for k in LOOK)
    if not EX.search(proj):continue
    if n in seen and r!=seen[n]:raise ValueError('Conflicting Baltimore case '+n)
    if n in seen:continue
    seen[n]=r;modified=r['IsPermitModification'];pno=re.search(r'original permit\s*:\s*([a-z]{3}\d{4}-\d+)',proj,re.I)
    if modified and not pno:raise ValueError('Modification without original number: '+n)
    start=ms(r['IssuedDate']);url=query(B+'/query',where="CaseNumber='"+n+"'",outFields=','.join(F),returnGeometry='false',f='pjson')
    rows.append(rec('MD','balt-'+n,CITY,n,'Building or use permit / '+('amendment' if modified else 'original'),'Issued',start,'issue date',url,'CaseNumber '+n+', IsPermitModification '+str(modified),r.get('Description') or r.get('PermitName'),'Baltimore','Baltimore city',p,base_permit=pno[1].upper() if modified else n,expiry=ms(r['ExpirationDate']),is_modification=modified,address=r['Address'],project_phase='data center decommissioning/consolidation' if n=='COM2023-02318' else 'data center-related work'))
 return rows,dict(baltimore_candidates=city['count'])
