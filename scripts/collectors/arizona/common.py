"""Arizona shared helpers: configuration, source snapshot session, the per-layer GIS download and the row-scanning loop
used by the issuer modules (Mesa, Phoenix, Maricopa County, Tempe, Tucson, ADEQ)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
from lib.text import date
import lib.net as netfetch
import argparse, csv, gzip, hashlib, io, json, re, time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request
import lib.files, lib.net, lib.terms, lib.text, lib.geo
R=Path(__file__).resolve().parents[3]; C=R/'cache/history/az'; D=R/'data'
conf=json.loads((collector_data('arizona','config.json')).read_text()); ASOF=conf['cutoff']
manifest=collector_data('arizona','manifest.json'); OUT=series_path('az')
WATER=('storm_old','demin_old','industrial_old','storm','demin','industrial')
GIS=('phoenix_plan','phoenix_permit','air','tempe','tucson')+WATER
labels={'mesa':'Mesa building permit register','phoenix_plan':'Phoenix plan reviews','phoenix_permit':'Phoenix permits','air':'Maricopa County air permit register','tempe':'Tempe building safety permits','tucson':'Tucson commercial building permits','accela':'City citizen access record','case':'Chandler city council zoning decisions'}
rx=re.compile(r'\b(?:data[\s/-]*(?:(?:computer\s+)?cent(?:er|re)s?|(?:server\s+)?halls?)|server[\s/-]*farms?)\b',re.I)
def match(s):return rx.search(re.sub(r'(?<=[a-z])(?=[A-Z])',' ',s))
def js(b):return json.loads(b)
def session():
    """Opens the snapshot directory and returns (m, queries, save, query): file manifest, candidate counts, and the two writers."""
    C.mkdir(exist_ok=True,parents=True);m={};queries={}
    def save(key,url,b):
        name=key
        if name.endswith('.gz'):b=gzip.compress(b,mtime=0)
        (C/name).write_bytes(b);m[name]={'url':url,'sha256':lib.files.sha(b),'bytes':len(b)}
    def query(key,url,params):
        full=url+'?'+urlencode(params);b=lib.net.req(url,params);res=js(b)
        if isinstance(res,dict) and res.get('error'):raise RuntimeError((key,res['error']))
        save(key,full,b);return res
    return m,queries,save,query
def gis_layer(k,query,queries):
    """Download one ArcGIS layer's screened records (ids first, then batched attribute queries)."""
    x=conf[k];url=x['url']+'/query';w=lib.terms.patterns(x['search'],'UPPER')
    # Unlike a bare objectIds query, retaining WHERE avoids Maricopa's physical/virtual OID mismatch.
    if k in WATER:w="("+w+") OR (UPPER(FACILITY_NAME) LIKE '%PROJECT BLUE%' AND UPPER(CITY) LIKE '%TUCSON%') OR (UPPER(FACILITY_NAME) LIKE '%PHX73%' AND UPPER(CITY) LIKE '%GOODYEAR%')"
    a=query(k+'-ids.json.gz',url,{'where':w,'returnIdsOnly':'true','f':'json'});ids=sorted(a['objectIds'] or []);assert a['objectIdFieldName'].lower()==x['oid'].lower()
    physical=[]
    if k=='air':
        check=query('air-stable.json.gz',url,{'where':w,'outFields':'OBJECTID,facility_id,permit_nbr','returnGeometry':'false','f':'json'})
        physical=sorted((el['attributes']['OBJECTID'],el['attributes']['facility_id'],el['attributes']['permit_nbr'] or '') for el in check['features'])
    batch=(len(ids) or 1) if k=="air" else 120
    for start in range(0,len(ids),batch):
        pack=ids[start:start+batch];cond=w if k=='air' else '('+w+') AND '+x['oid']+' IN ('+','.join(map(str,pack))+')'
        result=query(f'{k}-{start}.json.gz',url,{'where':cond,'outFields':x['fields'],'returnGeometry':'false','f':'json'});got=[v['attributes'][x['oid']] for v in result['features']]
        if k=='air':
            assert len(got)==len(pack) and physical==sorted((el['attributes']['OBJECTID'],el['attributes']['facility_id'],el['attributes']['permit_nbr'] or '') for el in result['features'])
        else:assert sorted(got)==pack,(k,'coverage',len(got),len(pack))
    queries[k]=len(ids);print(k,len(ids),flush=True)
class Build:
    """State shared by every source while rows are built: verified archive manifest, output rows, exclusions, counters."""
    def __init__(self):
        self.meta=js(manifest.read_bytes());self.m=self.meta['files'];self.rows={};self.reject=[];self.stats=Counter();self.mesa_seen={};self.phx_seen={}
        for n,f in self.m.items():
            if lib.files.sha((C/n).read_bytes())!=f['sha256']:raise ValueError('Archive hash mismatch: '+n)
    def archived(self,n):return js(gzip.decompress((C/n).read_bytes()))
    def add(self,k,n,no,project,kind,status,dt,role,loc,url,locator,detail,key=None,source=None):
        m=self.m;rows=self.rows;stats=self.stats
        if dt and dt>ASOF:stats['future events']+=1;return
        natural=key or no
        id_='az-'+k+'-'+quote(str(natural),safe='')
        if id_ in rows:raise ValueError(('Duplicate natural key',id_))
        assert all([no,project,kind,status,role,loc,url,locator])
        assert not dt or dt>'1960-01-01',(no,dt)
        rows[id_]=dict(id=id_,state='AZ',dataset=labels.get(k,k),jurisdiction=loc,record_no=str(no),project=project,kind=kind,status=status,date=dt,date_role=role,url=url,source_url=source or conf.get(k,{}).get('url',url),locator=locator,source_sha256=m[n]['sha256'],details={**detail,'archive':'cache/history/az/'+n})
def scan(b,k,branch):
    """Walk one layer's archived pages, reject rows without an explicit data-center/project match, and hand the rest to branch()."""
    m=b.m;meta=b.meta;reject=b.reject
    x=conf[k];seen=[]
    for n in sorted(m):
        if not re.fullmatch(k+r'-\d+\.json\.gz',n):continue
        j=b.archived(n);arr=j if k=='mesa' else [v['attributes'] for v in j['features']]
        for a in arr:
            oid=a['src_id'] if k=='mesa' else a[x['oid']];seen.append(oid);fields=x['search'] if k!='air' else ['facility_nm','facility_desc']
            txt=' | '.join(str(a.get(f) or '') for f in fields)
            hit=match(txt);alias=None
            if k in WATER and not hit:
                if re.search('PROJECT BLUE',txt,re.I) and str(a['CITY']).upper()=='TUCSON':alias='County Project Blue FAQ'
                if re.search(r'\bPHX73\b',txt,re.I) and str(a['CITY']).upper()=='GOODYEAR':alias='City of Goodyear B26-01057'
            if not (hit or alias):reject.append([k,str(oid),'No explicit facility/project/scope match']);continue
            evidence={'matched_text':hit.group() if hit else alias}
            branch(b,k,n,x,a,oid,evidence)
    assert len(seen)==len(set(seen))==meta['candidate_counts'][k],(k,len(seen),meta['candidate_counts'][k])
    if k in GIS and k!='air':assert sorted(seen)==sorted(b.archived(k+'-ids.json.gz')['objectIds'] or [])
    if k=='air':
        natural=lambda a:(a['OBJECTID'],a['facility_id'],a['permit_nbr'] or '')
        assert sorted(natural(z['attributes']) for z in b.archived('air-stable.json.gz')['features'])==sorted(natural(z['attributes']) for z in b.archived('air-0.json.gz')['features'])
