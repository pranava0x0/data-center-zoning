"""National USACE ORM public search; replay reviewed actions and notices without network by default."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path, collector_data, R
import lib.net as netfetch
import argparse, collections, csv, datetime as dt, gzip, hashlib, io, json, re, sys
from pathlib import Path
from urllib.parse import urlencode,urlparse
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from lib.archive import Store
from lib.files import j
from lib.text import htmltext
from lib.geo import pinring
import lib.discovery as collect

S=Store('CORPS');BASE='https://permits.ops.usace.army.mil/orm-public-api/permits/search'
QUERIES=('data center','data centers','datacenter','datacenters','data centre','data-center','server farm','server campus','hyperscale','colocation','data processing center','cloud computing center','cloud computing campus','Amazon','Microsoft','Google','QTS','Equinix','Vantage Data','Meta Platforms','EdgeConneX','CyrusOne','Digital Realty','STACK Infrastructure','CloudHQ','Aligned Data','Switch Datacenters','Compass Datacenters')
WORDS=re.compile(r'\b(?:data[\s-]*(?:cent(?:er|re)s?)|server[\s-]+farms?|data[\s-]+processing[\s-]+centers?)\b',re.I)
DS='US Army Corps of Engineers regulatory public actions';PN='US Army Corps of Engineers district public notices'
def encoded(**p):return BASE+'?'+urlencode(p)
def h(o):return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def pages(q,scope,step=200):
    result=[];n=0
    while True:
        ref=S.get(encoded(q=q,max=step,start=n,**{scope:'true'}));p=S.read(ref);rows=p['results']['features']
        result.append(ref);n+=len(rows)
        if n==p['total']:return result
        if n>p['total'] or not rows:raise ValueError('Pagination mismatch: '+q)
def unpack(pg):
    for r in pg:
        for f in S.read(r)['results']['features']:yield f,r
def fetch_queries():
    p=collector_data('federal/usace_regulatory','queries.json');m=j(p) if p.exists() else {}
    for t in QUERIES:
        if t not in m:m[t]=pages('"'+t+'"','da');collect.dump(p,m)
    return m
def fetch_cases():
    q=fetch_queries();p=collector_data('federal/usace_regulatory','cases.json');m=j(p) if p.exists() else {};known=j(collector_data('federal/usace_regulatory','district.json'))
    ids={f['properties']['identifier'] for ps in q.values() for f,_ in unpack(ps) if WORDS.search(f['properties'].get('projectName',''))}
    ids.update(known)
    for k in sorted(ids):
        if k not in m:m[k]=pages('identifier:"'+k+'"','sa');collect.dump(p,m)
    return m
RRS='https://rrs.usace.army.mil/api/publicnotice/'
def rrs_post(params):
    from urllib.request import Request,urlopen
    url=RRS+'getPublicNotices'
    raw=netfetch.request(url,json_body=params,timeout=150,limit=16*1024*1024).body
    d=json.loads(raw)
    if len(raw)>16*1024*1024 or d.get('status')!='Success':raise ValueError('RRS list retrieval failed: '+str(d.get('msg')))
    z=hashlib.sha256(raw).hexdigest();target=S.d/(z+'.json.gz')
    if not target.exists():target.write_bytes(gzip.compress(raw,mtime=0))
    return dict(url=url,ext='json',bytes=len(raw),sha256=z,method='POST',body=params)
def fetch_rrs():
    p=collector_data('federal/usace_regulatory','rrs.json');m=j(p) if p.exists() else {}
    for q in ('','data center','datacenter','data centre','server farm','hyperscale','server campus','data processing center'):
        if q in m:continue
        result=[];ids=set();i=1
        while True:
            ref=rrs_post(dict(districtCodes=[],states=[],itemsPerPage=100,pageNumber=i,searchText=q,sortColumn='',sortOrder='desc'));data=S.read(ref)['data'];result.append(ref)
            page=data['publicNotices'];ids.update(x['publicNoticeID'] for x in page)
            if len(ids)==data['totalFilteredCount']:break
            if not page or i>300:raise ValueError('RRS pagination mismatch')
            i+=1
        m[q]=result;collect.dump(p,m)
    return m
def rrs_list(m):
    allr={}
    for pageset in m.values():
        for p in pageset:
            for z in S.read(p)['data']['publicNotices']:allr[z['publicNoticeID']]=z
    return allr
def fetch_docs(casepages):
    from urllib.parse import quote
    p=collector_data('federal/usace_regulatory','documents.json');m=j(p) if p.exists() else {}
    for v in casepages.values():
        for f,_ in unpack(v):
            a=f['properties'];url=a.get('ajdUrl','').strip()
            if not url or url in m:continue
            gov=(urlparse(url).hostname or '').lower()
            if not gov.endswith('.usace.army.mil'):continue
            try:
                ref=S.get(quote(url,safe=':/?=&%#;,+'),'pdf')
                if b'%PDF-' not in S.read(ref)[:1024]:raise ValueError('Not PDF')
                m[url]=ref
            except (OSError,ValueError) as e:m[url]=dict(url=url,error=str(e))
            collect.dump(p,m)
    return m
TIGER='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query'
def pointkey(pt):return ','.join(str(x) for x in pt[:2])
def fetch_geo(m):
    p=collector_data('federal/usace_regulatory','geo.json');g=j(p) if p.exists() else {}
    for ps in m.values():
        for f,_ in unpack(ps):
            pt=f.get('geometry',{}).get('coordinates',[])
            if len(pt)!=2:continue
            k=pointkey(pt)
            if k not in g:
                u=TIGER+'?'+urlencode(dict(f='json',geometry=k,geometryType='esriGeometryPoint',inSR=4326,spatialRel='esriSpatialRelIntersects',outFields='STATE,COUNTY,GEOID,NAME',returnGeometry='false'))
                g[k]=S.get(u);collect.dump(p,g)
    return g
def from_dates(value):
    if not value or value in ('N/A','NA'):return None
    for fmt in ('%m/%d/%Y','%d-%b-%Y','%Y%m%d','%Y-%m-%d'):
        try:return dt.datetime.strptime(value[:10],fmt).date().isoformat()
        except ValueError:continue
    raise ValueError('Unknown date '+value)
def dates(a):
    typ=a['vtype']
    if typ=='pending':return from_dates(a.get('dateReceived')),'application received date'
    if typ=='nepa_ea':
        if a.get('finalEaPublicationDate'):return from_dates(a['finalEaPublicationDate']),'final EA publication date'
        if a.get('pnDate'):return from_dates(a['pnDate']),'public notice date associated with EA'
        return None,'date unavailable'
    return from_dates(a.get('displayDate') or a.get('vdate')),'final regulatory action date' if typ!='jds' else 'jurisdictional determination date'
def facts(a):
    v=a['vtype']
    if v=='jds':return 'Approved jurisdictional determination','Approved jurisdictional determination'
    if v=='nepa_ea':return 'Environmental assessment',a.get('pendingOrFinal') or a.get('ormPendingOrFinal')
    if v=='pending':return a.get('permitType') or 'Permit application','Pending'
    if v in ('issued','wrda','emergency'):return a.get('permitType') or 'Regulatory action',a.get('actionTaken') or v
    raise ValueError('Unmapped federal action: '+v)
def validstates():
    p=R/'cache/geo/state.zip';ref=next(x for x in j(R/'data/geography_sources.json')['sources'] if x['file']=='cache/geo/state.zip')
    if hashlib.sha256(p.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('State gazetteer hash mismatch')
    with ZipFile(p) as z: return {v['GEOID']:v['USPS'] for v in csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode()),delimiter='|')}
def district_notices(rrsm):
    p=collector_data('federal/usace_regulatory','district.json');m=j(p) if p.exists() else {}
    for n,z in rrs_list(rrsm).items():
        if not WORDS.search(' '.join(str(z.get(k) or '') for k in ('description','keywords','projectName'))):continue
        if z['daNumber'] not in m:m[z['daNumber']]=dict(notice_id=n,notice=S.get(RRS+'getPublicNotice?'+urlencode(dict(id=n))));collect.dump(p,m)
    return m
def fetch_rrsfiles(m):
    p=collector_data('federal/usace_regulatory','rrs_documents.json');refs=j(p) if p.exists() else {}
    for z in m.values():
        for u in S.read(z['notice'])['data'].get('urls') or []:
            if u in refs or not urlparse(u).hostname.endswith('.usace.army.mil'):continue
            try:
                ref=S.get(u,'pdf')
                if b'%PDF-' not in S.read(ref)[:1024]:raise ValueError('Not a PDF')
                refs[u]=ref
            except (OSError,ValueError) as e:refs[u]=dict(url=u,error=str(e))
            collect.dump(p,refs)
    return refs
def build():
    queries=j(collector_data('federal/usace_regulatory','queries.json'));cases=j(collector_data('federal/usace_regulatory','cases.json'));district=j(collector_data('federal/usace_regulatory','district.json'));rrs=j(collector_data('federal/usace_regulatory','rrs.json'));geo=j(collector_data('federal/usace_regulatory','geo.json'));docs=j(collector_data('federal/usace_regulatory','documents.json'));rrsfiles=j(collector_data('federal/usace_regulatory','rrs_documents.json'));states=validstates()
    # A file result is a search artifact. Use per-file action pages, not search-hit totals, for publication.
    candidates={};expected=set(district)
    for term,ps in queries.items():
        for f,_ in unpack(ps):
            a=f['properties'];ident=a['identifier'];candidates.setdefault(ident,a.get('projectName') or '')
            if WORDS.search(a.get('projectName','')):expected.add(ident)
    if set(cases)!=expected:raise ValueError('File set and discovery manifest differ')
    out={};held={k:{'project':n,'reason':'Operator or search-word match without reviewed positive project scope.'} for k,n in candidates.items() if k not in expected};skipped=[];rawcount=0;equiv=0;seen=collections.Counter()
    def add(z):
        nonlocal equiv
        if z['id'] in out:equiv+=1;return
        out[z['id']]=z
    for key,ps in cases.items():
        if len({S.read(v)['total'] for v in ps})!=1 or sum(1 for _ in unpack(ps))!=S.read(ps[0])['total']:raise ValueError('Incomplete case '+key)
        for f,ref in unpack(ps):
            rawcount+=1;a=f['properties']
            if a.get('identifier')!=key or a.get('dtype')!='ACTION':raise ValueError('Wrong scope of ORM response')
            pt=f['geometry']['coordinates'];g=geo[pointkey(pt)];gs=S.read(g)['features']
            if len(gs)!=1:skipped.append({'case':key,'reason':'Ambiguous/unavailable TIGER geography'});continue
            county=gs[0]['attributes'];st=states[county['STATE']];kind,status=facts(a);date,role=dates(a)
            if date and date>'2026-11-16':skipped.append({'case':key,'reason':'Date beyond snapshot cutoff'});continue
            # Exclude generic snapshots with identical public action identity. Distinct date or document remains an event.
            identity=[key,a.get('vtype'),kind,status,date,a.get('ajdUrl',''),a.get('jdType','')]
            id='federal-corps-'+h(identity)[:24];reg=a.get('districtOfficeDescription') or a.get('district') or a.get('org')
            det=dict(source_sha256=ref['sha256'],authority='US Army Corps of Engineers',federal_issuer='US Army Corps of Engineers',corps_file=key,authority_level='federal',issuer_level='federal',orm_identifier=key,da_number=a['daNumber'],district_code=a['org'],orm_view=a['vtype'],census_county=county['NAME'],census_county_geoid=county['GEOID'],geography_basis='USACE point intersected with Census TIGERweb county; not an agency-reported county',geography_url=g['url'],geography_sha256=g['sha256'],longitude=pt[0],latitude=pt[1])
            if a.get('publicNoticeDate') not in (None,'N/A'):det['orm_public_notice_date']=a['publicNoticeDate']
            if a.get('subactions'):det['consultations']=a['subactions']
            if a.get('fEaPubDate'):det['final_ea_publication']=a['fEaPubDate']
            if key in district:
                notice=S.read(district[key]['notice'])['data']
                if len(notice['state'])==1 and notice['state'][0]==st and abs(notice['longitude']-pt[0])+abs(notice['latitude']-pt[1])<.02:det.update(county=notice['county'],county_basis='USACE district RRS notice')
            if a.get('ajdUrl'):
                url=a['ajdUrl'].strip();d=docs.get(url,{})
                if d.get('sha256'):S.read(d);det.update(document_url=d['url'],document_sha256=d['sha256'])
                elif urlparse(url).hostname and urlparse(url).hostname.endswith('.usace.army.mil'):det.update(document_url=url,document_retrieval=d.get('error','not archived'))
            seen[a.get('vtype')]+=1
            add(dict(id=id,state=st,jurisdiction='US Army Corps of Engineers — '+reg,dataset=DS,record_no=a['daNumber'],project=a['projectName'].strip(),kind=kind,status=status,date=date,date_role=role,url=ref['url'],source_url=ref['url'],locator='Army file '+key+'; ORM '+a['vtype']+' action; '+str(date or 'undated'),details=det))
    for key,v in district.items():
        ref=v['notice'];z=S.read(ref)['data'];n=z['publicNoticeID'];assert key==z['daNumber'] and len(z['state'])==1
        det=dict(source_sha256=ref['sha256'],authority='US Army Corps of Engineers',federal_issuer='US Army Corps of Engineers',corps_file=key,authority_level='federal',issuer_level='federal',orm_identifier=key,district_code=z['districtCode'],county=z['county'],county_basis='USACE RRS',comments_end=z['commentsEndDate'][:10],source_description=z['description'],notice_id=n)
        attachments=[]
        for u in z.get('urls') or []:
            d=rrsfiles.get(u,{})
            if d.get('sha256'):S.read(d);attachments.append(dict(url=d['url'],sha256=d['sha256']))
        if attachments:det['notice_documents']=attachments
        add(dict(id='federal-corps-notice-'+str(n),state=z['state'][0],jurisdiction='US Army Corps of Engineers — '+z['district'],dataset=PN,record_no=key,project=z['projectName'],kind='District public notice of proposed action',status='Public notice published',date=z['startDate'][:10],date_role='notice opening date',url=next((a['url'] for a in attachments if 'plans.pdf' not in a['url'].lower()),ref['url']),source_url=ref['url'],locator='RRS notice ID '+str(n)+'; Army file '+key,details=det))
    if not out:raise ValueError('No output')
    by=collections.defaultdict(list)
    for z in sorted(out.values(),key=lambda z:z['id']):by[z['state']].append(z)
    for st,rows in by.items():collect.dump(series_path(f'corps_{st.lower()}'),rows)
    collect.dump(collector_data('federal/usace_regulatory','held.json'),held)
    cv=dict(query_file_hits_per_term={k:sum(1 for _ in unpack(p)) for k,p in queries.items()},candidate_ids=len(candidates),reviewed_orm_queries=len(cases),reviewed_action_rows=rawcount,duplicate_public_actions=equiv,skipped=skipped,held_ids=len(held),action_views=dict(seen),public_notices_screened=len(rrs_list(rrs)),notices=len(district),archived_jd_pdfs=sum('sha256' in r for r in docs.values()),archived_notice_pdfs=sum('sha256' in r for r in rrsfiles.values()),published=len(out),by_state={k:len(v) for k,v in sorted(by.items())})
    collect.dump(collector_data('federal/usace_regulatory','coverage.json'),cv);return list(out.values()),cv
def main():
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true',help='Fetch missing national queries, files, notices, PDFs and geographic lookup pages.');a=p.parse_args()
    if a.fetch:
        rrs=fetch_rrs();d=district_notices(rrs);fetch_rrsfiles(d);m=fetch_cases();fetch_geo(m);fetch_docs(m)
    _,cv=build();print(json.dumps(cv,indent=1))
if __name__=='__main__':main()
