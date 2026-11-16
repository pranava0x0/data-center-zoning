"""Join state priorities, leading local clusters and independently sourced atlas records.
No facility counts are inferred from permit filings. No authority is inferred from a place name.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import collections, csv, re
import lib.discovery as c
D=c.R/'data/national'
def read(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 with p.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
import lib.geo_labels as geo_labels
KEEP=geo_labels.exceptions()
def normalized(s,st):
 s=s.casefold().strip();s=re.sub(r'^(?:the )?(?:city|town|village|township) of ','',s);return re.sub(r' township$','',geo_labels.key(s,st,KEEP))
def run():
 ranked=read(D/'priority.csv');hot=read(D/'hotspots.csv');rules=read(c.OUT/'published.csv');events=read(c.OUT/'permit_history.csv');geos=read(D/'jurisdictions.csv')
 from ordinances.discovery.local_register_audit import audit
 reviewed=audit(events)
 geo=collections.defaultdict(list)
 for g in geos:geo[g['state'],g['layer'],normalized(g['name'],g['state'])].append(g)
 highlights=[];score=[]
 for st in ranked:
    state=st['state'];rr=[r for r in rules if r['state']==state];ee=[e for e in events if e['state']==state];buckets=collections.Counter(e['permit_bucket'] for e in ee if e['permit_representative']=='True');hs=[]
    for group,layer in [('Reported county','counties'),('place','place'),('cousubs','cousubs'),('statistical place','statistical place')]:
        locations=[h for h in hot if h['state']==state and h['layer']==group];m=max([int(h['markers']) for h in locations],default=0)
        for h in locations:
            if int(h['markers'])!=m:continue
            g=geo[state,layer,normalized(h['name'],state)]
            geoid=h['geoid'] or (g[0]['geoid'] if len(g)==1 else '')
            # Strict unambiguous local labels only. Never assign a county's law to contained cities.
            attached=[r for r in rr if geoid and r['map_geoid']==geoid]
            def scopes(e):
                if group=='Reported county':return [e['county'],e['jurisdiction']]
                return [e['locality'],e['jurisdiction']]
            # Avoid a town/township homonym getting another government's cases.
            ambiguity=sum(bool(geo[state,ly,normalized(h['name'],state)]) for ly in ('place','cousubs','counties'))>1
            def matches(e):
                return any(v.casefold()==h['name'].casefold() or (not ambiguity and normalized(v,state)==normalized(h['name'],state)) for v in scopes(e) if v)
            linked=[e for e in ee if matches(e)];hs.append((group,h['name'],m))
            local=[e for e in linked if e['dataset'] in reviewed];permits={e['permit_key']:e['permit_bucket'] for e in linked if e['permit_key']};local_keys={e['permit_key'] for e in local if e['permit_key']}
            highlights.append(dict(reviewed_local_register_rows=len(local),reviewed_local_permit_keys=len(local_keys),all_permit_keys_at_location=len(permits),active_keys_at_location=sum(v=='active' for v in permits.values()),historical_keys_at_location=sum(v=='historical' for v in permits.values()),unconfirmed_keys_at_location=sum(v=='unconfirmed' for v in permits.values()),example_local_register=local[0]['dataset'] if local else '',example_local_record=local[0]['url'] if local else '',state=state,group=group,location=h['name'],geoid=geoid,facility_markers=m,local_provisions=len(attached),history_rows_named_here=len(linked),federal_rows_named_here=sum(bool(e['federal_issuer']) for e in linked),example_rule=next((r['url'] for r in attached),''),example_history=next((e['url'] for e in linked),'')))
    cols={k:', '.join(f'{name} ({count})' for group,name,count in hs if group==k) for k in ('Reported county','place','cousubs','statistical place')}
    score.append(dict(rank=st['count_rank'],state=state,name=st['name'],listed=st['listed_count'],operating=st['operating'],under_construction=st['under_construction'],planned=st['planned'],leading_counties=cols['Reported county'],leading_cities_or_towns=cols['place'],leading_townships=cols['cousubs'],leading_statistical_places=cols['statistical place'],verified_provisions=len(rr),local_provisions=sum(r['level'] in ('city','town','township','village','municipality','county','parish','borough','consolidated') for r in rr),statewide_provisions=sum(r['level']=='state' for r in rr),history_rows=len(ee),federal_rows=sum(bool(e['federal_issuer']) for e in ee),active_permit_keys=buckets['active'],historical_permit_keys=buckets['historical'],status_unconfirmed_keys=sum(n for k,n in buckets.items() if k not in ('active','historical'))))
 assert len(score)==56 and sum(r['history_rows'] for r in score)==len(events) and sum(r['verified_provisions'] for r in score)==len(rules)
 write(c.OUT/'state_progress.csv',score);write(c.OUT/'priority_localities.csv',highlights)
 backlog=[r for r in highlights if r['group']!='statistical place' and not r['reviewed_local_register_rows']]
 # A code or meeting-site referral is a starting point for a clerk or permit search,
 # never a finding that a site has a particular law. Join only the exact geographic ID.
 referrals=collections.defaultdict(list)
 for ref in read(D/'local_code_referrals.csv'):
    referrals[ref['geoid']].append((ref['referring_page'],ref['url'],ref['provider'],ref['referring_sha256']))
 books=collections.defaultdict(list)
 for ref in read(D/'codebooks.csv'):
    books[ref['geoid']].append((ref['referral'],ref['url'],'Published codebook',ref['referral_sha256']))
 queue=[]
 for item in backlog:
    gid=item['geoid'];refs=sorted(set(referrals.get(gid,[])+books.get(gid,[]))) if gid else []
    entry=next((t for t in refs if t[1] and t[0] and t[3]),None)
    queue.append(dict(**item,starting_government_page=entry[0] if entry else '',linked_resource=entry[1] if entry else '',source_kind=entry[2] if entry else '',government_referral_sha256=entry[3] if entry else '',discovery_links=len(refs),next_step='Check local permit and hearing register' if entry else 'Identify issuing office and obtain an official register link'))
 if queue:write(c.OUT/'priority_local_backlog.csv',queue)
 lines=['# Where the atlas has records','','State order follows operating, under-construction and planned listings in the [directory snapshot](../data/national/priority.csv). County and municipal priorities use [PNNL mapped facility markers](../data/national/hotspots_audit.json), which cover fewer facilities and do not measure gigawatts. Ties are kept. A dash means no ranking source for this area. A zero means no published atlas record in that column, not that a jurisdiction has no law or permit.','','[State totals and permit status](../output/state_progress.csv) · [Leading localities, matching record counts and example government documents](../output/priority_localities.csv) · [Search the full directory](../viewer/coverage.html)','','| State or territory | Listed sites | Leading county (markers) | Leading city or town (markers) | Rules | History rows | Federal subset |','|---|---:|---|---|---:|---:|---:|']
 for x in score:
    lines.append(f"| [{x['name']}](../viewer/index.html#view=permits&state={x['state']}) | {x['listed'] or '—'} | {x['leading_counties'] or '—'} | {x['leading_cities_or_towns'] or '—'} | {x['verified_provisions']} | {x['history_rows']} | {x['federal_rows']} |")
 lines.extend(['','The CSV also includes the leading statistical places, such as Ashburn, Virginia. They identify a concentration of facilities, not a separate permitting government. The local CSV counts rules tied to that Census identifier and history rows explicitly naming the city or county; missing geography can leave genuine cases unmatched. A county history count can include projects inside a city. Federal records are already included in history. Never sum the county and city columns, or equate a history row with a distinct permit.'])
 lines.extend(['','[Local permit follow-up queue](../output/priority_local_backlog.csv): leading counties, cities and townships with no matched action in the [reviewed local registers](../output/local_register_examples.csv). A federal or state case in a county does not establish coverage of its local permit office. Unclassified registers are excluded from these lower bounds. A local-government record at a site in a county can be city-issued; see the register name and primary citation. The full locality CSV includes dates only through the edition cutoff and counts unique permit keys even when a representative row appears elsewhere.'])
 (c.R/'docs/national-progress.md').write_text('\n'.join(lines)+'\n');print(len(score),'states/territories,',len(highlights),'leading localities including ties')
if __name__=='__main__':run()
