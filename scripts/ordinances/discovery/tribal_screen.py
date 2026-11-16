"""Join the Federal Register's printed governments to public agency websites; never infer tribal jurisdiction by state."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, csv, io, collections, unicodedata, re
from concurrent.futures import ThreadPoolExecutor
from lib.url_archive import Archive
from ordinances.discovery.national_local_screen import safe
from ordinances.discovery.screen_local_sites import LOG,harvest,h
import lib.discovery as c
D=c.R/'data/national';U='https://onemap-bia-geospatial.hub.arcgis.com/api/download/v1/items/3c6ae1b6fa9f414cbd36758905b196c3/csv?layers=0'
def norm(s):return ''.join(ch for ch in unicodedata.normalize('NFKD',s.casefold()) if ch.isalnum() and ch.isascii())
def run(fetch):
 a=Archive('tribalsites',fetch,owner='ordinances/discovery/tribal_screen');b,sha=a.get(U);entries=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))));raw=collections.defaultdict(list)
 for r in entries:raw[norm(r['Tribe Full Name'])].append(r)
 paired=[];links=set()
 for r in c.read(D/'tribal_governments.json',[]):
    hits=raw[norm(r['name'])];u=safe(hits[0]['Website']) if len(hits)==1 else '';paired.append((r,u))
    if u:links.add(u)
 if fetch:
    with ThreadPoolExecutor(max_workers=12) as p:list(p.map(harvest,sorted(links)))
 done=[]
 for r,u in paired:
    v=c.read(LOG/(h(u.encode())+'.json'),{}) if u else {};pages=v.get('pages',[]);n=sum(bool(x['hits']) for x in pages)
    done.append(dict(**r,site=u,directory=U,directory_sha256=sha,checked_pages=len(pages),result='Possible mention on pages read' if n else 'No mention on pages read' if pages else 'Website unavailable' if v else 'Website queued' if u else 'No exact website match'))
 c.dump(D/'tribal_site_checks.json',done);print(len(done),'printed names;',len(links),'distinct matched sites;',sum(bool(r['checked_pages']) for r in done),'readable.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
