"""Prioritize unreviewed research without mistaking Census geography for legal authority."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, json
from collections import defaultdict
import lib.discovery as c
def main():
    def rows(s):return list(csv.DictReader(s.open()))
    ap=argparse.ArgumentParser();ap.add_argument('--basis',choices=['count','forecast','power'],default='count');basis=ap.parse_args().basis
    key={'count':'count_rank','forecast':'scenario_rank','power':'directory_power_rank'}[basis]
    priority={r['state']:int(r[key]) for r in rows(c.R/'data/state_priority.csv')}
    census=[g for g in rows(c.OUT/'coverage.csv') if g['state'] in priority]  # Historical ten-state queues; nationwide order is in data/national/priority.csv.
    registry=defaultdict(list)
    for r in c.rules():
        if r.get('geoid'):registry[r['geoid']].append(r['url'])
    va=c.read(c.OUT/'virginia_screen.json',{})['results']
    byid={i:s for s in va for i in s['geoids']}
    local=c.read(c.OUT/'local_screen.json',{}).get('rows',{})
    jobs=[]
    for g in census:
        gid=g['geoid'];s=byid.get(gid,{})
        direct=local.get(gid,{})
        # Offer only actual pages with data-center mentions as proof of a lead.
        cand=[d['url'] for d in s.get('documents',[]) if d['data_center_mentions']]
        leads=[x[1] for x in s.get('leads',[])]
        targets=list(dict.fromkeys(cand+[p['url'] for p in direct.get('pages',[]) if p['hits']]+registry[gid]+leads[:3]))
        gov=s.get('url') or direct.get('entry') or next(('https://'+u for u in g['domain_candidates'].split('|') if u),'')
        activity=g['coverage']
        stage=('adjudicate held source' if activity=='evidence held' else 'review candidate passage' if activity=='screened: candidate only' else 'follow planning/code links' if targets and not registry[gid] else 'find or confirm issuing authority' if not gov and not targets else 'screen official sources' if not registry[gid] else 'audit remaining topics and monitor changes')
        if not registry[gid] and activity!='evidence held':
            if direct.get('result')=='possible mention':stage='review candidate passage'
            elif direct.get('result')=='no keyword match' and not cand:stage='inspect full local code or request records'
            elif direct.get('result')=='unavailable' and not targets:stage='locate a readable government source'
        jobs.append(dict(ranking_basis=basis,state_rank=priority[g['state']],state=g['state'],geoid=gid,name=g['name'],layer=g['layer'],coverage=activity,next_step=stage,entry_url=gov,document_leads=' | '.join(targets),order_key=(0 if gid=='51107' else 1 if stage.startswith('review candidate') else 2 if stage.startswith('adjudicate') else 3 if targets else 4 if gov else 5)))
    jobs.sort(key=lambda j:(j['state_rank'],j['state'],j['order_key'],j['name'],j['geoid']))
    with (c.OUT/('worklist.csv' if basis=='count' else 'worklist_'+basis+'.csv')).open('w') as f:
        w=csv.DictWriter(f,fieldnames=jobs[0]);w.writeheader();w.writerows(jobs)
    print(len(jobs),'geographic work items (layers may overlap)')
if __name__=='__main__':main()
