"""Fetch Utah DAQ's public datatable submissions with their provided form/session values."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import sys, json, re, html
from urllib.request import build_opener,HTTPCookieProcessor,Request
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from lib.files import pack
from lib.paths import CACHE
BASE='https://daqpermitting.utah.gov/'
PAGES=['AOsIssuedAll','NOI_Pub_H','AOsOutForCmt','OPS_Issued','OPS_OutForCmt','OPS_OutForEPA']
def getpage(page):
    op=build_opener(HTTPCookieProcessor(CookieJar()));raw=op.open(BASE+page,timeout=60).read();s=raw.decode('latin-1')
    vals={k:html.unescape(re.search(r'(?:id|name)="'+k+r'"[^>]*value="([^"]*)"',s)[1]) for k in ('reportType','startDate','endDate','_csrf')}
    r=op.open(Request(BASE+'ajax_report_data',data=urlencode(vals).encode(),headers={'Content-Type':'application/x-www-form-urlencoded','X-CSRF-TOKEN':vals['_csrf'],'Referer':BASE+page,'X-Requested-With':'XMLHttpRequest'}),timeout=100);js=json.load(r)
    if 'data' not in js:raise ValueError(str(js)[:100])
    d=CACHE/'ut';d.mkdir(exist_ok=True,parents=True);pack(d/(page+'.json.gz'),dict(page=BASE+page,url=BASE+'ajax_report_data',parameters={k:v for k,v in vals.items() if k!='_csrf'},rows=js['data']));print(page,len(js['data']),str(js['data'][:1])[:500],flush=True)
if __name__=='__main__':
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as t:list(t.map(getpage,PAGES))
