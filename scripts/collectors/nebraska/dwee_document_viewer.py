"""Nebraska DWEE public-record viewer: reproduce the City/State's documented facility-number/program search."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.net as netfetch
import re, json, sys, hashlib
from urllib.request import Request,urlopen
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from lib.paths import CACHE
from lib.files import pack, unpack
B='https://ecmp.nebraska.gov/publicaccess/';D=CACHE/'ne'; FACS={'122487':('CLOP Omaha NE, LLC','Papillion'),'106518':('Fireball Group LLC','Papillion'),'108432':('Raven Northbrook LLC','Papillion'),'103923':('TierPoint Data Center','Bellevue')}
def page(i):return B+'index.html?OBKey__114_1='+i+'&OBKey__115_1=AIR&MyQueryID=340'
def collect(i):
 q={'QueryID':340,'Keywords':[{'ID':114,'Value':i,'KeywordOperator':'Equal'},{'ID':115,'Value':'AIR','KeywordOperator':'Equal'}],'QueryLimit':0}
 r=json.loads(netfetch.request(B+'api/CustomQuery/KeywordSearch',json_body=q,timeout=90).body)
 if r.get('Truncated') or len(r['Data'])>=500:raise ValueError('Split DWEE official date windows before using '+i)
 names=[v['Heading'] for v in r['DisplayColumns']]
 if names!=['Document Date','Document Type','DEQ Description','DEQ Program ID','DEQ Program','DEQ Facility Number']:raise ValueError(names)
 out=[]
 for d in r['Data']:
    v=[x['Value'] for x in d['DisplayColumnValues']]
    if v[-2:]!=['AIR',i]:raise ValueError('State response outside requested scope')
    key=hashlib.sha256(json.dumps(v).encode()).hexdigest()[:16];data=dict(values=v,key=key)
    if v[1]=='DEQ Issued Permit':
        dest=D/('permit-'+i+'-'+key+'.pdf');u=B+'api/Document/'+quote(d['ID'],safe='')+'/';b=netfetch.get(u,timeout=75)
        if b[:4]!=b'%PDF':raise ValueError('Document is not PDF '+str(b[:70]))
        key=key+'-'+hashlib.sha256(b).hexdigest()[:10];dest=D/('permit-'+i+'-'+key+'.pdf');dest.write_bytes(b);data.update(key=key,filename=dest.name)
    out.append(data)
 pack(D/('ecm-'+i+'.json.gz'),dict(query=q,source=page(i),rows=out));print(i,len(out),sum('filename' in x for x in out),flush=True)
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=2) as t:list(t.map(collect,FACS))
