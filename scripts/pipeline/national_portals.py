"""Discover actual council records portals from archived government webpages. Portals are leads."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, gzip, re, collections, json
from urllib.parse import urlsplit
from pathlib import Path
import lib.discovery as c
from ordinances.discovery.screen_local_sites import h,BASE,LOG
from ordinances.discovery.national_local_screen import safe
D=c.R/'data/national'
def main():
    rows=collections.defaultdict(set)
    with (D/'government_units.csv').open() as f:
        for r in csv.DictReader(f):
            if r['class_name']=='General Purpose' and (u:=safe(r['site'])):rows[u].add((r['state'],r['name'],r['government_id']))
    found=[];pages={}
    pat=re.compile(rb'https?://([a-z0-9-]+)(?:\.m|\.granicus|\.primegov|\.csv)?\.legistar\.com/',re.I)
    for u,units in rows.items():
        visit=c.read(LOG/(h(u.encode())+'.json'),{})
        for p in visit.get('pages',[]):
            sha=p['sha256']
            if sha not in pages:
                try:pages[sha]={m.decode().lower() for m in pat.findall(gzip.decompress((BASE/(sha+'.gz')).read_bytes()))}
                except FileNotFoundError:pages[sha]=set()
            for client in pages[sha]:
                for st,n,id in units:found.append((st,n,id,u,p['url'],sha,client))
    with (D/'council_portals.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow('state government government_id homepage source source_sha256 client'.split());w.writerows(sorted(set(found)))
    print(len(set(x[-1] for x in found)),'public council register candidates from government pages')
if __name__=='__main__':main()
