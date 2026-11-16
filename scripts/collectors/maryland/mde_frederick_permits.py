"""Maryland Department of the Environment (MDE): Frederick-area data-center permit and approval documents (air permits to
construct, water appropriation permits, land restoration decisions, construction stormwater letters), read from the PDFs
linked on MDE's Frederick data-center page and checked against data/history/maryland/review.json."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT, CACHE
import sys, re, json, html, fitz
from urllib.parse import urljoin
from lib.records import rec
from lib.epa_icis import digest
from lib.net import get_simple as get
D=CACHE/'md';M='https://mde.maryland.gov/datacenters/Pages/FrederickDataCenter.aspx'
def download():
 D.mkdir(exist_ok=True,parents=True);p=D/'mde.html';p.write_bytes(get(M));pairs={}
 for href,label in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',p.read_text(),re.S|re.I):
    t=' '.join(html.unescape(re.sub('<[^>]*>',' ',label)).split()).strip('​')
    if any(s in t for s in ['final air permit','Permit Water Appropriation','management plan approval','rescinding approval','general permit for stormwater discharges letter']):pairs[t]=urljoin(M,html.unescape(href))
 for i,(t,u) in enumerate(pairs.items()):(D/('action-'+str(i)+'.pdf')).write_bytes(get(u))
 (D/'links.json').write_text(json.dumps(list(pairs.items()),indent=2))
AIR='Maryland MDE Frederick campus air permits';WATER='Maryland MDE Frederick water appropriation and use permits';BIO='Maryland MDE Frederick land restoration decisions';STORM='Maryland MDE Frederick construction stormwater letters'
def rows():
 """Records plus the audit counts the validation file reports."""
 rows=[]
 checks=json.loads((collector_data('maryland','review.json')).read_text());links=json.loads((D/'links.json').read_text());scope=list(checks)
 for i,(label,u) in enumerate(links):
    if label not in checks or checks[label]['url']!=u:raise ValueError('New state document needs review')
    p=D/('action-'+str(i)+'.pdf')
    if digest(p)!=checks[label]['sha256']:raise ValueError('Recheck source PDF against cover and dated action')
    def add(key,ds,n,kind,status,dt,role,site,place,loc,**extra):
        rows.append(rec('MD','mde-'+key,ds,n,kind,status,dt,role,u,loc,site,place,'Frederick County',p,issuer='Maryland Department of the Environment',**extra))
    if 'final air permit' in label:
        aws=label.startswith('Amazon');n='B-08076' if aws else 'B-07819';dt='2026-03-25' if aws else '2025-01-30'
        add(n,AIR,n,'Air permit to construct','Construction Permit',dt,'signed issue date',label.rsplit(' final',1)[0],'Frederick','Signed premises-wide permit cover and registered installation table pp. 2–3 (printed numbering).',premises='021-0809' if aws else '021-0805',identification='Control number; equipment registration numbers are subordinate.')
    elif 'Appropriation' in label:
        n=re.search(r'FR\d{4}[GS]\d{3}\(\d+\)',label)[0]
        dt,exp,site,place,avg,purpose={'FR2025G001(01)':('2025-07-15','2028-06-30','Turner Construction Company','Frederick',6000,'Groundwater dewatering for stormwater utility installation'), 'FR2023G001(03)':('2025-11-21','2028-10-31','Quantum Maryland LLC','Adamstown',35000,'Groundwater dewatering for installation of stormwater and other utilities'), 'FR2024S001(01)':('2024-10-28','2026-09-30','Quantum Maryland LLC','Adamstown',9100,'Surface water dewatering for stormwater management ponds')}[n]
        add(n,WATER,n,'Water appropriation and use permit','Authorized',dt,'permit effective date',site,place,'Permit face, effective/expiration dates; allocation, purpose, source and location conditions 1–4.',printed_expiration=exp,annual_average_gpd=avg,water_use=purpose)
    elif 'management plan approval' in label:add('rowan',BIO,'MD2196 / Bauxite 2 EMP','Environmental management plan','approves','2025-03-18','approval letter date','Rowan Frederick II data center','Frederick','Land Restoration Program letter p. 1; construction of temporary distribution line and ducts.')
    elif 'rescinding' in label:
        add('emp-approve',BIO,'Eastalco phase I utility EMP','Environmental management plan','approval','2023-03-16','prior approval cited in later letter','Quantum Maryland','Frederick','May 25 withdrawal letter p. 1, paragraph 1 cites prior approval.')
        add('emp-withdraw',BIO,'Eastalco phase I utility EMP','Environmental management plan','withdrawing our approval','2023-05-25','withdrawal letter date','Quantum Maryland','Frederick','Land Restoration Program withdrawal letter p. 1.')
    elif 'stormwater' in label:
        doc=fitz.open(p);s=' '.join(doc[3].get_text().split());matches=re.findall(r'(?:^|\s)(\d{1,2})\.\s+((?:20CP|MDRC)[A-Z0-9]+)(?:\s+\((20CP[A-Z0-9]+)\))?\s+([^\n]+?)(?=\s+\d{1,2}\.\s|$)',s)
        if [int(r[0]) for r in matches]!=list(range(1,21)):raise ValueError('MDE 20-NOI appendix schema changed')
        for item,n,alias,site in matches:
            site=re.sub(r'(?:14GP-20CP Continuations|Pending 20CP Authorizations).*','',site).strip()
            add('storm-'+item,STORM,n,'Construction stormwater / regulator correspondence','Action required','2023-11-09','agency letter date',site,'Frederick County','Nov. 9 letter, appendix p. 4, item '+item,alternative_20cp=alias,appendix_group='20CP authorization' if item=='1' else '14GP-20CP continuations' if int(item)<=8 else 'pending 20CP authorizations',action_is='Request for action on NOI; not new issuance.')
    else:raise ValueError(label)
 return rows,dict(verified_file_count=len(checks))
