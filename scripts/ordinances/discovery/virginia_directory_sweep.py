"""Directory-wide VA screening; cache each locality separately for safe resumable runs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, csv, html, io, json, re, threading, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from urllib.request import Request,urlopen
import lib.discovery as c
DIRECTORY='https://www.virginia.gov/local-government/'
BASE=c.R/'cache/va_sweep'
def directory(refresh):
    folder=c.R/'cache/geo';path=folder/'virginia-directory.html'
    if refresh or not path.exists():
        c.policy(DIRECTORY);path.write_bytes(urlopen(Request(DIRECTORY,headers={'User-Agent':c.AGENT}),timeout=15).read())
    raw=path.read_bytes()
    rows=[]
    for attr,body in re.findall(r'<a\b([^>]+)>(.*?)</a>',raw.decode(),re.I|re.S):
        n=re.search(r'js-vagov-filter__data--gis-name">([^<]+)',body)
        u=re.search(r'href="([^"]+)"',attr)
        if n and u:rows.append((html.unescape(n[1]).strip(),urljoin(DIRECTORY,html.unescape(u[1]))))
    if len(rows)<250:raise ValueError('Directory markup changed; inspect before running.')
    return rows,c.digest(raw)
LOCK=threading.Lock(); HOST={}
def web(url):
    host=urlsplit(url).hostname
    with LOCK: lock=HOST.setdefault(host,threading.Lock())
    with lock:
        c.policy(url)
        with urlopen(Request(url,headers={'User-Agent':c.AGENT}),timeout=12) as r:
            b=r.read(5*1024*1024+1);mime=r.headers.get_content_type();final=r.url
        if len(b)>5*1024*1024:raise ValueError('size limit')
        h=c.digest(b);(BASE/(h+'.bin')).write_bytes(b);typ,s,links=c.parse(b,mime,final)
        return h,typ,s,links,final
def sweep(entry,refresh):
    name,url,ids=entry;p=BASE/(c.digest(name.encode())+'.json')
    if p.exists() and not refresh:return c.read(p,{})
    result=dict(jurisdiction=name,geoids=ids,url=url,retrieved_utc=c.now(),documents=[],leads=[],assessment='screen_only')
    try:
        h,typ,s,links,final=web(c.address(url))
        result['documents'].append(dict(url=final,sha256=h,adapter=typ,data_center_mentions=[x for x in c.hits(s) if x['topic']=='data_center']))
        leads=set()
        for href,lab in links:
            dest=urljoin(final,href)
            if urlsplit(dest).scheme not in ('https','http'):continue
            if not lab or len(lab)>175:continue
            label=lab+' '+urlsplit(dest).path.split('/')[-1]
            w=c.score(label)
            if not w or re.search('calendar|employment|facebook|linkedin|job posting',lab,re.I):continue
            leads.add((w,c.address(dest),lab))
        result['leads']=sorted(leads,key=lambda a:(-a[0],a[1],a[2]))[:12]
        # One additional top-ranked, same-host planning, permitting or ordinance page.
        for w,u,lab in result['leads']:
            if u!=c.address(final) and urlsplit(u).hostname==urlsplit(final).hostname:
                result['attempted_child']=u
                h,typ,s,_,actual=web(u)
                result['documents'].append(dict(url=actual,sha256=h,adapter=typ,data_center_mentions=[x for x in c.hits(s) if x['topic']=='data_center']))
                break
    except Exception as e:result['error']=type(e).__name__+': '+str(e)
    c.dump(p,result);return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');ap.add_argument('--limit',type=int);a=ap.parse_args()
    BASE.mkdir(exist_ok=True,parents=True);rows,checksum=directory(a.refresh)
    with (c.R/'data/jurisdictions.csv').open() as f:
        geo=defaultdict(list)
        for g in csv.DictReader(f):
            if g['state']=='VA':geo[c.norm(g['name'])].append(g['geoid'])
    entries=[(n,u,geo[c.norm(n)]) for n,u in rows];entries=sorted(entries,key=lambda x:(not x[0].lower().startswith('loudoun'),x[0]))[:a.limit]
    with ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(lambda e:sweep(e,a.refresh),entries))
    c.dump(c.OUT/'virginia_screen.json',dict(source=DIRECTORY,directory_sha256=checksum,method='Home page plus at most one same-host ranked link; no legal finding from silence.',results=results))
    print(len(results),'directory entries;',sum(bool(r['documents']) for r in results),'retrieved at least one document')
if __name__=='__main__':main()
