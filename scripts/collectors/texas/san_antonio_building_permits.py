"""City of San Antonio: issued building and trade permits (CKAN datastore resources), matched on project name."""
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
def download(m):
    save=saver(m)
    x=CONFIG['san_antonio'];url=x['url']
    for resource in x['ids']:
        # Source supplies the project label but no narrative in these issued registers.
        select='SELECT "_id","PROJECT NAME","PERMIT #","PERMIT TYPE","WORK TYPE","DATE ISSUED","DATE SUBMITTED","ADDRESS"'
        where=' OR '.join('"PROJECT NAME" ILIKE '+repr(z) for z in ('%data%center%','%data%centre%','%data%hall%','%server%farm%'))
        tail=' FROM "'+resource+'" WHERE '+where
        q='SELECT COUNT(*) AS n'+tail
        expected=int(json.loads(req(url,{'sql':q}))['result']['records'][0]['n']);seen=set()
        for off in range(0,expected,1000):
            q=select+tail+' ORDER BY "_id" LIMIT 1000 OFFSET '+str(off)
            b=req(url,{'sql':q});rr=json.loads(b)['result']['records'];assert not(seen & {a['_id'] for a in rr});seen.update(a['_id'] for a in rr)
            save(f'san_antonio-{resource}-{off}.json.gz',b,url+'?'+urlencode({'sql':q}))
        if len(seen)!=expected:raise ValueError('San Antonio source reconciliation failed')
        print('san_antonio',resource,expected,flush=True)
def rows(m,add,exclusions):
    k='san_antonio';x=CONFIG[k]
    for n in sorted(m):
        if not n.startswith('san_antonio-'):continue
        rid=re.match(r'san_antonio-(.{36})-',n).group(1)
        for a in json.loads(gzip.decompress((C/n).read_bytes()))['result']['records']:
            name=a['PROJECT NAME'];no=a['PERMIT #'];oid=a['_id'];match=MATCH.search(name)
            if not match:exclusions.append((k,oid,'no explicit keyword',name));continue
            href='https://data.sanantonio.gov/api/3/action/datastore_search?'+urlencode({'resource_id':rid,'filters':json.dumps({'PERMIT #':no},separators=(',',':'))})
            add(k,n,no,name,a['PERMIT TYPE'],'Issued',isodate(a['DATE ISSUED']),'Issue date',href,f'{rid}; PERMIT # {no}',{'address':a['ADDRESS'],'work_class':a['WORK TYPE'],'application_date':isodate(a['DATE SUBMITTED']),'matched_text':match.group()},'San Antonio',row_id=oid)
