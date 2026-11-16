"""Query selected government open-data tables. Pin filtered rows and an independent count.
Raw candidate labels never establish building-permit issuance on their own.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, hashlib, json, re, sys, argparse
from urllib.parse import urlencode
from collections import Counter,defaultdict
import lib.discovery as c
from lib.url_archive import Archive
CONFIG=c.R/'data/national/municipal_feeds.csv'
def scan(fetch,review=False):
    a=Archive('municipal',fetch,owner='multistate/open_data_feeds');results={};candidates=[]
    for f in csv.DictReader(CONFIG.open()):
        dom=f['domain'];table=f['feed'];col=f['description'];slug=f['series'];st=f['state']
        url='https://'+dom+'/resource/'+table+'.json?';root='https://'+dom+'/d/'+table
        where=' OR '.join("upper("+col+") like '%"+term+"%'" for term in ['DATA CENTER','DATA CENTRE','DATA-CENTER','DATACENTER','SERVER FARM'])
        fields=list(dict.fromkeys([f[k] for k in ('number','description','date','status','type') if f[k]]))
        try:
            meta=a.json('https://'+dom+'/api/views/'+table)
            if meta.get('id')!=table or not set(fields)<={v['fieldName'] for v in meta['columns']}:raise ValueError('Changed register fields')
            uc=url+urlencode({'$where':where,'$select':'count(*) as n'})
            n=int(a.json(uc)[0]['n']); got=[]
            for start in range(0,n,500):
                q=url+urlencode({'$select':','.join(fields),'$where':where,'$order':f['number']+' asc,:id asc','$limit':500,'$offset':start})
                raw,h=a.get(q);got.extend((v,q,h) for v in json.loads(raw))
            if len(got)!=n:raise ValueError('Query returned fewer records than count')
            results[table]=dict(state=st,government=f['government'],source=root,total=n,count_source=uc,issued_field=f['date'])
            for v,q,h in got:
                label=v.get(f['description'],'');key=str(v.get(f['number']) or '').strip()
                if not key:continue
                candidates.append(dict(state=st,feed=table,series=slug,government=f['government'],county=f['county'],no=key,description=label,date=(v.get(f['date']) or '')[:10],status=v.get(f['status']) or '',type=v.get(f['type']) or '',url=url+urlencode({'$where':f['number']+"='"+key.replace("'","''")+"'"}),source=q,hash=h))
        except Exception as e:
            if not fetch and table not in (c.read(c.R/'data/national/municipal_exceptions.json',{})):raise
            results[table]=dict(state=st,government=f['government'],source=root,error=str(e))
    c.dump(c.R/'data/national/municipal_scan.json',results)
    c.dump(c.R/'cache/national/municipal_candidates.json',candidates)
    print('Government registers:',[(k,v.get('total',v.get('error'))) for k,v in results.items()])
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fetch',action='store_true');scan(ap.parse_args().fetch)
