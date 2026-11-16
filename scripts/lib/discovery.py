"""Bounded official-source discovery, archival fetching and deterministic triage.
Nothing harvested here is automatically promoted to a rule.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, hashlib, io, json, re, sys, time, unicodedata
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urldefrag, quote
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from zipfile import ZipFile
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2]
OUT=R/'output'; CACHE=R/'cache/sources'; INDEX=OUT/'source_index.json'
AGENT='OrdinanceAtlas/1.0 (public-source research)'
LIMIT=35*1024*1024
POLICY={}; LAST={}; NEXT={}
def read(p,default):
    return json.loads(p.read_text()) if p.exists() else default
def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def norm(s):
    return ' '.join(unicodedata.normalize('NFKC',s).replace('\u00ad','').replace('’',"'").replace('‘',"'").replace('–','-').replace('‑','-').replace('“','"').replace('”','"').split()).casefold()
def digest(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def address(url):
    url=urldefrag(url.strip())[0]
    if urlsplit(url).scheme not in ('http','https') or not urlsplit(url).hostname:raise ValueError('Expected http(s) URL')
    return quote(url,safe=":/?&=;%$+@,!~*'()[]-._")
def policy(url):
    u=urlsplit(url);host=u.scheme+'://'+u.netloc
    if host not in POLICY:
        rp=RobotFileParser(); rurl=host+'/robots.txt'
        try:
            with urlopen(Request(rurl,headers={'User-Agent':AGENT}),timeout=12) as r:
                rp.parse(r.read(512000).decode('utf8','replace').splitlines())
        except HTTPError as e:
            if e.code in (404,410):rp.parse([])
            else: raise ValueError(f'robots preflight HTTP {e.code}')
        POLICY[host]=rp
    rp=POLICY[host]
    if not rp.can_fetch('OrdinanceAtlas',url):raise ValueError('robots disallows this URL')
    delay=max(.25,rp.crawl_delay('OrdinanceAtlas') or rp.crawl_delay('*') or 0)
    wait=LAST[host]+delay-time.monotonic() if host in LAST else 0
    if wait>15:raise ValueError('deferred for host crawl delay')
    if wait>0:time.sleep(wait)
    LAST[host]=time.monotonic()
class HTML(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.links=[];self.link=None;self.label=[];self.ignore=0
    def handle_starttag(self,t,a):
        if t in ('script','style','noscript'):self.ignore+=1
        if self.ignore:return
        if t in ('p','div','li','tr','h1','h2','h3','h4','br','section','article','main','td'):self.parts.append('\n')
        if t=='a':self.link=dict(a).get('href');self.label=[]
    def handle_endtag(self,t):
        if t in ('script','style','noscript'):self.ignore=max(0,self.ignore-1)
        if t=='a' and self.link:
            self.links.append((self.link,' '.join(' '.join(self.label).split())));self.link=None
    def handle_data(self,d):
        if not self.ignore:
            self.parts.append(d)
            if self.link:self.label.append(d)
def parse(b,mime,url):
    if b.startswith(b'%PDF'):
        from pypdf import PdfReader
        rd=PdfReader(io.BytesIO(b));pages=[p.extract_text() or '' for p in rd.pages]
        return 'pdf' if any(p.strip() for p in pages) else 'scan_needs_review','\n'.join(f'[Page {i+1}]\n{s}' for i,s in enumerate(pages)),[]
    if b.startswith(b'PK') and ('word' in mime or urlsplit(url).path.lower().endswith('.docx')):
        xml=ET.fromstring(ZipFile(io.BytesIO(b)).read('word/document.xml'))
        return 'docx','\n'.join(''.join(p.itertext()) for p in xml.findall('.//{*}p')),[]
    if 'html' in mime or b.lstrip().lower().startswith((b'<!doctype html',b'<html')):
        enc=re.search(rb'charset=["\x27 ]*([\w-]+)',b[:4096],re.I)
        try: html=b.decode(enc[1].decode() if enc else 'utf-8')
        except (LookupError,UnicodeDecodeError):html=b.decode('windows-1252','replace')
        h=HTML();h.feed(html);s='\n'.join(' '.join(x.split()) for x in ''.join(h.parts).splitlines() if x.strip())
        return 'html',s,h.links
    if mime.startswith('text/plain'):return 'text',b.decode('utf8','replace'),[]
    return 'unsupported','',[]
class SourceStore:
    def __init__(self,refresh=False,offline=False):
        self.index=read(INDEX,{});self.refresh=refresh;self.offline=offline;self.seen=set()
    def get(self,url):
        key=address(url);old=self.index.get(key,{})
        if self.offline or key in self.seen or (old.get('sha256') and not self.refresh):
            return old or {'error':'not_cached'}
        self.seen.add(key)
        try:
            policy(key)
            with urlopen(Request(key,headers={'User-Agent':AGENT}),timeout=22) as r:
                b=r.read(LIMIT+1);mime=r.headers.get_content_type();final=r.url
            if len(b)>LIMIT:raise ValueError('exceeds byte limit')
            h=digest(b);CACHE.mkdir(exist_ok=True,parents=True);(CACHE/(h+'.bin')).write_bytes(b)
            kind,s,links=parse(b,mime,final)
            (CACHE/(h+'.txt')).write_text(s);dump(CACHE/(h+'.links.json'),links)
            rec=dict(url=key,resolved=final,fetched_at=now(),sha256=h,text_sha256=digest(s.encode()),bytes=len(b),adapter=kind)
            if old.get('sha256') and old['sha256']!=h:
                rec['previous_sha256']=old['sha256']
        except Exception as exc:
            rec=dict(url=key,attempted_at=now(),error=type(exc).__name__+': '+str(exc))
            if old.get('sha256'):rec['last_good_sha256']=old['sha256']
        self.index[key]=rec
        with (OUT/'fetch_history.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
        dump(INDEX,self.index);return rec
def rules():
    duplicate={(x["file"],x["id"]) for x in read(R/"data/duplicate_rule_sources.json",[])}
    return [r for n in ('virginia','expansion','utility','extra_local','sweep_promotions','national_rules','national_codebook_rules','national/compass_code_sources_rules','national/filing_rules','national/current_book_rules','national/second_codebook_rules','national/alternate_published_rules','national/township_rules','national/douglas_ga_rules','national/codebook_ocr_rules','westmetro_rules','national_rules_terra','national_rules_astra','state_construction_rules') for r in read(R/f'data/{n}.json',[]) if (n,r['id']) not in duplicate]
PATTERNS={
 'data_center':r'\b(?:data\s*cent(?:er|re)s?|server farms?|digital (?:storage|infrastructure) facilit(?:y|ies)|computer (?:storage|processing) facilit(?:y|ies))\b',
 'permission':r'\b(?:by[ -]right|as[ -]of[ -]right|special exception|conditional use|permitted uses?|specific use permits?|special use|moratorium|moratoria|prohibited uses?)\b',
 'development':r'\b(?:grading permits?|land[ -]disturb(?:ing|ance)|building permits?|site plans?|construction stormwater)\b',
 'water':r'\b(?:pretreatment|(?:groundwater|water) withdrawal|reclaimed water|industrial discharge|discharge permits?)\b',
 'equipment':r'\b(?:stationary engines?|emergency generators?|air permit|noise study|sound level|setbacks?|megawatts?)\b'}
P={k:re.compile(v,re.I) for k,v in PATTERNS.items()}
def hits(s):
    spans=[]
    for k,pat in P.items():
        for m in list(pat.finditer(s))[:12]:
            a=max(0,m.start()-145);z=min(len(s),m.end()+210)
            spans.append(dict(topic=k,start=m.start(),end=m.end(),match=m[0],context=' '.join(s[a:z].split())))
    return sorted(spans,key=lambda d:(d['start'],d['topic']))
def score(s):
    return (8 if P['data_center'].search(s) else 0)+(3 if re.search(r'ordinance|zoning|permit|land use|planning|development code',s,re.I) else 0)+(2 if re.search(r'adopted|enacted|code of|regulations|\.pdf',s,re.I) else 0)
def discover(store,state,budget,geoid=None):
    seeds=read(R/'data/seeds.json',[])
    if geoid:
        with (R/'data/jurisdictions.csv').open() as f:
            for g in csv.DictReader(f):
                if g['geoid']==geoid and g['state']==state:
                    for d in filter(None,g['domain_candidates'].split('|')):
                        seeds.append(dict(state=state,jurisdiction=g['name'],url='https://'+d))
    if not geoid:
        seeds += [dict(state=r['state'],jurisdiction=r['jurisdiction'],url=r['url']) for r in rules()]
    else:
        with (R/'data/jurisdictions.csv').open() as f:
            names={norm(g['name']) for g in csv.DictReader(f) if g['geoid']==geoid and g['state']==state}
        seeds=[s for s in seeds if norm(s['jurisdiction']) in names or s.get('geoid')==geoid]
    seeds=[s for s in seeds if s['state']==state]
    if not seeds:raise SystemExit('No attributed seed for this geography; supply an official URL in data/seeds.json.')
    q=deque((s,s['url'],0) for s in seeds);seen=set();log=[]
    while q and len(log)<budget:
        seed,url,depth=q.popleft();url=address(url);key=(seed['jurisdiction'],url)
        if key in seen:continue
        seen.add(key);d=store.get(url);h=d.get('sha256');found=[];leads=[]
        if h:
            found=hits((CACHE/(h+'.txt')).read_text())
            for href,label in read(CACHE/(h+'.links.json'),[]):
                u=urljoin(d.get('resolved',url),href)
                if urlsplit(u).scheme not in ('https','http'):continue
                u=address(u);weight=score(label+' '+u.split('?')[0].split('/')[-1])
                if u!=url and weight:leads.append((weight,u,label))
        leads=sorted(set(leads),key=lambda x:(-x[0],x[1],x[2]))[:20]
        log.append(dict(state=state,jurisdiction=seed['jurisdiction'],url=url,depth=depth,sha256=h,adapter=d.get('adapter'),error=d.get('error'),hits=found,links=leads,status='candidate_only' if found else 'not_assessed'))
        # Follow only same-host children. External publishers remain attributed leads.
        if depth<1:
            children=[(seed,u,depth+1) for _,u,_ in leads if urlsplit(u).hostname==urlsplit(d.get('resolved',url)).hostname]
            q.extendleft(reversed(children[:3]))
    path=OUT/f'discovery_{state}{"_"+geoid if geoid else ""}.json';dump(path,log)
    print(len(log),'documents;',sum(len(i['hits']) for i in log),'candidate passages;',path.name)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['fetch','discover']);ap.add_argument('--state');ap.add_argument('--geoid')
    ap.add_argument('--budget',type=int,default=12);mode=ap.add_mutually_exclusive_group();mode.add_argument('--refresh',action='store_true');mode.add_argument('--offline',action='store_true')
    a=ap.parse_args();OUT.mkdir(exist_ok=True);s=SourceStore(a.refresh,a.offline)
    if a.command=='discover':
        if not a.state or a.budget<1:ap.error('discover needs --state and a positive --budget')
        discover(s,a.state.upper(),a.budget,a.geoid)
    else:
        for u in sorted({address(r['url']) for r in rules() if not a.state or r['state']==a.state.upper()}):
            d=s.get(u);print(d.get('adapter') or d.get('error'),u,flush=True)
if __name__=='__main__':main()
