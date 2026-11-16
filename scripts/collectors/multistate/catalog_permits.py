"""Search government registers selected from the national catalogue; publish only reviewed row IDs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, csv, collections, re, json
from urllib.parse import urlencode
from lib.url_archive import Archive
import lib.discovery as c
D=c.R/'data/national'
PINS=D/'catalog_permit_review.json'
DS='Municipal building permit case files'
def run(fetch=False,review=False):
 specs=list(csv.DictReader((D/'catalog_registers.csv').open()));arch=Archive('catalog_permits',fetch,owner='multistate/catalog_permits');candidates={};stats={};out=collections.defaultdict(list);pins=c.read(PINS,{})
 for spec in specs:
    dom,tab=spec['domain'],spec['table'];base='https://'+dom+'/resource/'+tab+'.json?';url='https://'+dom+'/api/views/'+tab
    try:
        m=arch.json(url);fields={x['fieldName'] for x in m['columns']};keys=list(dict.fromkeys(spec[k] for k in ('number','description','issued','status','worktype') if spec[k]))
        if not set(keys)<=fields:raise ValueError('Schema differs from configured source')
        cond=' OR '.join('upper('+spec['description']+") like '%"+q+"%'" for q in ('DATA CENTER','DATA CENTRE','DATA-CENTER','DATACENTER','SERVER FARM'));nc=base+urlencode({'$where':cond,'$select':'count(*) as n'});n=int(arch.json(nc)[0]['n']);rows=[]
        for i in range(0,n,200):
            q=base+urlencode({'$select':','.join(keys),'$where':cond,'$order':spec['number']+' asc,:id asc','$offset':i,'$limit':200});b,sha=arch.get(q)
            rows.extend((item,q,sha) for item in json.loads(b))
        if len(rows)!=n:raise ValueError('Count differs from page total')
    except Exception as e:
        if not fetch and not c.read(D/'catalog_register_checks.json',{}).get(tab,{}).get('error'):raise
        stats[tab]={'source':url,'error':str(e)};continue
    stats[tab]=dict(source=url,count=n,count_query=nc)
    for x,q,sha in rows:
        num=x.get(spec['number'],'');desc=x.get(spec['description'],'');key=tab+'/'+num+'/'+c.digest(json.dumps(x,sort_keys=True).encode())[:12]
        candidates[key]={'source':q,'sha256':sha,'state':spec['state'],'number':num,'description':desc,'issued':x.get(spec['issued']),'status':x.get(spec['status']),'type':x.get(spec['worktype'])}
        if pins.get(key,{}).get('decision')!='include':continue
        if not num:raise ValueError('Missing case identity')
        d=(x.get(spec['issued']) or '')[:10];st=spec['state'];rr=pins[key]
        if d and d>'2026-11-15':raise ValueError('After cutoff')
        out[st].append(dict(id='cat-'+tab+'-'+key.split('/')[-1],state=st,record_no=num,project=rr['project'],kind='Building permit' if d else 'Building department case',jurisdiction=spec['government'],county=spec['county'],dataset=DS,date=d or None,date_role='Issue date' if d else 'No issue date reported',status=x.get(spec['status']) or ('Issued' if d else 'No status reported'),url=base+urlencode({'$where':spec['number']+"='"+num.replace("'","''")+"'"}),source_url=q,source_sha256=sha,locator=m['name']+' · '+spec['number']+' '+num,details=dict(work_description=desc,issuing_register=m['name'],source_table=tab,scope=rr['scope'],issuance_dated=bool(d),disposition=rr['disposition'],source_type=x.get(spec['worktype']))))
 if set(pins)-candidates.keys():raise ValueError('Reviewed permit row changed or disappeared')
 c.dump(c.R/'cache/national/catalog_permit_candidates.json',candidates);c.dump(D/'catalog_register_checks.json',stats)
 for st,rows in out.items():c.dump(series_path('catalog_'+st.lower()),rows)
 if not review and set(candidates)!=set(pins):raise ValueError('Review '+str(len(set(candidates)-set(pins)))+' new candidates; refusing automatic promotion')
 print(len(candidates),'candidate rows;',sum(map(len,out.values())),'reviewed for release;',[(k,s.get('count',s.get('error'))) for k,s in stats.items()])
def classify(r,cutoff,perm,no,app,obs):
 from lib.status import details,iso
 d=details(r);s=d.get('disposition')
 if s=='nonpermit':return no('Building department record without evidence of an issued permit.','application')
 if d.get('issuance_dated') and s in ('unconfirmed','historical'):
    return perm(r['state']+':municipal-building:'+d['source_table'],s,'The register records issuance'+(' and a final or expired status.' if s=='historical' else '; current validity is not established.'),iso(r['date']))
 return no('Unsupported local register disposition.','unknown')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--review',action='store_true');a=p.parse_args();run(a.fetch,a.review)
