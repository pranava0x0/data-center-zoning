"""Merge staged inventories without replacing already reviewed source bytes. Offline only."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, json
from pathlib import Path
import lib.discovery as c
D=c.R/'data'
def run():
    ix=c.read(c.INDEX,{});added=0
    def add(u,v):
        nonlocal added
        k=c.address(u);old=ix.get(k,{})
        if old.get('sha256') and old['sha256']!=v['sha256']:raise ValueError('Changed source; review both versions before replacing '+k)
        b=(c.CACHE/(v['sha256']+'.bin')).read_bytes();t=(c.CACHE/(v['sha256']+'.txt')).read_bytes()
        if c.digest(b)!=v['sha256'] or c.digest(t)!=v['text_sha256']:raise ValueError('Corrupt staged snapshot '+k)
        if not old.get('sha256'):ix[k]=v;added+=1
    for stage in ('state-construction','national_rules_terra','compass_code_sources','codebook-ocr','alternate_published_rules','douglas_ga'):
        for u,v in c.read(c.R/f'cache/{stage}/reviewed_index.json',{}).items():add(u,v)
    from ordinances.rules.national_rules import extract
    entries={**c.read(D/'national_rules_astra_sources.json',{}),**c.read(D/'westmetro_sources.json',{})};rules=c.read(D/'national_rules_astra.json',[])+c.read(D/'westmetro_rules.json',[])
    selected={r['url'] for r in rules}
    for k,row in entries.items():
        u=row['url']
        if u not in selected:continue
        b=(c.R/row['path']).read_bytes();sha=row['sha256']
        if c.digest(b)!=sha:raise ValueError('Raw source drift '+u)
        old=ix.get(c.address(u),{})
        if old.get('sha256')==sha and (not row.get('ocr_path') or old.get('ocr_sha256')==row.get('ocr_sha256')):continue
        pages=extract(k,entries);t='\n'.join('[Page '+str(i)+']\n'+v for i,v in enumerate(pages,1)) if row['ext']=='pdf' else pages[0];(c.CACHE/(sha+'.bin')).write_bytes(b);(c.CACHE/(sha+'.txt')).write_text(t);c.dump(c.CACHE/(sha+'.links.json'),[])
        if old.get('sha256')==sha and row.get('ocr_path'):ix.pop(c.address(u))
        add(u,dict(url=u,resolved=u,ocr_sha256=row.get('ocr_sha256'),sha256=sha,text_sha256=c.digest(t.encode()),bytes=len(b),adapter=row['ext'],fetched_at=row['retrieved'],imported_from=row['path']))
    c.dump(c.INDEX,ix);print(added,'additional primary documents indexed')
if __name__=='__main__':run()
