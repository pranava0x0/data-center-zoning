"""Supplement the Census URL screen with county-qualified township directory links.

python3 scripts/township_screen_roster.py [--refresh-in] [--oh-html FILE]

Default: offline, reads cache/screen_rosters, writes townships.csv + coverage audit.
Ohio snapshot came from the public OTA page's headings/list and exact anchor targets
(including targets explicitly reported as fetch failures). Numeric link references
are snapshot-local; do not mix generations. To update Ohio, provide a fresh saved
public HTML page; the direct web host declined automated download on this run.
No form submission, URL guessing, or screening of ordinances is performed here.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse
from collections import Counter, defaultdict
import csv
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path
import json
import hashlib
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parents[3]
CACHE=ROOT/'cache/screen_rosters'
DATA=ROOT/'data/screen_rosters'
OH='https://www.ohiotownships.org/ohio-townships-map'
IN='https://www.in.gov/townships/'
HAMILTON='https://www.hctaindiana.com/about'
COUNTY_SITES={'defiance-county.com','co.delaware.oh.us','fultoncountyoh.com','co.geauga.oh.us','co.madison.oh.us','co.marion.oh.us','jeffersontwp.mercercountyoh.org','miamicountyohio.gov','sciotocountyoh.com','williamscountyoh.gov'}
EXCLUDE_HOSTS={'facebook.com','facebook.net','washogs.org','crawfordcountyta.us','woodcountytownships.com','mcta.info','andovervillage.com'}
def clean(t):return ' '.join(unescape(re.sub('<[^>]+>',' ',t)).split())
def key(t):return re.sub('[^a-z0-9]','',t.lower().replace('saint','st').replace(' township','').replace(' county',''))
def host(url):return (urlsplit(url).hostname or '').lower().removeprefix('www.')
def readcsv(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def get(u,p):
    with urlopen(Request(u,headers={'User-Agent':'TownshipDirectoryResearch/1.0'}),timeout=25) as resp:
        t=resp.read()
    if b'<html' not in t.lower():raise ValueError('Not HTML: '+u)
    p.write_bytes(t)
def in_links(h):
    return {u.rsplit('/',1)[-1]:clean(label) for u,label in re.findall(r'<a\b[^>]*href="(/townships/[a-z0-9]+)"[^>]*>([^<]+)',h,re.I) if 'township' in label.lower()}
def in_pages():
    links=in_links((CACHE/'in-directory.html').read_text())
    if 'fun' not in links or len(links)<30:raise ValueError('Incomplete state directory')
    pages={k:(urljoin(IN,k),v) for k,v in links.items() if k!='fun'}
    fun=(CACHE/'in-fun.html').read_text()
    for slug,tag in re.findall(r'<a\b[^>]*href="(/townships/fun/townships/[a-z]+)"[^>]*>([^<]+)',fun,re.I):
        n=slug.rsplit('/',1)[1];pages['fun-'+n]=(urljoin(IN,slug),clean(tag)+' Township')
    return pages
def refresh_in():
    get(IN,CACHE/'in-directory.html')
    get(urljoin(IN,'fun'),CACHE/'in-fun.html')
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda kv:get(kv[1][0],CACHE/('in-'+kv[0]+'.html')),in_pages().items()))
def parse_oh(t):
    rows=[]; targets={}; headings=list(re.finditer(r'<h4\b[^>]*>(.*?)</h4>',t,re.I|re.S))
    for i,m in enumerate(headings):
        county=clean(m[1]); segment=t[m.end():headings[i+1].start() if i+1<len(headings) else len(t)]
        if county=='Wyandot':segment=segment[:segment.lower().find('</ul>')+5]
        for item in re.findall(r'<li\b[^>]*>(.*?)</li>',segment,re.I|re.S):
            name=clean(item); a=re.search(r'<a\b[^>]*href=["\']([^"\']+)',item,re.I)
            url=urljoin(OH,unescape(a[1])) if a else None
            idx=len(rows)+1 if url else None
            rows.append({'name':name,'county':county,'id':idx,'host':host(url) if url else None})
            if url:targets[str(idx)]={'url':url,'title':'','accessible':None}
    if len({r['county'] for r in rows})!=88 or not 1200<=len(rows)<=1420:raise ValueError('Ohio directory count or structure changed; inspect HTML before replacement')
    return rows,targets
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--refresh-in',action='store_true');ap.add_argument('--oh-html',type=Path)
    a=ap.parse_args();CACHE.mkdir(parents=True,exist_ok=True)
    if a.refresh_in:refresh_in()
    if a.oh_html:
        rows,links=parse_oh(a.oh_html.read_text());(CACHE/'oh-directory.json').write_text(json.dumps(rows));(CACHE/'oh-anchor-targets.json').write_text(json.dumps(links))
    frame=readcsv(ROOT/'data/jurisdictions.csv');counties={r['geoid']:r['name'] for r in frame if r['layer']=='counties'}
    tw=defaultdict(list)
    for r in frame:
        if r['state'] in ('IN','OH') and r['layer']=='cousubs':tw[(r['state'],key(counties[r['geoid'][:5]]),key(r['name']))].append(r)
    base={r['geoid'] for r in readcsv(DATA/'census.csv') if r['url']}
    stats={s:Counter() for s in ('IN','OH')}; matched={s:set() for s in stats}; listed={s:set() for s in stats}; proposals={}
    def candidate(st,co,tn,url,origin,was_listed=True,why=''):
        ss=stats[st];keys=(st,key(co),key(tn))
        if keys==('OH','ashland','vermilion'):keys=('OH','ashland','vermillion')
        hits=tw.get(keys,[])
        if len(hits)!=1:ss['directory_rows_ambiguous_or_unmatched']+=1;return
        r=hits[0];g=r['geoid'];matched[st].add(g)
        if was_listed:listed[st].add(g)
        if g in base:return
        if not url or why:
            if was_listed:ss['held_'+(why or 'missing_exact_href')]+=1
            return
        if urlsplit(url).scheme not in ('http','https') or not host(url):raise ValueError(url)
        if g in proposals and proposals[g]['url']!=url:raise ValueError('Conflicting qualified links for '+g)
        proposals[g]=dict(geoid=g,state=st,name=r['name'],url=url,origin=origin)
    rows=json.loads((CACHE/'oh-directory.json').read_text());targets=json.loads((CACHE/'oh-anchor-targets.json').read_text())
    href_counts=Counter((targets.get(str(r['id'])) or {}).get('url') for r in rows if r.get('id'))
    for r in rows:
        site=(r.get('host') or '').lower().removeprefix('www.');a=targets.get(str(r['id'])) or {};url=a.get('url');co=r['county'];tn=r['name']
        why='non_government_or_social' if site in EXCLUDE_HOSTS or site.endswith('.facebook.com') else ''
        if url and href_counts[url]>1 and not(site=='fallstownship.org' and co=='Muskingum' and tn=='Falls'):why='shared_target_ambiguous'
        # The Falls Township landing page explicitly identifies MUSKINGUM COUNTY;
        # OTA links the same page under Hocking. Never propagate that attribution.
        if url and host(url)!=site:why='target_host_mismatch'
        if site in COUNTY_SITES and url and urlsplit(url).path in ('','/'):why='county_root_not_township_page'
        ident='county-hosted township page' if site in COUNTY_SITES else 'listed township site'
        origin=f'{OH} | {co} County > {tn} | {ident}'
        candidate('OH',co,tn,url,origin,was_listed=bool(r['id']),why=why)
    in_counties=[c for g,c in counties.items() if g.startswith('18')]
    for k,(url,label) in in_pages().items():
        h=(CACHE/('in-'+k+'.html')).read_text()
        # Strip global portal navigation/footer and use only the township's own content.
        main=re.search(r'<main\b[^>]*>(.*?)</main>',h,re.S|re.I)
        t=clean(main[1] if main else '')+' '+clean(re.search(r'<title>(.*?)</title>',h,re.S|re.I)[1])
        names=[n for n in in_counties if re.search(r'\b'+re.escape(n)+r'\b',t,re.I)]
        tn=re.split(r'\s+Township',label,flags=re.I)[0]
        extra=''
        if k.startswith('fun-') and 'Johnson County' in names:co='Johnson County';extra=' | joint trustee office, township-specific page'
        elif len(names)==1:co=names[0]
        elif k=='washington88' and 'Washington Township of Washington County' in t:co='Washington County'
        elif k=='delaware29' and 'debbie driskell' in t.lower() and 'Fishers, IN 46038' in h:co='Hamilton County';extra=' | matching Fishers trustee locality: '+HAMILTON
        else:raise ValueError(f'County qualification incomplete for {k}: {names}')
        candidate('IN',co,tn,url,f'{IN} | {co} > {tn} | state-hosted township office'+extra)
    for st in stats:
        frame_ids={r['geoid'] for (s,_,_),hits in tw.items() if s==st for r in hits}
        stats[st].update({'frame':len(frame_ids),'frame_in_directory':len(matched[st]),'frame_with_directory_link':len(listed[st]),'frame_without_directory_link':len(frame_ids-listed[st]),'no_link_and_no_census_site':len(frame_ids-listed[st]-base),'frame_already_in_census_roster':len(frame_ids&base),'new_qualified_links':sum(v['state']==st for v in proposals.values())})
    with (DATA/'townships.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=('geoid','state','name','url','origin'));writer.writeheader();writer.writerows(proposals[g] for g in sorted(proposals))
    report={'source_pages':{'OH':OH,'IN':IN},'stats':stats,'definitions':'Frame = project Census township features. Without directory link includes omitted townships, bare listings and unresolved same-name GEOIDs, not a negative government-site or ordinance finding. Supplement excludes GEOIDs already present in Census URL roster. Endpoint or trustee site listing is a discovery lead; county-hosted township pages are specifically labelled. Non-government association, history-site, municipality and social links are held. Exact anchor links, not inferred domain roots.'}
    report['source_evidence']={'cache':str(CACHE.relative_to(ROOT)),'scope':'Ohio saved county headings, bare labels and linked source hosts for the complete printed list; exact click targets saved for supplemental candidates, not already-covered Census entries. Indiana HTML includes the state directory, listed trustee pages and the three individual FUN pages. These seeds are not legal citations.', 'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(CACHE.iterdir()) if p.is_file()}}
    (DATA/'townships-audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
