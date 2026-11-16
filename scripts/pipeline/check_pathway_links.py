"""Guard the reviewed pathway crosswalk separately from the parent source pin."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, json
import lib.discovery as c
P=c.R/'data/pathway_review_fingerprints.json'
def records():
 rules={r['id']:r for r in c.read(c.OUT/'rules.json',[])};by_id={};held=[]
 with (c.R/'data/pathways.csv').open() as fp:
    for p in csv.DictReader(fp):
        rid=p.pop('rule_id');r=rules[rid]
        if r['check'] not in ('snapshot_match','visual_source_check'):held.append(rid);continue
        if not all(p[k].strip() for k in ('path','district_or_area','qualifier')):raise ValueError('Incomplete zoning pathway: '+rid)
        z=by_id.setdefault(rid,dict(source_url=r['url'],source_sha256=r['sha256'],locator=r['locator'],paths=[]))
        if p in z['paths']:raise ValueError('Duplicate pathway: '+rid)
        z['paths'].append(p)
 for z in by_id.values():z['paths'].sort(key=lambda p:(p['path'],p['district_or_area'],p['qualifier']))
 return by_id,held
def run(initial=False):
 by_id,held=records();current={k:c.digest(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()) for k,v in by_id.items()}
 if initial:
    if P.exists():raise ValueError('Baseline already exists. Review changed rows individually before updating their fingerprints.')
    c.dump(P,current)
 expected=c.read(P,{})
 if expected!=current:raise ValueError('Pathway, issuer source, or citation changed: '+', '.join(sorted(k for k in set(expected)|set(current) if expected.get(k)!=current.get(k))))
 c.dump(c.OUT/'pathway_evidence.json',dict(published=by_id,held_rule_ids=sorted(set(held)),held_entries=len(held)))
 print(sum(len(z['paths']) for z in by_id.values()),'source-linked zoning pathways;',len(held),'rows attached to withheld sources')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--initial',action='store_true');run(p.parse_args().initial)
