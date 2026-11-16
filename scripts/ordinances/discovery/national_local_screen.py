"""Queue public local-government websites in facility-count order. State + subdivision + unit type scope.
Reuse the project's capped, cached, robots-aware homepage/linked-rule collector; never infer no rule from no hit.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections, csv, itertools, json, re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import lib.discovery as c
from ordinances.discovery.screen_local_sites import harvest,h,LOG,BASE
D=c.R/'data/national'
def csvrows(n):
    with (D/n).open() as f:return list(csv.DictReader(f))
def safe(u):
    if not u:return ''
    u=re.sub('^http://','https://',u.strip(),flags=re.I)
    if '://' not in u:u='https://'+u
    host=urlsplit(u).hostname or ''
    if not re.fullmatch('[A-Za-z0-9.-]+',host) or '.' not in host or any(x in host for x in ['facebook.com','instagram.com','wikipedia.org','google.com','godaddy.com']):return ''
    return u
def main():
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--limit',type=int,default=500);p.add_argument('--workers',type=int,default=12);p.add_argument('--states',nargs='*');p.add_argument('--round-robin',action='store_true',help='Visit one new government per state per round, in count-rank order.');a=p.parse_args()
    pr={q['state']:int(q['count_rank'] or 999) for q in csvrows('priority.csv')};allunits=csvrows('government_units.csv')
    units=[x for x in allunits if x['class_name']=='General Purpose' or (x['class_name']=='Special District' and re.search(r'water|sewer|fire|utility|storm|flood|planning|power',x['name'],re.I))]
    units.sort(key=lambda r:(pr.get(r['state'],999),0 if r['class_name']=='General Purpose' else 1,r['classification'],r['name']))
    BASE.mkdir(exist_ok=True,parents=True);LOG.mkdir(exist_ok=True)
    if a.fetch:
        ordered=units
        if a.round_robin:
            by=collections.defaultdict(list)
            for x in units:
                url=safe(x['site'])
                if url and not (LOG/(h(url.encode())+'.json')).exists():by[x['state']].append(x)
            ordered=(x for row in itertools.zip_longest(*by.values()) for x in row if x)
        queue=list(dict.fromkeys(u for r in ordered if (not a.states or r['state'] in a.states) and (u:=safe(r['site'])) and not (LOG/(h(u.encode())+'.json')).exists()))
        with ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(harvest,queue[:a.limit]))
    out=c.OUT/'national_local_checks.csv';stats=collections.defaultdict(collections.Counter)
    with out.open('w',newline='') as f:
        w=csv.writer(f);w.writerow('state government_id name layer origin_url outcome readable_pages lead_urls'.split())
        for r in units:
            u=safe(r['site']);v=c.read(LOG/(h(u.encode())+'.json'),{}) if u else {};pages=v.get('pages',[]);leads=[p['url'] for p in pages if p['hits']]
            result='No listed website' if not u else 'Not visited' if not v else 'Could not read' if not pages else 'Possible mention' if leads else 'No mention on pages read'
            stats[r['state']][result]+=1;w.writerow([r['state'],r['government_id'],r['name'],r['class_name'],u,result,len(pages),' | '.join(leads)])
    c.dump(c.OUT/'national_local_summary.json',stats)
if __name__=='__main__':main()
