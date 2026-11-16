"""Find legislative matters through government-linked public Legistar registers, not a census of permits.
Bounded, paginated public API; does not promote a filing, hearing or vote to an issued construction permit.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.net as netfetch
import argparse, csv, collections, json, re, gzip, hashlib
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from lib.url_archive import Archive
import lib.discovery as c
D=c.R/'data/national';BASE=c.R/'cache/national/councils'
def offices():
    users=collections.defaultdict(set)
    for r in csv.DictReader((D/'council_portals.csv').open()):
        users[r['client']].add((r['state'],r['government'],r['homepage']))
    for st,client,gov,src in [('WI','madison','City of Madison','https://madison.legistar.com/LegislationDetail.aspx?ID=7777877'),('WI','milwaukee','City of Milwaukee','https://milwaukee.legistar.com/LegislationDetail.aspx?ID=8029591'),('NH','concordnh','City of Concord','https://concordnh.legistar.com/LegislationDetail.aspx?ID=8210754')]:
        users[client].add((st,gov,src))
    return users
def collect(client):
    target=BASE/(client+'.json');proof=BASE/(client+'.json.gz')
    if proof.exists() and target.exists():return
    from urllib.request import urlopen,Request
    from urllib.error import HTTPError
    c.policy('https://webapi.legistar.com/');found=[];sources=[];ids=set()
    filt=' or '.join("substringof('"+term+"',"+field+")" for field in ('MatterTitle','MatterName') for term in ('data center','datacenter','data centre','server farm','data-center'))
    try:
        for offset in range(0,2501,250):
            url='https://webapi.legistar.com/v1/'+client+'/matters?'+urlencode({'$filter':filt,'$orderby':'MatterId','$top':250,'$skip':offset})
            raw=netfetch.get(url,timeout=35,limit=12*1024*1024)
            values=json.loads(raw);assert isinstance(values,list)
            if any(r['MatterId'] in ids for r in values):raise ValueError('Repeated ID across query pages')
            ids.update(r['MatterId'] for r in values);sources.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),rows=len(values)));found.extend(values)
            (BASE/(sources[-1]['sha256']+'.gz')).write_bytes(gzip.compress(raw,mtime=0))
            if len(values)<250:break
        else:raise ValueError('Page budget exhausted')
        proof.write_bytes(gzip.compress(json.dumps(found,ensure_ascii=False).encode(),mtime=0));msg='Complete public title/name query'
    except Exception as e:msg='Unavailable: '+str(e)[:130]
    c.dump(target,dict(result=msg,items=len(found),sources=sources))
def summarize():
    offices_=offices();results=[];logs=[]
    for client,owners in sorted(offices_.items()):
        file=BASE/(client+'.json');doc=c.read(file,{});owners=sorted(owners)
        logs.append(dict(client=client,origins=owners,**doc))
        if doc.get('result')!='Complete public title/name query' or len({(s,n) for s,n,u in owners})!=1:continue
        st,gov,url=owners[0]
        for j,src in enumerate(doc['sources']):
            raw=gzip.decompress((BASE/(src['sha256']+'.gz')).read_bytes())
            if hashlib.sha256(raw).hexdigest()!=src['sha256']:raise ValueError('Council source changed')
            for r in json.loads(raw):
                results.append(dict(client=client,state=st,government=gov,id=r['MatterId'],guid=r['MatterGuid'],file=r['MatterFile'],title=r['MatterTitle'],name=r['MatterName'],kind=r['MatterTypeName'],status=r['MatterStatusName'],introduced=r['MatterIntroDate'],passed=r['MatterPassedDate'],enacted=r['MatterEnactmentDate'],source=src['url'],sha=src['sha256']))
    c.dump(D/'council_searches.json',logs);c.dump(BASE/'candidates.json',results)
    print(len(logs),'public portals;',len(results),'title or name candidates')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');args=p.parse_args();BASE.mkdir(exist_ok=True,parents=True)
 if args.fetch:
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(collect,sorted(offices())))
 summarize()
