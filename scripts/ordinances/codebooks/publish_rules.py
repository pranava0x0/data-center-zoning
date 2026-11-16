"""Permanent casebook for government-hosted codes; validate cited page before building a rule."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, csv, re
from collections import defaultdict
import fitz
import lib.discovery as c
D=c.R/'data/national';ROOT=c.R/'cache/codebooks'
def run():
 referrals=defaultdict(list)
 with (D/'codebooks.csv').open() as f:
    for r in csv.DictReader(f):referrals[r['url']].append(r)
 index=c.read(c.INDEX,{});curated=c.read(D/'codebook_claims.json',[]);rules=[];documents={};seen=set()
 for z in curated:
    u=z['url'];gid=z['geoid'];sha=z['sha256']
    if z['id'] in seen:raise ValueError('Duplicate authored claim'); 
    seen.add(z['id'])
    if not any(r['geoid']==gid and r['state']==z['state'] for r in referrals[u]):raise ValueError('Missing government referral '+gid)
    if sha not in documents:
        b=(ROOT/'files'/(sha+'.pdf')).read_bytes()
        if c.digest(b)!=sha:raise ValueError('PDF has changed')
        p=fitz.open(stream=b,filetype='pdf');documents[sha]=[' '.join(pg.get_text().split()) for pg in p]
        t='\n'.join('[Page '+str(i)+']\n'+pg for i,pg in enumerate(documents[sha],1))
        (c.CACHE/(sha+'.bin')).write_bytes(b);(c.CACHE/(sha+'.txt')).write_text(t);c.dump(c.CACHE/(sha+'.links.json'),[])
        key=c.address(u);old=index.get(key,{})
        if old.get('sha256') and old['sha256']!=sha:raise ValueError('Prior version changed; adjudicate '+u)
        index[key]=dict(url=u,resolved=u,fetched_at=c.read(ROOT/'checks'/(c.digest(u.encode())+'.json'),{})['checked'],adapter='pdf',sha256=sha,text_sha256=c.digest(t.encode()),bytes=len(b))
    pg=documents[sha][z['page']-1]
    if c.norm(z['evidence']) not in c.norm(pg):raise ValueError('Evidence missing on stated page: '+z['id'])
    rules.append({k:v for k,v in z.items() if k not in ('page','sha256')})
 c.dump(index_path:=c.INDEX,index);c.dump(c.R/'data/national_codebook_rules.json',rules);print(len(rules),'reviewed claims from',len(documents),'codebooks')
if __name__=='__main__':run()
