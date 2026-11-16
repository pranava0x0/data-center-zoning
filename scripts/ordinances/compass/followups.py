"""Search the remaining eligible COMPASS document referrals; reuse prior checks by exact URL."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, csv, collections
from concurrent.futures import ThreadPoolExecutor
import lib.discovery as c, ordinances.codebooks.inventory as books
from ordinances.compass.code_sources import CACHE
D=c.R/'data/national'
def run(fetch,workers,limit):
 rows=list(csv.DictReader((D/'compass_code_sources_queue.csv').open()));local=books.JOBS;files=books.FILES;books.JOBS=CACHE/'checks';books.FILES=CACHE/'files'
 jobs=[];hits=[];stats=collections.Counter()
 try:
    for r in rows:
        name=c.digest(r['url'].encode())+'.json'
        if not (local/name).exists() and not (books.JOBS/name).exists():jobs.append(r['url'])
    if fetch:
        with ThreadPoolExecutor(max_workers=workers) as p:list(p.map(books.check,jobs[:limit]))
    for r in rows:
        name=c.digest(r['url'].encode())+'.json';use=local/name if (local/name).exists() else books.JOBS/name;z=c.read(use,{})
        outcome='not visited' if not z else 'unavailable' if z.get('error') else 'text match' if z.get('hits') else 'no readable text' if not z.get('text_pages') else 'no match in readable pages'
        stats[outcome]+=1
        if z.get('hits'):hits.append(dict(**r,archive=str(use.relative_to(c.R)),sha256=z['sha256'],pages=z['pages'],hits=z['hits']))
 finally:books.JOBS=local;books.FILES=files
 c.dump(D/'compass_followup_matches.json',hits);c.dump(D/'compass_followup_status.json',dict(documents=len(rows),results=stats,scope='Every eligible PDF-type referral in the queue, including the frozen validation sample. Only reviewed, locally supported rules may enter the atlas.'))
 print(len(rows),'documents;',stats)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--workers',type=int,default=8);p.add_argument('--limit',type=int,default=1500);a=p.parse_args();run(a.fetch,a.workers,a.limit)
