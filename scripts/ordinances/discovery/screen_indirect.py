"""Search places without a readable local entry point by name in archived same-state material.
This is a lead search, never a review of that jurisdiction's own code.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, gzip, json, re, collections
from pathlib import Path
import lib.discovery as c
from ordinances.discovery.screen_local_sites import TERM
def main():
    local=c.read(c.OUT/'local_screen.json',{})['rows']; geo={g['geoid']:g for g in csv.DictReader((c.R/'data/jurisdictions.csv').open())}
    docs=collections.defaultdict(dict)
    def index(st,url,sha,text):
        if (url,sha) in docs[st]:return
        excerpts=[' '.join(text[max(0,m.start()-225):m.end()+225].split()) for m in TERM.finditer(text)]
        docs[st][url,sha]=excerpts
    for r in local.values():
        for p in r.get('pages',[]):
            if (p['url'],p['sha256']) in docs[r['state']]:continue
            if not p['hits']:docs[r['state']][p['url'],p['sha256']]=[];continue
            b=gzip.decompress((c.R/'cache/local-screen/pages'/(p['sha256']+'.gz')).read_bytes())
            _,txt,_=c.parse(b,'application/pdf' if p['adapter']=='pdf' else 'text/html',p['url'])
            index(r['state'],p['url'],p['sha256'],txt)
    for r in c.read(c.OUT/'rules.json',[]):
        sha=r.get('sha256');p=c.CACHE/(str(sha)+'.txt')
        if sha and p.exists():index(r['state'],r['url'],sha,p.read_text())
    results={};n=collections.Counter()
    for gid,r in local.items():
        if r.get('pages'):continue
        st=r['state'];g=geo[gid];name=g['name']
        if g['layer']=='place':name=re.sub(r' (city|town|village)$','',name,flags=re.I)
        pattern=re.compile(r'(?<!\w)'+re.escape(name)+r'(?!\w)',re.I)
        hits=[]
        for (url,sha),windows in docs[st].items():
            match=next((w for w in windows if pattern.search(w)),None)
            if match:hits.append({'url':url,'sha256':sha,'excerpt':match})
        results[gid]=dict(state=st,name=g['name'],direct=r['result'],indexed_pages=len(docs[st]),nearby_text_hits=hits)
        n['names searched']+=1;n['with leads']+=bool(hits)
    c.dump(c.OUT/'indirect_screen.json',dict(unit='place-name matches near data-center terms in archived same-state documents; not findings or a local code search',counts=n,states={s:len(x) for s,x in docs.items()},results=results));print(dict(n))
if __name__=='__main__':main()
