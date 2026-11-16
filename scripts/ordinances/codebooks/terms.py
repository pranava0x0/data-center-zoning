"""Search locally archived text-bearing legal PDFs using a broader historical vocabulary.
Terms can describe ordinary offices; this screen never makes a legal claim.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, csv, collections, re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import fitz
import lib.discovery as c
D=c.R/'data/national';P=c.R/'cache/codebook-terms'
TERMS=re.compile(r'\b(?:data[ -]processing (?:cent(?:er|re)s?|facilit(?:y|ies))|electronic data (?:processing|storage) (?:cent(?:er|re)s?|facilit(?:y|ies))|telecommunications? hotels?|carrier hotels?|internet (?:server|exchange) (?:cent(?:er|re)s?|facilit(?:y|ies))|mission[ -]critical data facilit(?:y|ies)|cloud computing (?:campus(?:es)?|facilit(?:y|ies))|high[ -]performance computing (?:campus(?:es)?|facilit(?:y|ies))|computer (?:cent(?:er|re)s?|data storage facilit(?:y|ies)))\b',re.I)
def examine(item):
 sha,filename=item;p=P/(sha+'.json')
 if p.exists():return
 try:
    hits=[];total=0
    with fitz.open(filename) as pdf:
        n=len(pdf)
        for i,page in enumerate(pdf,1):
            txt=' '.join(page.get_text().split())
            for m in TERMS.finditer(txt):
                total+=1
                if len(hits)<45:hits.append([i,m.group(),txt[max(m.start()-80,0):m.end()+140]])
    c.dump(p,dict(sha256=sha,pages=n,match_count=total,hits=hits))
 except Exception as e:c.dump(p,dict(sha256=sha,error=str(e)[:160],hits=[]))
def run(workers,limit):
 P.mkdir(parents=True,exist_ok=True);links=collections.defaultdict(list);paths={}
 refs=list(csv.DictReader((D/'codebooks.csv').open()));comp=list(csv.DictReader((D/'compass_code_sources_queue.csv').open()))
 for r in refs+comp:
    u=r['url'];k=c.digest(u.encode())+'.json'
    for root in (c.R/'cache/codebooks',c.R/'cache/compass_code_sources'):
        z=c.read(root/'checks'/k,{})
        if not z.get('text_pages'):continue
        h=z['sha256'];paths[h]=str(root/'files'/(h+'.pdf'))
        l=[r.get('state') or r['states'],r.get('geoid') or r['referred_geoids'],u]
        if l not in links[h]:links[h].append(l)
        break
 new=[(h,p) for h,p in sorted(paths.items(),key=lambda x:x[0]) if not (P/(h+'.json')).exists()][:limit]
 if new:
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i,_ in enumerate(pool.map(examine,new,chunksize=3),1):
            if i%250==0:print(i,'/',len(new),flush=True)
 hits=[];examined=0;failed=0
 for h in sorted(links):
    z=c.read(P/(h+'.json'),{})
    if not z:continue
    if z.get('error'):failed+=1;continue
    examined+=1
    if z['hits']:hits.append(dict(referrals=links[h],**z))
 c.dump(D/'alternative_code_terms.json',dict(pattern=TERMS.pattern,eligible_documents=len(paths),examined=examined,failed=failed,matching_documents=len(hits),scope='Screen of readable cached PDF text only. A data-processing office or telecom facility is not necessarily a data center. Inclusion requires separate district, legal status and source review.',documents=hits));print(examined,'read;',len(hits),'matching documents')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=2);p.add_argument('--limit',type=int,default=5000);a=p.parse_args();run(a.workers,a.limit)
