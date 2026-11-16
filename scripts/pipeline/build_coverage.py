"""Create the independent nationwide research index without increasing atlas cold-start costs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, json, html
from collections import defaultdict
import lib.discovery as c
from pipeline.build_viewer import pack
D=c.R/'data/national';V=c.R/'viewer'
def read(p):
    with p.open() as f:return list(csv.DictReader(f))
def build():
    prior=read(D/'priority.csv');names={r['state']:r['name'] for r in prior}
    checks={(r['state'],r['government_id'],r['name']):r for r in read(c.OUT/'national_local_checks.csv')} if (c.OUT/'national_local_checks.csv').exists() else {}
    data=defaultdict(list)
    hotspots={r['geoid']:r['markers'] for r in read(D/'hotspots.csv') if r['geoid']} if (D/'hotspots.csv').exists() else {}
    primary={r['state']:0 for r in prior}
    for item in read(c.OUT/'published.csv'):primary[item['state']]+=1
    for item in c.read(D/'territory_directories.json',[]):
        data[item['state']].append([item['name'],'Government directory',item['geoid'],item['scope'],item['url']])
    for item in c.read(D/'territorial_offices.json',[]):
        data[item['state']].append([item['name'],'Permit office','',item['scope'],item['url']])
    geocheck={r['geoid']:r for r in read(c.OUT/'national_jurisdiction_checks.csv')}
    referrals=defaultdict(dict)
    for link in read(D/'local_code_referrals.csv'):
        provider=link['provider'];g=referrals[link['geoid']];u=link['url']
        if provider not in g or len(u)<len(g[provider]):g[provider]=u
    for r in read(D/'jurisdictions.csv'):
        data[r['state']].append([r['name'],r['layer'],r['geoid'],geocheck[r['geoid']]['result']+(' · '+hotspots[r['geoid']]+' facility markers' if r['geoid'] in hotspots else ''),geocheck[r['geoid']]['url'] or r['source'],sorted(referrals[r['geoid']].items())])
    for r in read(D/'government_units.csv'):
        check=checks.get((r['state'],r['government_id'],r['name']),{})
        data[r['state']].append([r['name'],r['class_name'],r['government_id'],check.get('outcome','Government roster'),check.get('origin_url') or r['source']])
    for r in read(D/'tribal_areas.csv'):
        data['Tribal areas'].append([r['name'],r['layer'],r['geoid'],'Geographic reference',r['source']])
    for r in c.read(D/'tribal_site_checks.json',c.read(D/'tribal_governments.json',[])):
        data['Tribal governments'].append([r['name'],'Tribal government',r['id'],r.get('result','Government directory'),r.get('site') or r['url']])
    for r in c.read(D/'outlying.json',[]):
        data['US Minor Outlying Islands'].append([r['name'],'Federal island area',r['id'],r['note'],r['url']])
    states=read(c.OUT/'permit_history.csv');tot=defaultdict(int)
    for r in states:tot[r['state']]+=1
    opts=''.join(f'<option value="{s}">{html.escape(names.get(s,s))}</option>' for s in sorted(data,key=lambda s:names.get(s,s)))
    opts='<option value="">All states and areas</option>'+opts
    initial=''.join(f'<tr><td>{html.escape(r["name"])}</td><td>{r["listed_count"] or "—"}</td><td>{primary[r["state"]]:,}</td><td>{tot[r["state"]]:,}</td><td><a href="index.html#state={r["state"]}&amp;view=permits">Open atlas</a></td></tr>' for r in prior)
    htmltext=(c.R/'templates/coverage.html').read_text().replace('@@STYLE@@',(V/'style.css').read_text()).replace('@@OPTS@@',opts).replace('@@ROWS@@',initial)
    # Store each state independently. A state query does not unpack the entire roster.
    payload=''.join(pack(st,rs) for st,rs in data.items())
    (V/'coverage.html').write_text(htmltext.replace('@@DATA@@',payload).replace('@@LIB@@',(V/'vendor/pako_inflate.min.js').read_text()).replace('@@STATES@@',json.dumps(list(data))).replace('@@COUNT@@',f'{sum(map(len,data.values())):,}'))
if __name__=='__main__':build()
