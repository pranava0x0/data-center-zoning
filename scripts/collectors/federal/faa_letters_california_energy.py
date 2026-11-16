"""Replay direct FAA letter decisions docketed in California; no permit status inferred."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import lib.net as netfetch
from urllib.request import Request,urlopen
import argparse, re, json
from datetime import datetime
import lib.discovery as c
R=c.R;C=R/'cache/history/faaletters';CFG=R/'data/national/federal_aviation_letters.json';IDX=C/'manifest.json';OUT=series_path('faaletters_ca')
def fetch():
    cfg=c.read(CFG,{});ix={};C.mkdir(parents=True,exist_ok=True)
    for tn,(docid,docket,project) in cfg.items():
        url=f'https://efiling.energy.ca.gov/GetDocument.aspx?DocumentContentId={docid}&tn={tn}'
        raw=netfetch.get(url,timeout=30,limit=c.LIMIT)
        assert raw.startswith(b'%PDF') and len(raw)<=c.LIMIT
        h=c.digest(raw);(C/(h+'.pdf')).write_bytes(raw)
        import fitz
        with fitz.open(stream=raw,filetype='pdf') as pdf:pages=[p.get_text('text') for p in pdf]
        tb=json.dumps(pages,ensure_ascii=False).encode();(C/(h+'.json')).write_bytes(tb);ix[tn]=dict(sha256=h,bytes=len(raw),pages=len(pages),pages_sha256=c.digest(tb),url=url,captured=c.now());print(tn,len(pages),flush=True)
    c.dump(IDX,ix)

AUDIT=R/'data/national/federal_aviation_letters_audit.json'

def field(pattern,text):
    found=re.search(pattern,text,re.M)
    if not found: raise ValueError('Required FAA evidence absent: '+pattern)
    return found.group(1).strip()

def iso(s):
    return datetime.strptime(s,'%m/%d/%Y').date().isoformat()

def key(r):
    return r['record_no'].strip().upper(),r['status'].strip().lower(),r['date']

def parse(tn,config,meta,pages):
    docid,docket,project=config
    cover=pages[0]
    if not (field(r'^Docket Number:\s*(.+)$',cover)==docket and field(r'^Project Title:\s*(.+)$',cover)==project and field(r'^TN #:\s*(\d+)',cover)==tn):
        raise ValueError('Docket cover mismatch for '+tn)
    rows=[]; claimed=set()
    for i,s in enumerate(pages):
        if not ('Aeronautical Study No.' in s and 'Federal Aviation Administration' in s and re.search(r'Page 1 of \d+',s)):continue
        start=i+1; n=int(field(r'Page 1 of (\d+)',s)); end=i+n
        if end>len(pages) or claimed.intersection(range(start,end+1)):raise ValueError('Letter pagination mismatch')
        claimed.update(range(start,end+1))
        asn=field(r'Aeronautical Study No\.\s*(\d{4}-[A-Z]{3}-\d+-OE)\b',s)
        date=iso(field(r'^Issued Date:\s*(\d+/\d+/\d{4})',s))
        title=field(r'^\*\*\s*([^*\n]+)\s*\*\*',s)
        if title=='DETERMINATION OF NO HAZARD TO AIR NAVIGATION': status='No Hazard'
        elif title=='Extension' and 'is hereby extended' in s:status='Extension'
        else:raise ValueError('Unreviewed action: '+title)
        structure=field(r'^Structure:\s*([^\n]+)',s)
        city=field(r'^Location:\s*([^,\n]+),\s*CA\b',s)
        body='\n'.join(pages[i:end])
        sig=field(r'Signature Control No:\s*([\d-]+)',body)
        details=dict(federal_issuer='Federal Aviation Administration',docket_publisher='California Energy Commission',docket_number=docket,transaction_number=tn,signature_control_number=sig,letter_title=title,original_structure_type=structure,structure_city_as_reported=city,scope='Airspace review of the named structure; no construction or operating permit. Docket sponsor may differ from FAA issuer.',docketed_date=iso(field(r'^Docketed Date:\s*(\d+/\d+/\d{4})',cover)))
        if status=='Extension':
            details['conditional_expiry_as_stated']=iso(field(r'will expire on (\d+/\d+/\d{4})',s))
        rows.append(dict(id=f'fed-faa-letter-{asn.lower()}-{status.lower().replace(" ","-")}-{date}',state='CA',dataset='FAA airspace determinations',jurisdiction=city,record_no=asn,project=project,kind='Airspace review of proposed structure',status=status,date=date,date_role='FAA signed letter issue date',url=meta['url']+'#page='+str(start),source_url=meta['url'],source_sha256=meta['sha256'],locator=f'CEC {docket} TN {tn}, PDF pp. {start}–{end}; FAA study {asn}, Signed letter, {structure}',details=details))
    return rows, sorted(set(range(1,len(pages)+1))-claimed)

def run():
    bulk=series_path('faa_ca')
    if not bulk.is_file():raise FileNotFoundError('Build the FAA bulk California output first: '+str(bulk))
    bulkkeys={key(r) for r in c.read(bulk,[])};published=set();rows=[];log={}
    index=c.read(IDX,{});cfg=c.read(CFG,{})
    if set(index)!=set(cfg):raise ValueError('Capture/config mismatch')
    for tn,config in cfg.items():
        m=index[tn];h=m['sha256'];pdf=(C/(h+'.pdf')).read_bytes();b=(C/(h+'.json')).read_bytes()
        if not(c.digest(pdf)==h and c.digest(b)==m['pages_sha256']):raise ValueError('Source hash mismatch: '+tn)
        pages=json.loads(b)
        if len(pages)!=m['pages']:raise ValueError('Page count mismatch')
        candidates,uncounted=parse(tn,config,m,pages)
        if not candidates:raise ValueError('No letters recovered: '+tn)
        dropped=[]; kept=0
        for r in candidates:
            k=key(r)
            if k in bulkkeys or k in published:
                dropped.append(dict(key=list(k),reason='FAA bulk' if k in bulkkeys else 'docket duplicate'));continue
            published.add(k);rows.append(r);kept+=1
        log[tn]=dict(signed_letters=len(candidates),retained=kept,duplicates=dropped,nonletter_pages=uncounted)
    rows.sort(key=lambda r:(r['date'],r['record_no']))
    c.dump(OUT,rows);c.dump(AUDIT,log)
    print('Signed FAA letters: '+str(sum(x['signed_letters'] for x in log.values()))+'; newly published '+str(len(rows)))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--refresh',action='store_true');args=ap.parse_args()
    if args.refresh:fetch()
    run()
