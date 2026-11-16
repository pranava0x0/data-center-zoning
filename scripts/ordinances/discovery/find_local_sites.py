"""Fill roster gaps from Wikidata official-website claims, for discovery only.
Require the locality's qualified Wikipedia title; for counties also require its exact US FIPS.
No encyclopedia text is used as evidence for an ordinance.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, gzip, json, time
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen
import lib.discovery as c
from ordinances.discovery.screen_local_sites import roster,D
def api(host,params):
    key=c.digest(json.dumps(params,sort_keys=True).encode());base=D/'api';base.mkdir(exist_ok=True);f=base/(key+'.gz')
    if not f.exists():
        u='https://'+host+'/w/api.php?'+urlencode(dict(format='json',**params));time.sleep(.52)
        req=Request(u,headers={'User-Agent':'OrdinanceAtlas/1.0 (local government website directory research)','Accept':'application/json'})
        b=urlopen(req,timeout=14).read();j=json.loads(b)
        if 'error' in j:raise RuntimeError(j['error'].get('code'))
        f.write_bytes(gzip.compress(b,mtime=0))
    return json.loads(gzip.decompress(f.read_bytes()))
def main():
    import sys
    todo,ready=roster();geo={g['geoid']:g for g in csv.DictReader((c.R/'data/jurisdictions.csv').open())}
    states={g['state']:g['name'] for g in geo.values() if g['layer']=='state'}
    titles={};out=[];missing=[];files=[]
    for gid,(st,name,u,_) in todo.items():
        if gid in ready or u:continue
        g=geo[gid];ref=name
        if g['layer']=='cousubs':ref=name.title()+', '+geo[gid[:5]]['name']
        elif g['layer']=='place':ref=name.rsplit(' ',1)[0]
        title=ref+', '+states[st];titles.setdefault(title,[]).append(gid)
    order=sorted(titles,key=lambda t:(geo[titles[t][0]]['layer']!='counties',t))
    for k in range(0,len(order),45):
        entries=order[k:k+45]
        try:
            res=api('en.wikipedia.org',dict(action='query',titles='|'.join(entries),prop='pageprops',ppprop='wikibase_item'))
            qids={p['pageprops']['wikibase_item']:p['title'] for p in res['query']['pages'].values() if p.get('pageprops') and p['title'] in titles}
            if not qids:continue
            ents=api('www.wikidata.org',dict(action='wbgetentities',ids='|'.join(sorted(qids)),props='claims'))['entities']
            for q,item in ents.items():
                props=item.get('claims',{})
                def values(key):return [x['mainsnak'].get('datavalue',{}).get('value') for x in props.get(key,[]) if x['rank']!='deprecated']
                sites=[s for s in values('P856') if isinstance(s,str) and urlsplit(s).scheme in ('https','http') and not any(x in s.lower() for x in ['facebook.com','wikipedia.org','twitter.com','instagram.com'])]
                if not sites:continue
                for gid in titles[qids[q]]:
                    g=geo[gid]
                    if g['layer']=='counties' and gid not in values('P882'):continue
                    if g['layer']=='place' and gid not in {str(x).replace('-','') for x in values('P774')}:continue
                    if g['layer']=='cousubs' and ', '+geo[gid[:5]]['name']+', ' not in qids[q]:continue
                    out.append((gid,g['state'],g['name'],sites[0],'Wikidata official website '+q))
        except Exception as e:
            missing.append((k,str(e)))
            if getattr(e,'code',None)==429:break
    with (c.R/'data/screen_rosters/extra_sites.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['geoid','state','name','url','origin']);w.writerows(out)
    c.dump(c.OUT/'site_lookup.json',dict(qualified_titles=len(titles),matched=len(out),batch_errors=missing));print(len(out),'extra URLs',len(missing),'batch failures')
if __name__=='__main__':main()
