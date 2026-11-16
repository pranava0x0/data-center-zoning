"""Reconcile real search evidence with geographic features. Fail closed on ambiguous local government names."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, collections, csv, json, re, unicodedata
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from ordinances.discovery.national_local_screen import safe
from ordinances.discovery.screen_local_sites import h,harvest,LOG
import lib.discovery as c
D=c.R/'data/national'
def read(p):
 with p.open() as f:return list(csv.DictReader(f))
def norm(name):
 text=unicodedata.normalize('NFKD',name.casefold());text=''.join(x for x in text if not unicodedata.combining(x))
 text=re.sub(r'^(city and borough|city and county|municipality|city|township|town|village|county|borough|parish) of ','',text)
 return re.sub(r' (municipality|census area|township|county|city|town|village|borough|parish|municipio)$','',text).strip()
def inventory():
 geo=read(D/'jurisdictions.csv');overrides=c.read(D/'codebook_locator_corrections.json',[])
 fixes={i['referral_geoid']:i for i in overrides};identified={i['corrected_geoid']:i for i in overrides if i.get('corrected_geoid')}
 gov=collections.defaultdict(list);cisa=collections.defaultdict(set);county={g['geoid']:norm(g['name']) for g in geo if g['layer']=='counties'}
 for r in read(D/'government_units.csv'):
    lev={'1 - COUNTY':'counties','2 - MUNICIPAL':'place','3 - TOWNSHIP':'cousubs'}.get(r['classification'])
    if lev:gov[r['state'],lev,norm(r['name'])].append(r)
 for r in read(c.R/'cache/geo/dotgov.csv'):
    typ={'City':'place','County':'counties'}.get(r['Domain type'])
    if typ=='place' and re.search(r'\btownship\b',r['Organization name'],re.I):typ='cousubs'
    if typ and r['Organization name'] and not re.search(r'police|school|library|authority|sheriff|fire|district|commission|court|elections|clerk|council|association|utilities|department',r['Organization name'],re.I):
        cisa[r['State'],typ,norm(r['Organization name'])].add('https://'+r['Domain name']+'/')
 urls={r['GEOID'].split('US')[-1]:safe(r['WEBSITE_URL']) for r in read(c.R/'cache/local-screen/UScityURL.csv') if r['WEBSITE_AVAILABLE']=='1'}
 territorial={r['geoid']:r['url'] for r in c.read(D/'territory_directories.json',[]) if r['geoid']}
 linked={r['state']:r['url'] for r in c.read(D/'territorial_offices.json',[])}
 for g in geo:
    gid,st,lev=g['geoid'],g['state'],g['layer'];k=(st,lev,norm(g['name']));us=gov[k]
    if lev=='cousubs':us=[r for r in us if norm(r['county_area'])==county.get(gid[:5])]
    direct=safe(us[0]['site']) if len(us)==1 else ''
    url=direct;basis='Census government unit' if url else ''
    if not url and len(cisa[k])==1 and (lev!='cousubs' or len(gov[k])==1):url=next(iter(cisa[k]));basis='CISA .gov registry, exact organization'
    if not url and lev in ('place','cousubs') and urls.get(gid):url=urls[gid];basis='UScityURL exact GEOID'
    if not url and gid in territorial:url=territorial[gid];basis='Territorial directory listing'
    if not url and st in linked and lev in ('state','territory subdivisions'):url=linked[st];basis='Territorial agency only'
    # A shared name is not an issuer match. Keep the underlying bad directory record auditable.
    if gid in fixes and url and urlsplit(url).hostname.removeprefix('www.')==urlsplit(fixes[gid]['url']).hostname.removeprefix('www.'):url='';basis='Listed site belongs to a different government'
    if gid in identified:
        target=identified[gid]['url'];base='https://'+urlsplit(target).netloc
        candidates=[u for u in (url,base,base+'/') if u and urlsplit(u).netloc==urlsplit(target).netloc]
        url=next((u for u in candidates if (LOG/(h(u.encode())+'.json')).exists()),base+'/');basis='Issuer named in local ordinance; county and government type checked'
    yield g,url,basis
def run(fetch,limit,workers,additional=False):
 rr=list(inventory());counts=collections.defaultdict(collections.Counter)
 if fetch:
    queue=sorted({u for _,u,b in rr if u and b!='Territorial agency only' and (not additional or b!='Census government unit') and not (LOG/(h(u.encode())+'.json')).exists()});print('Remaining distinct added websites:',len(queue),flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:list(pool.map(harvest,queue[:limit]))
 published=collections.Counter(r.get('map_geoid') for r in c.read(c.OUT/'rules.json',[]) if r['check'] in ('snapshot_match','visual_source_check'))
 with (c.OUT/'national_jurisdiction_checks.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow('state layer geoid name source_basis url result pages mentions cited_provisions'.split())
    for g,u,b in rr:
        st,lev=g['state'],g['layer'];visit=c.read(LOG/(h(u.encode())+'.json'),{}) if u else {};pages=visit.get('pages',[]);hits=sum(bool(x['hits']) for x in pages);n=published[g['geoid']]
        result='Cited ordinance or permit rule' if n else 'Territorial office only' if b=='Territorial agency only' else 'Possible mention on pages read' if hits else 'No mention on pages read' if pages else 'Website unavailable' if visit else 'Website queued' if u else 'Statistical geography; no government assumed' if lev.startswith(('statistical','other county')) else 'No municipal source joined'
        w.writerow([st,lev,g['geoid'],g['name'],b,u,result,len(pages),hits,n]);counts[st][result]+=1
 c.dump(c.OUT/'national_jurisdiction_summary.json',counts)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--limit',type=int,default=500);p.add_argument('--workers',type=int,default=16);p.add_argument('--additional-only',action='store_true');a=p.parse_args();run(a.fetch,a.limit,a.workers,a.additional_only)
