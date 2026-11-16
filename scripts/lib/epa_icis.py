"""Rebuild per-state ICIS-NPDES slices from one EPA national archive. No external dependencies."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, io, gzip, json, zipfile, hashlib, re
from pathlib import Path
from urllib.request import urlopen
from collections import defaultdict
from datetime import datetime
from contextlib import ExitStack
from shutil import copyfileobj
from lib.paths import ROOT, CACHE
URL='https://echo.epa.gov/files/echodownloads/npdes_downloads.zip'
DICTIONARY='https://echo.epa.gov/tools/data-downloads/icis-npdes-download-summary'
STATES=('MS','LA')
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def split(path,states=STATES):
    meta={'url':URL,'sha256':digest(path),'members':{}}
    with zipfile.ZipFile(path) as z:
        for name,key in [('ICIS_FACILITIES.csv','NPDES_ID'),('ICIS_PERMITS.csv','EXTERNAL_PERMIT_NMBR')]:
            counts=defaultdict(int);member=z.getinfo(name)
            with ExitStack() as stack:
                raw=io.TextIOWrapper(stack.enter_context(z.open(member)),encoding='cp1252',errors='replace',newline='');rr=csv.DictReader((line.replace(chr(0),'') for line in raw))
                outs={}
                for st in states:
                    g=stack.enter_context(gzip.GzipFile(str(CACHE/st.lower()/f'epa-{name}.gz'),'wb',mtime=0));w=csv.DictWriter(stack.enter_context(io.TextIOWrapper(g,encoding='utf8',newline='')),rr.fieldnames);w.writeheader();outs[st]=w
                for r in rr:
                    st=r[key][:2]
                    if st in outs:outs[st].writerow(r);counts[st]+=1
            meta['members'][name]={'crc32':format(member.CRC,'08x'),'original_bytes':member.file_size,'state_rows':dict(counts)}
    for st in states:
        # Each state's metadata describes only that state, so the file is the same whichever states are split together.
        own={**meta,'members':{n:{**m,'state_rows':{st:m['state_rows'].get(st,0)}} for n,m in meta['members'].items()}}
        (CACHE/st.lower()/'epa-source.json').write_text(json.dumps(own,indent=2)+'\n')
def load(st,member):
    with gzip.open(CACHE/st.lower()/('epa-ICIS_'+member+'.csv.gz'),'rt') as f:return list(csv.DictReader(f))
def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--zip',type=Path);ap.add_argument('--download',action='store_true');ap.add_argument('--states',nargs='+',default=list(STATES),help='state slices to rewrite from the one national archive');a=ap.parse_args()
    if not a.zip:ap.error('Provide --zip PATH, optionally --download')
    if a.download:
        import lib.net as netfetch
        netfetch.download(URL,a.zip,timeout=240)
    split(a.zip,tuple(s.upper() for s in a.states))

def iso(raw):
    if not raw:return None
    return datetime.strptime(raw.strip(),'%m/%d/%Y').date().isoformat()
def state_rows(st, accept=None,cutoff='2026-11-15'):
    """Yield EPA facility-register permit versions, joined on exact NPDES ID; accept(fac,per) -> evidence URL or None.
    Default admission: explicit data center in facility or permit title. Versions are history, not distinct permits.
    The facility CITY field is an address locality, not proof of incorporation or issuing authority.
    """
    facilities=defaultdict(list)
    for r in load(st,'FACILITIES'):facilities[r['NPDES_ID']].append(r)
    with (ROOT/'data/jurisdictions.csv').open() as f:county={r['geoid']:r['name'] for r in csv.DictReader(f) if r['state']==st and r['layer']=='counties'}
    prefix=next(iter(county))[:2];manifest=json.loads((CACHE/st.lower()/'epa-source.json').read_text())
    for p in load(st,'PERMITS'):
        num=p['EXTERNAL_PERMIT_NMBR'];fac=facilities[num]
        if not fac or p['PERMIT_TYPE_CODE']=='UFT' or not p['ISSUE_DATE']:continue
        names=' '.join([p['PERMIT_NAME']]+[f['FACILITY_NAME'] for f in fac])
        if re.search(r'\bdata[\s-]*cent(?:er|re)s?\b',names,re.I):proof=DICTIONARY;basis='Explicit data center in facility or permit name'
        elif accept and (proof:=accept(fac[0],p)):basis='Reviewed named project or supporting work; corroborating source in identity_source'
        else:continue
        if len({(f['CITY'],f['COUNTY_CODE'],f['STATE_CODE']) for f in fac})!=1:raise ValueError('Ambiguous EPA facility location '+num)
        f=fac[0];c=f['COUNTY_CODE'];co=county.get(prefix+c[2:]) if c.startswith(st) else None
        if f['STATE_CODE']!=st or not co:raise ValueError('Invalid or absent EPA county '+num)
        day=iso(p['ISSUE_DATE'])
        if day>cutoff:continue
        kind='NPDES permit coverage' if p['PERMIT_TYPE_CODE']=='GPC' else 'NPDES discharge permit'
        city=f['CITY'].title();sha=manifest['sha256']
        yield dict(id=f"{st.lower()}-icis-{num}-{p['ACTIVITY_ID']}-{p['VERSION_NMBR']}",state=st,dataset='EPA ICIS-NPDES permit versions',jurisdiction=city or co,record_no=num,project=f['FACILITY_NAME'],kind=kind,status=p['PERMIT_STATUS_CODE'] or 'Not reported',date=day,date_role='EPA issue date',url=('https://echo.epa.gov/detailed-facility-report?fid='+f['FACILITY_UIN'] if f['FACILITY_UIN'].isdigit() else URL),source_url=URL,source_sha256=sha,locator=f"ICIS_PERMITS.csv EXTERNAL_PERMIT_NMBR={num}, ACTIVITY_ID={p['ACTIVITY_ID']}, VERSION_NMBR={p['VERSION_NMBR']}; ICIS_FACILITIES.csv NPDES_ID={num}",details=dict(county=co,epa_frs_id=f['FACILITY_UIN'] or None,source_locality=city,issuer=p['ISSUING_AGENCY'],identity_source=proof,identity_basis=basis,permit_name=p['PERMIT_NAME'],version=p['VERSION_NMBR'],activity_id=p['ACTIVITY_ID'],effective_date=iso(p['EFFECTIVE_DATE']),expiration_date=iso(p['EXPIRATION_DATE']),termination_date=iso(p['TERMINATION_DATE']),retirement_date=iso(p['RETIREMENT_DATE']),master_permit=p['MASTER_EXTERNAL_PERMIT_NMBR'],address=f['LOCATION_ADDRESS'],raw_status_code=p['PERMIT_STATUS_CODE'],dictionary=DICTIONARY))

if __name__=='__main__':main()
