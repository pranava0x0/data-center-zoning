"""Tennessee shared evidence store: hash-named gzip archive (cache/history/tn), manifest paths, and the fetch/read/record helpers every source module uses."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.arcgis as arcgis
import lib.net as netfetch
import datetime as dt, gzip, hashlib, json, re
from pathlib import Path
from urllib.parse import urlencode
import lib.discovery as collect
R=Path(__file__).resolve().parents[3];D=R/'cache/history/tn'; C=collector_data('tennessee','config.json');M=collector_data('tennessee','manifest.json'); O=series_path('tn');RK=collector_data('tennessee','rank.json');A=collector_data('tennessee','coverage.json'); REVIEW=collector_data('tennessee','review.json')
RX=re.compile(r'\b(?:data[\s-]*(?:cent(?:er|re)s?|ctrs?|halls?)|server[\s-]+farms?)\b',re.I)
def j(p):return json.loads(p.read_text())
def get(url,ext='json',**q):
    if q:url+='?'+urlencode(dict(f='json',**q))
    b=netfetch.get(url,timeout=65,limit=40*1024*1024)
    if len(b)>40*1024*1024:raise ValueError('Oversized source')
    if ext=='json' and isinstance((d:=json.loads(b)),dict) and 'error' in d:raise ValueError(str(d['error']))
    if ext=='pdf' and b[:4]!=b'%PDF':raise ValueError('not PDF')
    h=hashlib.sha256(b).hexdigest();D.mkdir(parents=True,exist_ok=True);p=D/(h+'.'+ext+'.gz')
    if not p.exists():p.write_bytes(gzip.compress(b,mtime=0))
    return dict(url=url,sha256=h,ext=ext,bytes=len(b))
def read(r,raw=False):
    b=gzip.decompress((D/(r['sha256']+'.'+r['ext']+'.gz')).read_bytes())
    if hashlib.sha256(b).hexdigest()!=r['sha256'] or len(b)!=r['bytes']:raise ValueError('archive hash failure')
    return b if raw else json.loads(b)
def qcap(l,meta,where,sel):
    oid=meta.get('objectIdField') or next(v['name'] for v in meta['fields'] if v['type']=='esriFieldTypeOID')
    p=arcgis.pull(get,read,l['url'],where,','.join(dict.fromkeys([oid]+sel)),oid,batch=125)
    return dict(oid=oid,ids=p['ids'],batches=p['batches'],predicate=where)
def dataset_rows(p):
    ids=read(p['ids'])['objectIds'] or [];rr=[(v['attributes'],r) for r in p['batches'] for v in read(r)['features']]
    if sorted(ids)!=sorted(a[p['oid']] for a,_ in rr):raise ValueError('missing rows in frozen page')
    return rr
def fetch_layers(c,m,keys):
    for k,l in c['layers'].items():
        if k not in keys:continue
        if k in m.setdefault('layers',{}) and not netfetch.REFETCH:continue
        try:collect.policy(l['url'])
        except (ValueError,OSError) as e:
            m.setdefault('unavailable_layers',{})[k]=str(e);collect.dump(M,m);continue
        meta=get(l['url']+'?f=json');d=read(meta);fields={v['name'] for v in d['fields']}
        lex=[f for f in l['lex'] if f in fields];sel=[f for f in l['fields']+lex if f in fields]
        cond=["UPPER("+f+") LIKE '"+t+"'" for f in lex for t in c['terms']+l.get('aliases',[])]
        cond+=l.get('extra',[])
        w=' OR '.join(cond);p=qcap(l,d,w,sel)
        b=dict(meta=meta,screen=p,count=get(l['url']+'/query',where='1=1',returnCountOnly='true'))
        m['layers'][k]=b;collect.dump(M,m);print(k,len(dataset_rows(p)),flush=True)
def fetch_documents(c,m,keys):
    for k,entry in c.get('documents',{}).items():
        if k not in keys:continue
        if k not in m.setdefault('docs',{}) or netfetch.REFETCH:m['docs'][k]=get(entry['url'],entry['ext']);collect.dump(M,m)
def adder(rows,cut):
    def add(key,ds,ju,num,project,kind,status,date,role,url,loc,ref,details):
        if date and dt.date.fromisoformat(date)>dt.date.fromisoformat(cut):return
        rows.append(dict(id='tn-'+key,state='TN',dataset=ds,jurisdiction=ju,record_no=num,project=project,kind=kind,status=status,date=date,date_role=role,url=url,locator=loc,source_url=ref['url'],source_sha256=ref['sha256'],details=details))
    return add
