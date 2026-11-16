"""Export the official COMPASS workbook source trail; screen a bounded subset of attributable PDF leads.
Default is offline. Neither an upstream energy finding nor a regex hit is a local data-center policy.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections, csv, hashlib, io, json, re, unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote
from openpyxl import load_workbook
import lib.discovery as c
ROOT=c.R; D=ROOT/'data/national'; CACHE=ROOT/'cache/compass_code_sources'
CSV=D/'compass_code_sources.csv'; AUDIT=D/'compass_code_sources_audit.json'; SCREEN=D/'compass_code_sources_screen.json'
def read(p):
    with p.open() as f:return list(csv.DictReader(f))
def normalized(x):
    return ' '.join(re.findall(r'[a-z0-9]+',unicodedata.normalize('NFKD',str(x or '').strip().casefold()).encode('ascii','ignore').decode()))
SUFFIX=re.compile(r'\s+(?:consolidated government|city and borough|city and county|census area|charter township|metro township|planning region|municipality|borough|county|parish|township|village|town|city|ccd|precinct|district)$')
def base(x):
    s=normalized(x)
    return SUFFIX.sub('',s)
def same_label(s,t):
    # The label 'James City' is the actual county name before the suffix in
    # 'James City County'; do not strip 'City' from both sides unconditionally.
    return bool(s) and (normalized(s)==normalized(t) or normalized(s)==base(t) or base(s)==base(t))
def cell(x):return '' if x is None else str(x)
def clean_url(x):
    try:
        k=urlsplit(x.strip())
        if k.scheme.lower() not in ('https','http') or not k.hostname or k.username or k.password:return ''
        return c.address(urlunsplit((k.scheme.lower(),k.netloc.lower(),k.path,k.query,'')))
    except (TypeError,ValueError):return ''
def host(u):
    return (urlsplit(u).hostname or '').lower().removeprefix('www.') if u else ''
def compact(ids):
    out=[];first=last=ids[0]
    for n in ids[1:]:
        if n==last+1:last=n;continue
        out.append(str(first) if first==last else f'{first}-{last}');first=last=n
    out.append(str(first) if first==last else f'{first}-{last}');return ';'.join(out)
def initgeo():
    geos=read(D/'jurisdictions.csv');return ({r['geoid']:r for r in geos},{normalized(r['name']):r for r in geos if r['layer']=='state'})
def geo(st,county,sub,typ,fips,g,states):
    state=states.get(normalized(st))
    if not state:return '',None,'unresolved: state name'
    code=state['state'];prefix=state['geoid'];raw=fips.strip();typ=normalized(typ)
    if not raw.isdigit():return code,None,'unresolved: FIPS is not numeric'
    if not county and not sub and typ in ('','state'):
        if raw.zfill(5)==prefix+'000':return code,state,'state pseudo-FIPS + state name'
        return code,None,'unresolved: state sentinel mismatch'
    # Preserve input as-is. Excel dropped leading zeroes in some earlier releases.
    size=5 if len(raw)<=5 else 7 if len(raw)<=7 else 10 if len(raw)<=10 else 0
    gid=raw.zfill(size);j=g.get(gid)
    if not j or j['state']!=code:return code,None,'unresolved: GEOID absent or state mismatch'
    layer=j['layer']
    if size==5 and layer=='counties':
        if typ=='city' and not county and sub and normalized(j['name']).endswith(' city') and same_label(sub,j['name']):return code,j,'independent city county-equivalent GEOID + name'
        if not same_label(county,j['name']) or sub or typ not in ('county','borough','parish','city'):return code,None,'unresolved: county-equivalent name or level mismatch'
        return code,j,'county GEOID + name'
    if size not in (7,10) or not sub:return code,None,'unresolved: subdivision name/level mismatch'
    if size==7 and layer not in ('place','statistical place') or size==10 and layer not in ('cousubs','other county subdivision','territory subdivisions'):return code,None,'unresolved: incompatible Census layer'
    if not same_label(sub,j['name']):return code,None,'unresolved: local name mismatch'
    if size==10 and county and (gid[:5] not in g or not same_label(county,g[gid[:5]]['name'])):return code,None,'unresolved: parent county mismatch'
    if layer in ('statistical place','other county subdivision'):return code,j,'geography only: statistical/non-governmental layer'
    return code,j,'subdivision GEOID + name + parent' if size==10 and county else 'GEOID + local name'
def identity_data():
    sites=collections.defaultdict(set)
    for rec in read(c.OUT/'national_jurisdiction_checks.csv'):
        if rec['geoid'] and rec['url'] and clean_url(rec['url']):sites[rec['geoid']].add(host(rec['url']))
    referred={(r['geoid'],clean_url(r['url'])) for r in read(D/'codebooks.csv')}
    ranks={r['state']:int(r['count_rank'] or 999) for r in read(D/'priority.csv')}
    markers={r['geoid']:int(r['markers']) for r in read(D/'hotspots.csv') if r['geoid']}
    return sites,referred,ranks,markers
VENDOR=re.compile(r'(^|\.)(?:ecode360\.com|municode\.com|amlegal\.com|codepublishing\.com|municipal\.codes|qcode\.us|zoneomics\.com|en-codeplus\.com|citycode\.net)$')
GOVDOC=re.compile(r'\.pdf(?:\b|$)|/documentcenter/view/|/archivecenter/viewfile/|/showpublisheddocument/|/vertical/sites/|/publicdocument/',re.I)
BOOK=re.compile(r'(?:ordinance|zoning|udc|udo|land[\W_]*(?:use|development)|municipal[\W_]*code|development[\W_]*(?:code|regulation))',re.I)
NARROW=re.compile(r'(?:wind|solar|wecs|swes|turbine|geotherm|photovoltaic|powerline|transmission|renewable|energy[\W_]*system)',re.I)
def attribution(u,geoid,sites,referred):
    if not u:return 'no valid HTTP source'
    h=host(u)
    if (geoid,u) in referred:return 'linked government codebook referral'
    if VENDOR.search(h):return 'code publisher: official delegation not verified'
    if geoid and h in sites.get(geoid,set()):return 'matched jurisdiction website host'
    if h.endswith('.gov') or re.search(r'\.state\.[a-z]{2}\.us$',h):return 'government host: issuing scope unverified'
    return 'external or unattributed host'
def export():
    gs,states=initgeo();sites,referred,ranks,marks=identity_data()
    sources=json.loads((ROOT/'data/compass_sources.json').read_text())['releases'];rows=[];aud={}
    for src in sources:
        if src['release_kind']!='compass':continue
        a=src['workbook_audit'];tech=src['technology'];sha=a['sha256'];file=(ROOT/'cache/compass'/sha).read_bytes()
        if hashlib.sha256(file).hexdigest()!=sha:raise ValueError(f'{tech}: workbook hash mismatch')
        wb=load_workbook(io.BytesIO(file),read_only=True,data_only=True);grouped=collections.defaultdict(lambda:[[],set(),set()]);heads=None
        for pos,v in enumerate(wb['All Ordinances'].values,1):
            if heads is None:
                if 'State' in v and 'Feature' in v:heads={k:i for i,k in enumerate(v) if k}
                continue
            if not v[heads['State']] or not v[heads['Feature']]:continue
            get=lambda k:cell(v[heads[k]])
            key=tuple(get(k) for k in ['State','County','Subdivision','Jurisdiction Type','County Subdivision FIPS Code','Source URL'])
            rec=grouped[key];rec[0].append(pos);rec[1].add(get('Ordinance Year'));rec[2].add(get('Feature'))
        wb.close();acc=0
        for (st,county,sub,typ,fips,url),(ids,years,ft) in sorted(grouped.items()):
            acc+=len(ids);abbr,j,check=geo(st,county,sub,typ,fips,gs,states);u=clean_url(url);gid=j['geoid'] if j else '';role=attribution(u,gid,sites,referred);path=unquote(u)
            rows.append(dict(technology=tech,catalog_url=src['catalog_url'],catalog_date=src['published'],compass_version=src['extraction_software_version'],workbook_url=next(x for x in src['resources'] if x.lower().endswith('.xlsx')),workbook_sha256=sha,worksheet='All Ordinances',excel_rows=compact(ids),feature_rows=len(ids),original_state=st,original_county=county,original_subdivision=sub,original_level=typ,original_fips=fips,original_years=';'.join(sorted(years-{''})),original_feature_labels=';'.join(sorted(ft)),original_url=url,url=u,host=host(u),state=abbr,match=check,geoid=gid,census_layer=j['layer'] if j else '',census_name=j['name'] if j else '',census_source=j['source'] if j else '',url_authority=role,state_rank=ranks.get(abbr,999),market_markers=marks.get(gid,0),document_hint='broad codebook path' if BOOK.search(path) and not NARROW.search(path) else 'energy-specific path' if NARROW.search(path) else 'other path'))
        if acc!=a['data_rows_with_state_and_feature']:raise ValueError(f'{tech}: row count drift {acc}')
        aud[tech]=dict(feature_rows=acc,distinct_source_geography_groups=len(grouped),sha256=sha)
    with CSV.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    cnt=lambda k:dict(collections.Counter(r[k] for r in rows));ids={r['geoid'] for r in rows if r['geoid']};valid=[r for r in rows if r['url']]
    c.dump(AUDIT,dict(catalog_as_of='2026-11-15',census_vintage=2025,release_counts=aud,original_feature_rows=sum(int(x['feature_rows']) for x in rows),source_geography_technology_groups=len(rows),nonempty_url_groups=len(valid),unique_urls=len({r['url'] for r in valid}),census_ids_seen=len(ids),geography_status_group_counts=cnt('match'),url_attribution_group_counts=cnt('url_authority'),methodology='One row per technology and original jurisdiction fields, original code and URL. Row ranges refer to 1-based Excel rows. Matching is exact FIPS with compatible Census layer, independent state and name confirmation; statistical geographies remain authority-unconfirmed. No aggregation of technology outcomes into data center law.'))
    return rows
def screen(rows,fetch,limit,workers):
    import ordinances.codebooks.inventory as books
    # Isolate this run before calling the shared scanner. Do not overwrite its directory or index.
    oldjobs=books.JOBS;oldfiles=books.FILES; checks=CACHE/'checks'; files=CACHE/'files'
    if not fetch and not checks.exists():return
    checks.mkdir(exist_ok=True,parents=True);files.mkdir(exist_ok=True,parents=True)
    oldhashes={p.stem for p in oldjobs.glob('*.json')}
    groups=collections.defaultdict(list)
    for r in rows:
        if r['state']=='MO' or not r['geoid'] or not r['url'] or r['census_layer'] not in ('counties','place','cousubs') or not GOVDOC.search(r['url']):continue
        if r['url_authority'] not in ('linked government codebook referral','matched jurisdiction website host','government host: issuing scope unverified'):continue
        # A filename about a specific energy technology is not a general-code lead.
        if r['document_hint']!='broad codebook path':continue
        groups[r['url']].append(r)
    def order(u):
        rs=groups[u];r=min(rs,key=lambda v:(int(v['state_rank']),-int(v['market_markers']),v['geoid']))
        return (int(r['state_rank']),-max(int(v['market_markers']) for v in rs),all(v['url_authority']=='government host: issuing scope unverified' for v in rs),-len({v['technology'] for v in rs}),u)
    # Separate the government-hosted candidate queue from the all-source crosswalk.
    with (D/'compass_code_sources_queue.csv').open('w',newline='') as f:
        fields=('priority','url','referred_geoids','states','technologies','authority_basis','market_markers','prior_codebook_url_check','same_host_jurisdiction_or_verified_referral')
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for rank,u in enumerate(sorted(groups,key=order),1):
            rs=groups[u];w.writerow(dict(priority=rank,url=u,referred_geoids=';'.join(sorted({r['geoid'] for r in rs})),states=';'.join(sorted({r['state'] for r in rs})),technologies=';'.join(sorted({r['technology'] for r in rs})),authority_basis=';'.join(sorted({r['url_authority'] for r in rs})),market_markers=max(int(r['market_markers']) for r in rs),prior_codebook_url_check=c.digest(u.encode()) in oldhashes,same_host_jurisdiction_or_verified_referral=any(r['url_authority']!='government host: issuing scope unverified' for r in rs)))
    queue=CACHE/'initial_cohort.json';previous=c.read(queue,[])
    if fetch and not previous:
        todo=[u for u in sorted(groups,key=order) if c.digest(u.encode()) not in oldhashes]
        # Rotation through ranked states avoids letting all scans land in one state.
        per=collections.defaultdict(list)
        for u in todo:per[groups[u][0]['state']].append(u)
        labels=sorted(per,key=lambda st:(int(groups[per[st][0]][0]['state_rank']),st));seenhosts=collections.Counter();seengeo=collections.Counter();jobs=[]
        for roundno in range(max([len(v) for v in per.values()]+[0])):
            for st in labels:
                if roundno>=len(per[st]):continue
                u=per[st][roundno];gid=groups[u][0]['geoid'];hn=host(u)
                if seenhosts[hn]>=2 or seengeo[gid]>=2:continue
                jobs.append(u);seenhosts[hn]+=1;seengeo[gid]+=1
                if len(jobs)>=limit:break
            if len(jobs)>=limit:break
        previous=[dict(url=u,referrals=sorted({(r['state'],r['geoid'],r['census_name'],r['technology']) for r in groups[u]}),authority_basis=sorted({r['url_authority'] for r in groups[u]}),market_markers=max(int(r['market_markers']) for r in groups[u])) for u in jobs]
        c.dump(queue,previous)
    try:
        books.JOBS=checks;books.FILES=files
        if fetch:
            with ThreadPoolExecutor(max_workers=workers) as pool:list(pool.map(books.check,[r['url'] for r in previous if not(checks/(c.digest(r['url'].encode())+'.json')).exists()]))
    finally:books.JOBS=oldjobs;books.FILES=oldfiles
    results=[];ct=collections.Counter()
    for seed in previous:
        u=seed['url'];r=c.read(checks/(c.digest(u.encode())+'.json'),{})
        status='not yet scanned' if not r else 'unreadable or blocked' if r.get('error') else 'no machine-readable pages' if not r.get('text_pages') else 'candidate text' if r['hits'] else 'no matching text in readable pages'
        ct[status]+=1;results.append(dict(**seed,screen_result=status,duplicate_content_in_shared_pdf_scan=bool(r.get('sha256') and (oldfiles/(r['sha256']+'.pdf')).exists()),source_check=r))
    c.dump(SCREEN,dict(cohort_size=len(previous),eligible_distinct_urls=len(groups),results=ct,documents=results,scope='Only matched, non-statistical Census local geographies. Selected source path resembles a general codebook; attributable host does not establish enactment. Source scanner reads up to 18 MiB and respects robots. Text hits are candidates, not legal findings. A state name is scoped to the cited upstream record. Missouri excluded by request.'))
    print('Screen:',dict(ct),flush=True)
def stage_claims():
    """Only human-authored claims from a pinned hit are eligible; independent output manifest."""
    import os, fitz
    raw=c.read(D/'compass_code_sources_claims.json',[]);docs={};seen=set()
    reviewed={r['url']:r for r in c.read(SCREEN,{})['documents'] if r['screen_result']=='candidate text'}
    for claim in raw:
        if claim['id'] in seen:raise ValueError('duplicate claim')
        seen.add(claim['id']);u=claim['url'];s=claim['sha256'];z=reviewed[u]
        if z['source_check']['sha256']!=s or not any((g[0],g[1])==(claim['state'],claim['geoid']) for g in z['referrals']):raise ValueError('source linkage mismatch')
        p=CACHE/'files'/(s+'.pdf')
        with fitz.open(p) as doc:
            if c.norm(claim['evidence']) not in c.norm(doc[claim['page']-1].get_text()):raise ValueError('claim evidence missing: '+claim['id'])
            if u in docs:continue
            if c.digest(p.read_bytes())!=s:raise ValueError('source file hash mismatch')
            t='\n'.join(f'[Page {n}]\n'+pg.get_text() for n,pg in enumerate(doc,1))
        dst=c.CACHE/(s+'.bin')
        if not dst.exists():
            try:os.link(p,dst)
            except OSError:dst.write_bytes(p.read_bytes())
        assert c.digest(dst.read_bytes())==s
        tp=c.CACHE/(s+'.txt')
        if not tp.exists():tp.write_text(t)
        t=tp.read_text()
        if c.norm(claim['evidence']) not in c.norm(t):raise ValueError('conflicting extraction of existing source')
        lp=c.CACHE/(s+'.links.json')
        if not lp.exists():c.dump(lp,[])
        docs[c.address(u)]=dict(url=c.address(u),resolved=z['source_check'].get('resolved') or u,sha256=s,text_sha256=c.digest(t.encode()),adapter='pdf',bytes=dst.stat().st_size,fetched_at=z['source_check']['checked'])
    c.dump(CACHE/'reviewed_index.json',docs)
    c.dump(D/'compass_code_sources_rules.json',[{k:v for k,v in r.items() if k not in ('page','sha256')} for r in raw])
    print('Original-verified reviewed provisions:',len(raw))
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--screen',action='store_true',help='Rebuild candidate report from existing frozen first cohort');ap.add_argument('--fetch',action='store_true',help='Actually scan bounded initial cohort; same cohort on repeat');ap.add_argument('--limit',type=int,default=72,help='First cohort size (1–200); pinned thereafter');ap.add_argument('--workers',type=int,default=6);ap.add_argument('--reuse-export',action='store_true');ap.add_argument('--claims',action='store_true',help='Validate hand-authored PDF claims and write sidecar index for publication')
    a=ap.parse_args()
    if not 1<=a.limit<=200 or not 1<=a.workers<=10:ap.error('Bound scan size to 1–200, workers 1–10')
    rows=read(CSV) if a.reuse_export else export()
    print('Source groups:',len(rows),flush=True)
    if a.fetch or a.screen:screen(rows,a.fetch,a.limit,a.workers)
    if a.claims:stage_claims()
if __name__=='__main__':main()
