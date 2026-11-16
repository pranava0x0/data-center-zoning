"""Stage verified offline originals in the shared content-addressed store, never the shared index.
Usage: python3 scripts/audit_rules_terra.py  (offline; no requests to source sites).
HTTP errors, indexed source text, or discovery metadata cannot stand in for raw ordinance bytes.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from lib.discovery import address, digest, dump, norm, parse
from pipeline.compass_taxonomy import classify_rule, UNMAPPED
R=Path(__file__).resolve().parents[3]
raw=R/'cache/national_rules_terra'; shared=R/'cache/sources'; shared.mkdir(exist_ok=True)
rules=json.loads((R/'data/national_rules_terra.json').read_text())
manifest=json.loads((R/'data/national/rules_terra_sources.json').read_text())
def main():
    juris={(r['state'],r['geoid']):r for r in csv.DictReader((R/'data/national/jurisdictions.csv').open())}
    index={}; held=[]; verified=[]
    visual=json.loads((raw/'visual_reviews.json').read_text()) if (raw/'visual_reviews.json').exists() else {}
    assert len({r['id'] for r in rules})==len(rules),'duplicated source rule id'
    for r in rules:
        assert (r['state'],r['geoid']) in juris and classify_rule(r['topic'])!=UNMAPPED,r['id']
        assert r['scope'] in {'data center specific','general','high energy facility'} and r['status']=='adopted' and r['locator'] and r['summary'] and len(r['evidence'].split())<=25
        assert r['url'] in manifest and manifest[r['url']]['type'] in ('enacted code','adopted council exhibit','adopted ordinance','state executive order'),r['id']
    for url,metadata in manifest.items():
        name=metadata.get('file')
        if not name:continue
        p=raw/name;b=p.read_bytes();assert digest(b)==metadata['sha256'],name
        if not any(r['url']==url for r in rules):continue
        key=address(url);h=digest(b)
        dest=shared/(h+'.bin')
        if not dest.exists():
            try:os.link(p,dest)
            except OSError:dest.write_bytes(b)
        assert digest(dest.read_bytes())==h
        kind='application/pdf' if b.startswith(b'%PDF') else 'text/html'
        k,s,l=parse(b,kind,url)
        if not s.strip():raise ValueError(f'{name} has no machine-readable text')
        # Use exactly the shared collector's converter. Never overwrite an already
        # pinned alternative text interpretation for the same content hash.
        textpath=shared/(h+'.txt')
        if not textpath.exists() or textpath.stat().st_size==0:
            # Embedded PDF ToUnicode tables occasionally emit isolated surrogates.
            # Replace only these before UTF-8 writing; the raw source remains byte-exact.
            textpath.write_bytes(s.encode('utf-8','replace'))
        s=textpath.read_text()
        links=shared/(h+'.links.json')
        if not links.exists():dump(links,l)
        index[key]=dict(url=key,resolved=url,fetched_at=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(timespec='seconds'),sha256=h,text_sha256=digest(s.encode()),bytes=len(b),adapter=k,source_role=metadata['type'])
    for r in rules:
        u=address(r['url']);rec=index.get(u)
        if not rec:held.append({'id':r['id'],'reason':manifest[r['url']].get('hold','no original')});continue
        if rec['adapter']=='scan_needs_review':
            check=visual.get(r['id'],{}); assert check.get('url')==r['url'] and check.get('sha256')==rec['sha256'] and check.get('page',0)>0 and check.get('method'),r['id']
        else:assert norm(r['evidence']) in norm((shared/(rec['sha256']+'.txt')).read_text()),r['id']
        verified.append(r['id'])
    dump(raw/'reviewed_index.json',index)
    dump(raw/'audit.json',dict(rules=len(rules),staged_rule_ids=verified,held=held))
    print(f'{len(verified)} ordinance provisions archived and anchored; {len(held)} reviewed online but offline hold; {len(index)} unique supporting source files.')
if __name__=='__main__':main()
