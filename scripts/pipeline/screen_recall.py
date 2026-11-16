"""Can a short government-site search rediscover independently documented local rules?
This positive-control panel is not a random sample; report only observed misses.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, collections, json
import lib.discovery as c
def run():
 rules=list(csv.DictReader((c.OUT/'published.csv').open()));geo={r['geoid']:r for r in csv.DictReader((c.OUT/'national_jurisdiction_checks.csv').open())};by=collections.defaultdict(list)
 for r in rules:
    if r['level'] not in ('state','federal','regional') and r['map_geoid']:by[r['map_geoid']].append(r)
 rows=[]
 for g,rr in sorted(by.items()):
    loc=geo.get(g)
    if not loc:raise ValueError('Published rule geography missing from local ledger: '+g)
    rows.append(dict(state=loc['state'],geoid=g,jurisdiction=loc['name'],level=loc['layer'],pages_read=loc['pages'],mention_count=loc['mentions'],disposition=loc['result'],website=loc['url'],documented_provisions=len(rr),published_rule=rr[0]['id'],primary_source=rr[0]['url'],comparison='mention discovered' if int(loc['mentions'] or 0) else 'no candidate from source screen' if int(loc['pages'] or 0) else 'no readable linked pages'))
 with (c.OUT/'local_search_controls.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 groups=collections.Counter(r['comparison'] for r in rows);c.dump(c.OUT/'local_search_quality.json',dict(known_positive_localities=len(rows),outcomes=groups,states=sorted({r['state'] for r in rows}),measurement='This panel comprises localities with a separately documented ordinance or program. A homepage mention need not be the same provision. The result is not nationwide recall or a random negative audit. Check code publishers and clerk archives even when an office page search misses.'))
 print('Local positive controls:',dict(groups))
if __name__=='__main__':run()
