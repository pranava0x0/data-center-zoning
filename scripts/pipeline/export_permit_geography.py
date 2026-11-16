"""GIS-ready governorate and county totals. Locations are Census internal points, never project locations."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, json
from collections import Counter,defaultdict
import lib.discovery as c

def read(path):
 with path.open() as fp:return list(csv.DictReader(fp))
def run():
 geo=[g for g in read(c.R/'data/national/jurisdictions.csv') if g['layer'] in ('state','counties')]
 states={r['state']:r['geoid'] for r in geo if r['layer']=='state'}
 names={(r['state'],r['name'].casefold()):r['geoid'] for r in geo if r['layer']=='counties'}
 data=defaultdict(Counter);missing=defaultdict(Counter);keys=set()
 for r in read(c.OUT/'published.csv'):
    if r['state'] in states:data[states[r['state']]]['rules']+=1
    if r['level'] in ('county','parish') and r['map_geoid'] in names.values():data[r['map_geoid']]['rules']+=1
 def record(q,r):
    q['history']+=1;q['federal_history']+=bool(r['federal_issuer'])
    if r['permit_representative']=='True':
        q[r['permit_bucket']]+=1
        if r['federal_issuer']:q['federal_'+r['permit_bucket']]+=1
 for r in read(c.OUT/'permit_history.csv'):
    st=r['state'];record(data[states[st]],r);gid=names.get((st,r['county'].casefold()))
    if not gid and st=='VA':
        # VA independent cities are county equivalents. Accept explicit city designation.
        loc=r['locality'].casefold().strip()
        if loc.endswith(' city'):gid=names.get((st,loc))
    if gid:record(data[gid],r)
    else:record(missing[st],r)
    if r['permit_representative']=='True':
        assert r['permit_key'] and r['permit_key'] not in keys;keys.add(r['permit_key'])
 qkeys=['history','federal_history','active','historical','unconfirmed','federal_active','federal_historical','federal_unconfirmed']
 totalj=lambda v:sum(v.get(k,0) for k in ('active','historical','unconfirmed'))
 features=[];table=[]
 for g in geo:
    st=g['state'];gid=g['geoid'];v=data[gid];p=dict(state=st,geoid=gid,name=g['name'],layer=g['layer'],ordinance_provisions=v['rules'],distinct_permits=totalj(v),**{k:v[k] for k in qkeys})
    if g['layer']=='state':
        counties=Counter()
        for t in geo:
            if t['state']==st and t['layer']=='counties':counties.update(data[t['geoid']])
        assert all(counties[k]+missing[st][k]==v[k] for k in qkeys),(st,v,counties,missing[st])
    table.append(p);features.append(dict(type='Feature',id=gid,geometry=dict(type='Point',coordinates=[float(g['lon']),float(g['lat'])]) if g['lon'] and g['lat'] else None,properties=p))
 assert sum(p['distinct_permits'] for p in table if p['layer']=='state')==len(keys)
 with (c.OUT/'permit_geography.csv').open('w',newline='') as fp:
    w=csv.DictWriter(fp,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
 (c.OUT/'permit_geography.geojson').write_text(json.dumps(dict(type='FeatureCollection',name='Counts by Census geography; points are not data center sites',features=features),separators=(',',':'))+'\n')
 c.dump(c.OUT/'permit_geography_quality.json',dict(state_and_territory_features=len(states),county_equivalent_features=len(geo)-len(states),permit_keys=len(keys),unassigned_by_state=missing,assignment='Exact state and county-equivalent name as reported; explicitly named Virginia independent cities are eligible. Empty or ambiguous county not assigned. State history and rule totals include lower levels; county provision counts only provisions issued by that county. Federal records are a subset of all records.'))
 print(len(features),'Census state/county locations;',len(keys),'distinct permits reconciled')
if __name__=='__main__':run()
