"""City of Austin: issued construction permits (Socrata open-data dataset), keyword-matched on the configured search fields."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.files import dump, sha
from lib.net import req
from lib.terms import MATCH, patterns
from lib.text import isodate, Fields
import lib.arcgis as arcgis
import gzip, json, re
from urllib.parse import urlencode, quote
from collections import Counter
from collectors.texas.common import ROOT, C, CONFIG, saver
K='austin'
def download(m):
    save=saver(m)
    k=K
    x=CONFIG[k];w=patterns(x['search'],'lower');url=x['url']
    count=int(json.loads(req(url,{'$where':w,'$select':'count(*) as n'}))[0]['n']);ids=set()
    for off in range(0,count,1000):
        params={'$select':x['fields'],'$where':w,'$limit':1000,'$offset':off,'$order':':id'}
        b=req(url,params);rows=json.loads(b);assert not(ids & {r['rowid'] for r in rows});ids.update(r['rowid'] for r in rows)
        save(f'{k}-{off}.json.gz',b,url+'?'+urlencode(params))
    if len(ids)!=count:raise ValueError(f'{k}: returned {len(ids)} vs reported {count}')
    print(k,count,flush=True)
def rows(m,add,exclusions):
    k,city=K,'Austin';x=CONFIG[k]
    for n in sorted(m):
        if not re.fullmatch(k+r'-\d+\.json\.gz',n):continue
        r=json.loads(gzip.decompress((C/n).read_bytes()))
        for a in ([z['attributes'] for z in r['features']] if k=='fort_worth' else r):
            text=' | '.join(str(a.get(f) or '') for f in x['search']);match=MATCH.search(re.sub(r"(?<=[a-z])(?=[A-Z])"," ",text))
            if not match:
                exclusions.append((k,a.get('rowid',a.get('ObjectId')),'no explicit keyword',text[:200]));continue
            no=a['permit_number'];oid=a['rowid'];desc=a.get('work_description',a.get('description',''));land=a.get('land_use','');kind=a.get('permit_type') or a.get('permit_type_desc');dt=isodate(a.get('issued_date',a.get('issue_date')));role='Issue date' if dt else 'Issue date not stated';status=a.get('status_current','Issued') if k=='dallas' else a.get('status_current');url=(a.get('link') or {}).get('url') or x['url']+'?'+urlencode({'permit_number':no});loc=f'permit_number {no}, Socrata row {oid}';addr=a.get('street_address',a.get('original_address1',''));project=addr or desc[:120] or no;extra={'work_description':desc,'address':addr,'land_use':land,'source_jurisdiction':a.get('jurisdiction'),'work_class':a.get('work_class'),'project_id':a.get('project_id')}
            extra['matched_text']=match.group();add(k,n,no,project,kind,status,dt,role,url,loc,extra,city)
