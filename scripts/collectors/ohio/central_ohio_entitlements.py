"""Central Ohio local entitlements; bounded primary-source capture and default offline replay."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import lib.net as netfetch
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import argparse, json, re
import lib.discovery as c
ROOT=c.R;D=ROOT/'data/national';C=ROOT/'cache/history/metropriority';OUT=series_path('metropriority_oh')
BASE='https://webgis.newalbanyohio.org/arcgis/rest/services/PublicZoning/ZoningEntitlementsBoardsCommissions/MapServer/0'
NA='New Albany verified campus zoning actions';HI='Hilliard campus board decisions';TZ=ZoneInfo('America/New_York')
def api(**kw):return BASE+'/query?'+urlencode(dict(f='json',returnGeometry='false',**kw))
def fetch(only_new=False):
    C.mkdir(parents=True,exist_ok=True);idx=c.read(C/'manifest.json',{}) if only_new else {};config=c.read(D/'metropriority_sources.json',{})
    urls=dict(config,na=api(where='1=1',outFields='*'),ids=api(where='1=1',returnIdsOnly='true'),schema=BASE+'?f=json')
    for k,url in urls.items():
        if only_new and k in idx:continue
        print(k,flush=True)
        resp=netfetch.request(url,timeout=30,limit=80*1024*1024);raw=resp.body;mime=resp.mime
        assert len(raw)<=80*1024*1024, k
        h=c.digest(raw);suffix='pdf' if k in config else 'json';(C/(h+'.'+suffix)).write_bytes(raw)
        if suffix=='pdf':
            assert raw.startswith(b'%PDF');_,txt,_=c.parse(raw,mime,url);(C/(h+'.txt')).write_text(txt)
        else:assert not json.loads(raw).get('error')
        idx[k]=dict(url=url,sha256=h,format=suffix,bytes=len(raw),captured=c.now())
        if suffix=='pdf':idx[k]['text_sha256']=c.digest(txt.encode())
        print(k,len(raw),flush=True)
    c.dump(C/'manifest.json',idx)
def load(ix,k):
    d=ix[k];h=d['sha256'];b=(C/(h+'.'+d['format'])).read_bytes();assert c.digest(b)==h
    if d['format']=='json':return json.loads(b)
    s=(C/(h+'.txt')).read_bytes();assert c.digest(s)==d['text_sha256'];return s.decode()
def day(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).astimezone(TZ).date().isoformat() if ms else None

def proof(ix,ref):
    k,n,words=ref
    s=re.split(r'\[Page \d+\]',load(ix,k))[n]
    assert c.norm(words) in c.norm(s),(k,n,words)
    return dict(url=ix[k]['url']+'#page='+str(n),sha256=ix[k]['sha256'],page=n,evidence=words)
def build():
    ix=c.read(C/'manifest.json',{});rows=[];gis=load(ix,'na');ids=load(ix,'ids')['objectIds']
    byid={x['attributes']['OBJECTID']:x['attributes'] for x in gis['features']};assert set(ids)==set(byid) and len(byid)==len(ids) and not gis.get('exceededTransferLimit')
    schemas={z['name']:z for z in load(ix,'schema')['fields']}
    old={r['record_no'] for r in c.read(series_path('oh'),[]) if r['jurisdiction'] in ['Hilliard','New Albany']}
    data=c.read(D/'metropriority_cases.json',[])
    for z in data:
        nm=z['record_no'];assert nm not in old
        e=[proof(ix,ref) for ref in z['evidence']];k=z['source'];r=dict(id='metropriority-oh-'+z['key'],state='OH',record_no=nm,project=z['project'],kind=z['kind'],status=z['status'])
        dt=dict(issuer_level='city',authority=z['authority'],scope=z['scope'],evidence_refs=e,county=z['county'])
        if z.get('visual_scope'):
            v=z['visual_scope'];assert ix[v['key']]['sha256']==v['sha256'];dt['visual_scope']=v
        if z.get('oid'):
            a=byid[z['oid']];assert nm==a['CaseNumber'];f=z['board']+'Status';d=z['board']+'HearingDate'
            labels={x['code']:x['name'] for x in schemas[f]['domain']['codedValues']};assert labels[a[f]]=='Approved'
            title=a['Name'];assert title==z['gis_name'];dt.update(gis_outcome=labels[a[f]],gis_date_field=d,gis_raw_case_date=day(a['AdoptionDate']),city_register_case=nm,event_role=z['key'],permit_family=z.get('family'))
            u=api(where='OBJECTID='+str(a['OBJECTID']),outFields='*');dt['gis_url']=u;dt['gis_sha256']=ix['na']['sha256']
            pk=next((v for v in e if v['url'].startswith(ix[k]['url']+'#')),None)
            r.update(jurisdiction='New Albany',dataset=NA,date=day(a[d]),date_role=z['date_role'],url=u if z['primary_gis'] else pk['url'],source_url=ix[k]['url'] if z['primary_gis'] else u,source_sha256=ix['na']['sha256'] if z['primary_gis'] else pk['sha256'],locator='Boards register '+nm+', '+f+' and '+d+'; '+z['locator'])
        else:
            dt.update(event_role=z['key'],county_source_url=ix['h-charter']['url'])
            assert 'hilliard, in franklin county' in c.norm(load(ix,'h-charter'))
            r.update(jurisdiction='Hilliard',dataset=HI,date=z['date'],date_role='board meeting vote date',url=ix[k]['url']+'#page='+str(z['vote_page']),source_url=ix[k]['url'],source_sha256=ix[k]['sha256'],locator=z['locator'])
        if z.get('date'):assert r['date']==z['date']
        r['details']=dt;rows.append(r)
    assert len({r['id'] for r in rows})==len(rows)
    c.dump(OUT,sorted(rows,key=lambda r:(r['date'] or '',r['id'])))
    print(len(rows),'local events,',len(byid),'city register entries checked')
def classify(r,cutoff,perm,no,app,obs):
    if r.get('dataset')==NA and r.get('details',{}).get('permit_family')=='PLCU20250038':
        from lib.status import iso
        return perm('OH:new-albany-temp-batch','unconfirmed','Temporary conditional-use authorization for the same batch plant; its later continuation is not a second plant or independent current permit.',iso(r['date']),stable_no='PLCU20250038')
    if r.get('dataset') in [NA,HI]:return no('Local variance, site-plan, rezoning, recommendation or lot-split decision; not a numbered construction permit.','decision')
    return None
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');a=p.parse_args()
    if a.refresh:fetch()
    build()
