"""Search published government entry points and linked planning documents. Offline by default.
Never infer that development is allowed or prohibited from a search with no hits.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections, csv, gzip, hashlib, json, re, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit,urljoin,urlunsplit
from urllib.request import Request,urlopen
import lib.discovery as c
D=c.R/'cache/local-screen';BASE=D/'pages';LOG=D/'visits';OUT=c.OUT/'local_screen.json'
DIR={'in-directory':('IN','https://www.in.gov/counties/'),'az-cities':('AZ','https://libguides.asu.edu/salad/cities'),'az-counties':('AZ','https://libguides.asu.edu/salad/counties')}
TERM=re.compile(r'\b(?:data[\s-]*(?:cent(?:er|re)|processing facilit)(?:s|ies|y)?|server farm|hyperscale)\b',re.I)
TOPIC=re.compile(r'zoning|ordinances?|land use|development code|municipal code|planning|community development',re.I)
LOCK=threading.Lock();HOST={}
def norm(s):return re.sub(r' (city|town|village)$','',s.lower().strip())
def roster():
    gs=list(csv.DictReader((c.R/'data/jurisdictions.csv').open()));todo={};lookup=collections.defaultdict(list)
    ready=set()
    for x in c.read(c.OUT/'virginia_screen.json',{}).get('results',[]):
        if x['documents']:ready.update(x['geoids'])
    for r in c.read(c.OUT/'rules.json',[]):
        if r['check'] in ('snapshot_match','visual_source_check'):ready.add(r.get('map_geoid'))
    for g in gs:
        gid=g['geoid'];lookup[g['state'],norm(g['name'])].append(gid)
        domains=[x for x in g['domain_candidates'].split('|') if x and not re.search('sheriff|elections|library|police|firedept',x)]
        todo[gid]=[g['state'],g['name'],'https://'+domains[0]+'/' if domains else '', 'CISA .gov directory candidate' if domains else '']
    for tag,(st,url) in DIR.items():
        p=D/(tag+'.html')
        if not p.exists():continue
        for href,title in c.parse(p.read_bytes(),'text/html',url)[2]:
            if not href.startswith(('https://','http://')):continue
            s=re.sub(r'^(City|Town|Village) [Oo]f ','',title.strip());s=re.sub(r' (Government|Official Website|Official Site|Website)$','',s,flags=re.I)
            for gid in lookup.get((st,norm(s)),[]):
                if tag=='in-directory' and not ('government' in title.lower() or title.endswith('County') or re.match('^(Town|City) of ',title)):continue
                if not todo[gid][2]:todo[gid][2:]=[re.sub('^http:','https:',href),url]
    for row in c.read(c.OUT/'virginia_screen.json',{}).get('results',[]):
        for gid in row['geoids']:
            if gid in todo and not todo[gid][2]:todo[gid][2:]=[row['url'],'Virginia government directory']
    catalog=D/'UScityURL.csv'
    if catalog.exists():
        with catalog.open() as f:
            for row in csv.DictReader(f):
                gid=row['GEOID'].split('US')[-1];u=row['WEBSITE_URL'].strip()
                if gid in todo and not todo[gid][2] and row['WEBSITE_AVAILABLE']=='1' and u.startswith(('https://','http://')) and not re.search('facebook.com|wikipedia.org',u,re.I):
                    todo[gid][2:]=[re.sub('^http:','https:',u),'UScityURL 2022 (GEOID)']
    table=c.R/'data/screen_rosters/census.csv'
    if table.exists():
        with table.open() as f:
            for row in csv.DictReader(f):
                t=todo[row['geoid']]
                if not t[2]:t[2:]=[row['url'],'US Census 2022 General Purpose Governments']
    for name in ['townships','extra_sites']:
        f=c.R/'data/screen_rosters'/(name+'.csv')
        if f.exists():
            with f.open() as fin:
                for row in csv.DictReader(fin):
                    if row['geoid'] in todo and not todo[row['geoid']][2]:
                        todo[row['geoid']][2:]=[row['url'],row.get('origin') or name]
    return todo,ready
def h(b):return hashlib.sha256(b).hexdigest()
def read_page(url):
    with LOCK:lock=HOST.setdefault(urlsplit(url).hostname,threading.Lock())
    with lock:
        c.policy(url)
        with urlopen(Request(url,headers={'User-Agent':c.AGENT}),timeout=6) as res:
            b=res.read(3*1024*1024+1);mime=res.headers.get_content_type();final=res.url
    if len(b)>3*1024*1024:raise ValueError('page too large')
    if mime not in ('text/html','application/xhtml+xml','application/pdf','text/plain'):raise ValueError('unsupported '+mime)
    typ,s,links=c.parse(b,mime,final);sha=h(b)
    if not s.strip() or len(s.strip())<80:raise ValueError('no readable text')
    if any(x in s[:1200].lower() for x in ['verify you are human','performing security verification','this domain is for sale','checking your browser before accessing']):raise ValueError('challenge or parked domain')
    path=BASE/(sha+'.gz')
    if not path.exists():path.write_bytes(gzip.compress(b,compresslevel=3,mtime=0))
    hits=[s[max(0,m.start()-65):m.end()+100].strip() for m in list(TERM.finditer(s))[:4]]
    return dict(url=final,sha256=sha,adapter=typ,hits=hits),links
def harvest(url):
    file=LOG/(h(url.encode())+'.json')
    if file.exists():return
    out=dict(entry=url,pages=[],errors=[])
    try:
        page,links=read_page(url);out['pages'].append(page)
        ranked={}
        for href,label in links:
            u=urljoin(page['url'],href).split('#')[0];parsed=urlsplit(u);e=(label+' '+parsed.path.replace('-',' ')).strip()
            if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.path in ('','/') or u==page['url']:continue
            if parsed.hostname!=urlsplit(page['url']).hostname and not re.search(r'(^|\.)(municode\.com|amlegal\.com|ecode360\.com|codepublishing\.com|encodeplus\.com)$',parsed.hostname):continue
            if not TOPIC.search(e) and not TERM.search(e):continue
            score=(12 if TERM.search(e) else 0)+(5 if re.search('zoning|ordinance|development code|land use',label,re.I) else 0)+1
            ranked[u]=max(ranked.get(u,0),score)
        for u in sorted(ranked,key=lambda u:(-ranked[u],len(u),u))[:2]:
            try:out['pages'].append(read_page(u)[0])
            except Exception as e:out['errors'].append([u,str(e)[:160]])
    except Exception as e:out['errors'].append([url,str(e)[:160]])
    c.dump(file,out)
def main():
    a=argparse.ArgumentParser();a.add_argument('--fetch',action='store_true');a.add_argument('--census-only',action='store_true');a.add_argument('--new-roster-only',action='store_true');a.add_argument('--workers',type=int,default=16);args=a.parse_args()
    BASE.mkdir(parents=True,exist_ok=True);LOG.mkdir(exist_ok=True);todo,ready=roster();urls=sorted({t[2] for gid,t in todo.items() if t[2] and gid not in ready and (not args.census_only or t[3].startswith('US Census')) and (not args.new_roster_only or t[3].startswith('UScityURL'))})
    if args.fetch:
        with ThreadPoolExecutor(max_workers=args.workers) as p:list(p.map(harvest,urls))
    rows={};stats=collections.Counter()
    for gid,(st,name,u,origin) in todo.items():
        p=LOG/(h(u.encode())+'.json');v=c.read(p,{}) if u else {}
        # Shared portals also link to other jurisdictions. Attribute only the
        # listed township path or its descendants, never the county/state home.
        if v and ('county-hosted township page' in origin or 'state-hosted township office' in origin):
            src=urlsplit(u);prefix=src.path.rstrip('/').lower()
            def in_township(page):
                dest=urlsplit(page['url']);path=dest.path.rstrip('/').lower()
                return bool(prefix) and (dest.hostname or '').removeprefix('www.')==(src.hostname or '').removeprefix('www.') and (path==prefix or path.startswith(prefix+'/')) and (not src.query or src.query==dest.query)
            relevant=[p for p in v['pages'] if in_township(p)]
            if len(relevant)!=len(v['pages']):
                v=dict(v,pages=relevant,errors=v['errors']+[[u,'Shared portal: pages outside the listed township path excluded.']])
        if gid in ready and not v:stats['prior research']+=1;continue
        state='no entry point' if not u else 'not attempted' if not v else 'unavailable' if not v['pages'] else 'possible mention' if any(x['hits'] for x in v['pages']) else 'no keyword match'
        stats[state]+=1;rows[gid]=dict(state=st,name=name,result=state,entry=u,origin=origin,pages=v.get('pages',[]),errors=v.get('errors',[]))
    c.dump(OUT,dict(method='Official directory or .gov domain; homepage and up to two linked planning/code pages. A term hit is a lead, not an ordinance.',counts=stats,rows=rows));print(dict(stats),flush=True)
if __name__=='__main__':main()
