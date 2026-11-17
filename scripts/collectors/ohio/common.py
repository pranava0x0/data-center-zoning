"""Ohio helpers shared by the source modules: paths and config, the hash-pinned capture archive (get/read), the ArcGIS
layer search and record readers, the history-row builder, and the build loop that dispatches each layer feature and each
reviewed PDF to the issuer module that owns it."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
from lib.geo import pinring
import argparse, collections, datetime as dt, hashlib, io, json, pathlib, re
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from pypdf import PdfReader
import lib.discovery as collect, lib.arcgis as arcgis
import lib.net as netfetch
R=pathlib.Path(__file__).resolve().parents[3];DIR=R/'cache/history/oh';CONF=collector_data('ohio','config.json');MAN=collector_data('ohio','manifest.json')
OUT=series_path('oh');AUDIT=collector_data('ohio','coverage.json');RANK=collector_data('ohio','rank.json');REVIEW=collector_data('ohio','documents.json')
TZ=ZoneInfo('America/New_York')
RX=re.compile(r'\b(?:data[\s_-]*(?:processing[\s_-]+)?(?:cent(?:er|re)|ctr|hall|building)s?|server[\s_-]*farms?)\b',re.I)
def dump(p,x):collect.dump(p,x)
def sha(b):return hashlib.sha256(b).hexdigest()
def get(url,ext='json',**q):
    u=url+('?'+urlencode(dict(f='json',**q)) if q else '')
    b=netfetch.get(u,timeout=90,limit=36*1024*1024)
    if ext=='pdf':
        if not b.startswith(b'%PDF'):raise ValueError('Not PDF: '+u)
    elif 'error' in json.loads(b):raise ValueError(str(json.loads(b)['error']))
    DIR.mkdir(parents=True,exist_ok=True);k=sha(b);path=DIR/(k+'.'+ext)
    if not path.exists():path.write_bytes(b)
    return {'url':u,'sha256':k,'bytes':len(b),'ext':ext}
def read(r,binary=False):
    b=(DIR/(r['sha256']+'.'+r['ext'])).read_bytes()
    if sha(b)!=r['sha256'] or len(b)!=r['bytes']:raise ValueError('Failed archive integrity: '+r['url'])
    return b if binary else json.loads(b)
def wq(l,c):
    return ' OR '.join(f"UPPER({field}) LIKE '{term}'" for field in l['lex'] for term in c['terms']+['%'+a+'%' for a in l.get('aliases',[])])
def pull(url,sql,fields,oid='OBJECTID'):return arcgis.pull(get,read,url,sql,fields,oid,batch=150)
def records(p):return [(a,b['sha256']) for a,b in arcgis.records(read,p,with_ref=True)]
def hits(a,l):return {field:str(a[field]) for field in l['lex'] if RX.search(str(a.get(field) or ''))}
def new_manifest(c):
    return {'config_sha256':sha(CONF.read_bytes()),'captured_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'layers':{},'docs':{},'joins':[]}
def fetch_layer(c,m,k,l):
    url=l['url'];meta=get(url+'?f=json');schema=read(meta)
    if not set(l['fields'].split(','))<={f['name'] for f in schema['fields']}:raise ValueError('Field mappings out of date')
    m['layers'][k]={'meta':meta,'all_use':get(url+'/query',where='1=1',returnCountOnly='true'),'screen':pull(url,wq(l,c),l['fields'],l.get('oid','OBJECTID'))}
    print(k,'screen',len(records(m['layers'][k]['screen'])),flush=True)
def cal(ms):
    return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).astimezone(TZ).date().isoformat() if ms is not None else None
def recordurl(u,n):return u+'/query?'+urlencode(dict(where='OBJECTID='+str(n),outFields='*',returnGeometry='false',f='pjson'))
def keyurl(u,field,value):
    """Stable record link: query the layer by the issuer's identifier field, never by the portal's row number."""
    v=str(value) if isinstance(value,int) else "'"+str(value).replace("'","''")+"'"
    return u+'/query?'+urlencode(dict(where=field+'='+v,outFields='*',returnGeometry='false',f='pjson'))
def tidy(s):return ' '.join(str(s or '').upper().split())
def normpdf(x):return ' '.join(str(x).split()).replace('–','-').casefold()
def add_document(add,r,ref,dataset,county):
    """Publish one reviewed PDF decision as a history row (the issuer module supplies its dataset label and county)."""
    add('doc-'+r['record_no'],dataset,r['jurisdiction'],r['record_no'],r['project'],r['kind'],r['status'],r['date'],r['date_role'],ref['url']+'#page='+str(r['pages'][0]),'PDF pp. '+', '.join(map(str,r['pages']))+'; '+r['record_no'],ref['url'],ref['sha256'],{'authority':r['authority'],'county':county,'notes':r['notes'],'anchors':r['anchors'],'review':'visually checked pinned scanned page' if r['reviewed_hash'] else 'number/date/outcome checked in pinned pages'})
def build(c,m,geo,layers,portal,docs):
    """geo: ranking module; layers: {layer key: module with row()}; portal: module with portal_rows(); docs: {doc key: module with add_record()}."""
    if m['config_sha256']!=sha(CONF.read_bytes()):raise ValueError('Config and capture mismatch')
    geo.rankings(m)
    rows=[];audit={'sources':{},'held':[],'duplicates':[]};seen={}
    def add(key,dataset,city,num,project,kind,status,date,role,url,locator,source,hashref,details):
        if date and dt.date.fromisoformat(date)>dt.date.fromisoformat(c['cutoff']):audit['held'].append({'source':dataset,'number':num,'reason':'post-cutoff date'});return
        if key in seen:raise ValueError('Duplicate history key: '+key)
        seen[key]=1
        rows.append(dict(id='oh-'+key,state='OH',dataset=dataset,jurisdiction=city,record_no=str(num),project=project or '(not named)',kind=kind,status=status or 'Not reported',date=date,date_role=role,url=url,locator=locator,source_url=source,source_sha256=hashref,details=details))
    state={'eng':[],'npseen':{},'npkeys':set()}
    for k,l in c['layers'].items():
        block=m['layers'][k];meta=read(block['meta']);entries=records(block['screen'])
        audit['sources'][k]={'all_use_rows':read(block['all_use'])['count'],'screen_candidates':len(entries),'strict_phrase_rows':sum(bool(hits(a,l)) for a,_ in entries),'url':l['url'],'predicate':block['screen']['where']}
        for a,h0 in entries:
            hh=hits(a,l);oid=a[l.get('oid','OBJECTID')];url=recordurl(l['url'],oid)
            if not hh:audit['held'].append({'source':k,'object_id':oid,'reason':'loose SQL or operator-only hit'});continue
            layers[k].row(add,audit,state,k,l,meta,a,h0,hh,oid,url)
    portal.portal_rows(c,m,add,audit,state['eng'])
    for r in json.loads(REVIEW.read_text()):
        ref=m['docs'][r['doc']];raw=read(ref,True);pdf=PdfReader(io.BytesIO(raw));content=' '.join(pdf.pages[i-1].extract_text() or '' for i in r['pages'])
        if r['reviewed_hash']:
            if sha(raw)!=r['reviewed_hash']:raise ValueError('Scanned decision changed; visual review required')
        elif any(normpdf(a) not in normpdf(content) for a in r['anchors']):raise ValueError('PDF evidence drift: '+r['record_no'])
        docs[r['doc']].add_record(add,r,ref)
    audit.update(as_of=c['cutoff'],rows=len(rows),by_dataset=dict(collections.Counter(r['dataset'] for r in rows)),by_jurisdiction=dict(collections.Counter(r['jurisdiction'] for r in rows)))
    dump(OUT,sorted(rows,key=lambda r:(r['date'] or '',r['id'])));dump(AUDIT,audit)
    print('Wrote',len(rows),'OH records:',audit['by_dataset'])
