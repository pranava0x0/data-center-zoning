"""Find government-hosted land-use texts from linked municipal pages; search within pinned PDFs.
A hit in a definition, table, revision notice or agenda is a lead only. Offline by default.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections, csv, gzip, hashlib, io, json, re, os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin,urlsplit,urldefrag
from urllib.request import Request,urlopen
import fitz
import lib.discovery as c
from ordinances.discovery.screen_local_sites import LOG,BASE,h,LOCK,HOST
D=c.R/'data/national';C=c.R/'cache/codebooks';FILES=C/'files';JOBS=C/'checks'
LAND=re.compile(r'zoning (?:ordinance|code|regulations|bylaw)|land (?:use|development) (?:ordinance|code|regulations)|uniform development code|unified (?:development|zoning) (?:ordinance|code)|municipal code|ordinance book|development standards',re.I)
DOC=re.compile(r'\.pdf\b|/(?:DocumentCenter|showpublisheddocument|ArchiveCenter|wp-content/uploads|download|ViewFile|vertical/sites)/',re.I)
EXCLUDE=re.compile(r'comprehensive plan|annual report|minutes|\bmap\b|job posting|press release|\bagenda\b|form|contact us|application fee',re.I)
DC=re.compile(r'\b(?:data[\s‐‑–-]*cent(?:er|re)s?|server farms?|hyperscale (?:computing|facilit)|computer (?:server|processing) facilit(?:y|ies))\b',re.I)
def read(p):
 with p.open() as f:return list(csv.DictReader(f))
def directory():
 geos=read(c.OUT/'national_jurisdiction_checks.csv');prior={x['state']:int(x['count_rank'] or 999) for x in read(D/'priority.csv')};hot={x['geoid']:int(x['markers']) for x in read(D/'hotspots.csv') if x['geoid']};book={};cached={}
 for g in geos:
    u=g['url']
    if not u or not int(g['pages'] or 0):continue
    visit=c.read(LOG/(h(u.encode())+'.json'),{});host=(urlsplit(u).hostname or '').removeprefix('www.')
    for p in visit.get('pages',[]):
        sha=p['sha256']
        if sha not in cached:
            entries=[]
            path=BASE/(sha+'.gz')
            if path.exists():
                b=gzip.decompress(path.read_bytes())
                if b[:4]==b'%PDF':pairs=[(p['url'],p['url'].split('/')[-1])]
                elif re.search(rb'zoning|unified.development|municipal.code|development.code|land.use|development.standards',b,re.I):
                    pairs=c.parse(b,'text/html',p['url'])[2]
                else:pairs=[]
                for href,t in pairs:
                    href=urldefrag(urljoin(p['url'],href))[0];tag=re.sub('[-_+]+',' ',href.rsplit('/',1)[-1]+' '+t)
                    if href.startswith(('https://','http://')) and DOC.search(href) and LAND.search(tag) and not EXCLUDE.search(tag):
                        entries.append((href,t[:150]))
            cached[sha]=entries
        for href,label in cached[sha]:
            dest=(urlsplit(href).hostname or '').removeprefix('www.')
            if dest!=host and not dest.endswith('.gov') and dest!=(urlsplit(p['url']).hostname or '').removeprefix('www.'):continue
            k=(g['geoid'],href)
            book[k]=dict(state=g['state'],geoid=g['geoid'],jurisdiction=g['name'],url=href,label=label,referral=p['url'],referral_sha256=sha,markers=hot.get(g['geoid'],0),state_rank=prior[g['state']])
 rows=sorted(book.values(),key=lambda r:(r['state_rank'],-r['markers'],r['jurisdiction'],r['url']))
 with (D/'codebooks.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(len(rows),'land use/code document referrals for',len({r['geoid'] for r in rows}),'jurisdictions',flush=True)
def check(u):
 key=c.digest(u.encode());p=JOBS/(key+'.json');host=urlsplit(u).hostname
 if p.exists():return
 try:
    import threading
    with LOCK:lock=HOST.setdefault(host,threading.Lock())
    with lock:
        c.policy(u)
        with urlopen(Request(u,headers={'User-Agent':c.AGENT}),timeout=15) as z:
            b=z.read(18*1024*1024+1);final=z.url
    if len(b)>18*1024*1024:raise ValueError('Source over 18 MiB; needs individual review')
    if b[:4]!=b'%PDF':raise ValueError('Not PDF; separate adapter required')
    sha=c.digest(b);pdf=fitz.open(stream=b,filetype='pdf');hits=[];readable=0
    for num,page in enumerate(pdf,1):
        txt=' '.join(page.get_text().split());readable+=len(txt)>80
        for m in list(DC.finditer(txt))[:10]:
            if len(hits)<140:hits.append([num,txt[max(0,m.start()-90):m.end()+125]])
    (FILES/(sha+'.pdf')).write_bytes(b);record=dict(url=u,resolved=final,sha256=sha,pages=len(pdf),text_pages=readable,hits=hits,checked=c.now())
 except Exception as e:record=dict(url=u,error=str(e)[:120],checked=c.now())
 c.dump(p,record)
def run(fetch,limit,workers):
 rows=read(D/'codebooks.csv');urls=list(dict.fromkeys(r['url'] for r in rows))
 if fetch:
    FILES.mkdir(exist_ok=True,parents=True);JOBS.mkdir(exist_ok=True,parents=True)
    jobs=[u for u in urls if not (JOBS/(c.digest(u.encode())+'.json')).exists()][:limit]
    with ThreadPoolExecutor(max_workers=workers) as ex:list(ex.map(check,jobs))
 results={u:c.read(JOBS/(c.digest(u.encode())+'.json'),{}) for u in urls};co=collections.Counter();hits=[]
 for u,x in results.items():
    co['queued' if not x else 'could not read' if x.get('error') else 'no text' if not x['text_pages'] else 'text hit' if x['hits'] else 'no matching text']+=1
    if x.get('hits'):hits.append({'jurisdictions':[[r['state'],r['geoid'],r['jurisdiction']] for r in rows if r['url']==u],**x})
 c.dump(D/'codebook_matches.json',hits);c.dump(D/'codebook_search_status.json',dict(referrals=len(rows),unique_document_urls=len(urls),results=co,scope='Only linked government PDFs capped at 18 MiB. A no-hit can miss scans, aliases or a newer ordinance. Matches require review.'));print(co)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',action='store_true');p.add_argument('--fetch',action='store_true');p.add_argument('--limit',type=int,default=200);p.add_argument('--workers',type=int,default=8);a=p.parse_args()
 if a.directory:directory()
 run(a.fetch,a.limit,a.workers)
