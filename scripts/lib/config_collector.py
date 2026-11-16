"""Config-only collector: a state's sources and reviewed records live in data/history/<state folder>/config.json.
Each record's quote must appear on the cited page. Used by KY, ID, KS, MT, ND, SD, WY."""
import argparse, collections, io
from functools import lru_cache
from pypdf import PdfReader
import lib.discovery as collect
from lib import net as netfetch
from lib.paths import R, collector_data, series_path, state_folder
from lib.files import j
from lib.archive import Store
from lib.geo import rank, geofetch
from lib.text import htmltext
from lib.arcgis import arcstore


def run(st,code,fetch=False,initial=False):
    lo=st.lower();s=Store(st);c=j(collector_data(state_folder(st),'config.json'));p=collector_data(state_folder(st),'manifest.json');m=j(p) if p.exists() else {}
    if fetch:
        if 'geo' not in m or netfetch.REFETCH:m['geo']=geofetch(s,code);collect.dump(p,m)
        for k,v in c['sources'].items():
            if k in m and not netfetch.REFETCH:continue
            try:
                m[k]=(arcstore(s,v['url'],v['where'],v['out']) if v.get('where') else s.get(v['url'],v['ext']))
            except (ValueError,OSError) as e:m[k]=dict(url=v['url'],error=str(e))
            collect.dump(p,m)
    rank(s,m['geo'])
    if initial:return m
    out=[]
    @lru_cache()
    def doc(k):return PdfReader(io.BytesIO(s.read(m[k])))
    for v in c['records']:
        k=v['source'];r=m[k];pg=v.get('page')
        if 'where' in r:
            match=[(b,a['attributes']) for b in r['batches'] for a in s.read(b)['features'] if str(a['attributes'][r['oid']])==str(v['oid'])]
            if len(match)!=1:raise ValueError('Case register mismatch')
            ref,a=match[0]
            if any(a.get(f)!=value for f,value in v.get('assert_attrs',{}).items()):raise ValueError('Published row drift')
            text=' '.join(str(z) for z in a.values());url=ref['url'];source=ref
        else:
            text=doc(k).pages[pg-1].extract_text() if r['ext']=='pdf' else htmltext(s.read(r));url=r['url']+(('#page='+str(pg)) if pg else '');source=r
        norm=lambda t:' '.join(str(t).lower().split())
        if norm(v['evidence']) not in norm(text):raise ValueError(k+' / '+v['evidence'])
        z={key:v[key] for key in 'id dataset jurisdiction record_no project kind status date date_role locator'.split()};z.update(id=lo+'-'+z['id'],state=st,url=url,source_url=source['url'],details=dict(source_sha256=source['sha256'],evidence=v['evidence'],**v.get('details',{})));out.append(z)
    if len(set(z['id'] for z in out))!=len(out):raise ValueError('Duplicate id')
    collect.dump(series_path(lo),sorted(out,key=lambda x:x['id']));collect.dump(collector_data(state_folder(st),'coverage.json'),dict(rows=len(out),by_dataset=dict(collections.Counter(x['dataset'] for x in out)),undated=sum(x['date'] is None for x in out),source_failures={k:v['error'] for k,v in m.items() if 'error' in v}))
    return out
def cli(st,code):
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');args=p.parse_args();run(st,code,args.fetch)
