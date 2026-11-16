"""Iowa Department of Natural Resources air construction permit search (idnraqrr.iowadnr.gov ConPermitSearch): equipment permit
versions for each data center plant in the state facility roster."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.text import strip, tr
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs,urlsplit
import re, html, gzip, json, hashlib
from lib.net import get_simple as get
from lib.paths import CACHE
from lib.records import CUT, rec
from collectors.iowa.dnr_title_v_permits import ATT
D=CACHE/'ia';BASE='https://idnraqrr.iowadnr.gov/ConPermitSearch/';ROSTER=BASE+'ByConstructionPermitPlantNameView'
PLANT=BASE+'ConstructionPermit?id='
ALIAS={'543':'https://www.councilbluffs-ia.gov/DocumentCenter/View/9195','8721':'https://www.cyrusone.com/data-centers/north-america/council-bluffs-ia','11381':ATT.format(2908)}
REG='Iowa DNR air construction equipment permit history'
def read(p):return gzip.decompress(p.read_bytes()).decode('utf-8-sig')
def pack(p,u):p.write_bytes(gzip.compress(get(u),mtime=0))
def selection(s):
    fs={};total=0
    for r in tr(s):
        k=re.search('data-selectclick="(\d+)"',r)
        if not k:continue
        total+=1;v=[strip(x) for x in re.findall(r'<td\b[^>]*>(.*?)</td>',r,re.S|re.I)]
        if len(v)!=4:raise ValueError(v)
        if re.search(r'data[ -]?cent(?:er|re)|server[ -]?farm',v[1],re.I) or k[1] in ALIAS:fs[k[1]]=v[1:]
    if not set(ALIAS)<=set(fs) or not total:raise ValueError('State registry missing expected aliases')
    return total,fs
def download():
    D.mkdir(parents=True,exist_ok=True);p=D/'state-facilities.html.gz';pack(p,ROSTER);_,fs=selection(read(p))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda i:pack(D/('plant-'+i+'.html.gz'),PLANT+i),sorted(fs)))
def rows():
    """Records, the plant identity map the Title V permits join to, and the audit counts the validation file reports."""
    total,fs=selection(read(D/'state-facilities.html.gz'));rows=[];counts={};used=set();duplicates=0;names={};baseids=set();rawrows=0
    for id,(name,place,facility) in sorted(fs.items()):
        p=D/('plant-'+id+'.html.gz');page=read(p);header=strip(page[page.index('plantHeader'):page.index('plantHeader')+1700]);g=re.search('County Name: (.*?) City Name: (.*?) Plant Name: (.*?) Plant Number: ([0-9-]+)',header)
        if not g or g[4]!=facility or name.casefold()!=g[3].casefold() or place.casefold()!=g[2].casefold():raise ValueError((facility,header))
        county=g[1].title()+' County';place=g[2].title();name=g[3];names[id]=(name,place,county,facility);counts[facility]=0
        for z in tr(page):
            if 'id="permitNumber"' not in z:continue
            rawrows+=1;counts[facility]+=1
            _,n,pr,ep,equipment,ds=[strip(x) for x in re.findall(r'<td\b[^>]*>(.*?)</td>',z,re.S|re.I)]
            href=html.unescape(re.search('href="([^"]+)"',z)[1]);j=json.loads(parse_qs(urlsplit(href).query)['dataString'][0]);dt=datetime.strptime(ds,'%m/%d/%Y').date().isoformat()
            if j['permitNumber'].strip()!=n or j['issueDate'][:10]!=dt or j['facilityNumber']!=facility:raise ValueError((n,dt,facility,j))
            if dt>CUT:continue
            base=re.fullmatch(r'(\d{2,4}-A-\d+)(?:-S\d*)?(?:-R)?',n)
            if not base:raise ValueError('Unreviewed permit version '+n)
            resc=pr.casefold()=='rescinded'; status='Rescinded' if resc else 'Date Issued';baseids.add((facility,base[1]))
            fingerprint=(facility,n,pr,ep,equipment,dt);key=hashlib.sha256(json.dumps(fingerprint).encode()).hexdigest()[:16]
            if fingerprint in used:duplicates+=1;continue
            used.add(fingerprint)
            row=rec('IA','eq-'+id+'-'+key,REG,n,'Air construction permit / equipment',status,dt,'register Date Issued on rescission row' if resc else 'permit issue date',PLANT+id,'Plant '+facility+'; permit '+n+'; '+ep+'; Date Issued '+ds,name,place,county,p,plant_number=facility,base_permit=base[1],project_number=pr,emission_point=ep,equipment=equipment,document_name=j.get('fileName'),register_rescission_date=j.get('rescissionDate'))
            rows.append(row)
    return rows,names,dict(state_plant_roster=total,selected_plants=len(fs),construction_plant_source_rows=counts,construction_source_rows=rawrows,identical_printed_rows_collapsed=duplicates,distinct_equipment_permit_families=len(baseids))
