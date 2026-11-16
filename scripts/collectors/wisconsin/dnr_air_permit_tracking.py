"""Wisconsin DNR air permit tracking (apps.dnr.wi.gov WARP permit tracking, including inactive permits) for the Mount Pleasant
and Port Washington data center facilities."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import CACHE
from lib.records import rec
from lib.text import strip, tr
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.request import build_opener,HTTPCookieProcessor,Request
from urllib.parse import urlencode
from http.cookiejar import CookieJar
import re, html
D=CACHE/'wi';B='https://apps.dnr.wi.gov/warp_ext/AM_PermitTracking2.aspx?id=';A='Wisconsin DNR air permit tracking'
SITES={'35961':('Microsoft Mount Pleasant Data Centers','Mount Pleasant','Racine County'),'38402':('Vantage WI-1','Port Washington','Ozaukee County')}
def page(i):
 op=build_opener(HTTPCookieProcessor(CookieJar()));u=B+i
 with op.open(u,timeout=75) as r:raw=r.read()
 s=raw.decode();d={}
 for tag in re.findall('<input[^>]+>',s,re.I):
    if 'type="hidden"' in tag:
        a={k:html.unescape(v) for k,v in re.findall(r'([\w:-]+)="([^"]*)"',tag)}
        if a.get('name'):d[a['name']]=a.get('value','')
 ctrl='ctl00$ContentPlaceHolder1$chkInactive';d.update({ctrl:'on','__EVENTTARGET':ctrl,'__EVENTARGUMENT':''});resp=op.open(Request(u,data=urlencode(d).encode(),headers={'Referer':u}),timeout=75).read().decode()
 if not re.search(r'id="ctl00_ContentPlaceHolder1_chkInactive"[^>]*checked=',resp):raise ValueError('Inactive rows not requested successfully '+u)
 # Only retain public permit table and facility identity; exclude transient form/session tokens.
 rows=re.search(r'<table[^>]*id="ctl00_ContentPlaceHolder1_gvPermits".*?</table>',resp,re.S|re.I)
 if not rows or SITES[i][0].lower() not in resp.lower():raise ValueError('Unexpected facility')
 (D/(i+'.html')).write_text(SITES[i][0]+'\n'+rows[0])
def download():
 D.mkdir(parents=True,exist_ok=True)
 with ThreadPoolExecutor(max_workers=2) as t:list(t.map(page,SITES))
def rows():
 """Records plus the per-facility register row counts the validation file reports."""
 rows=[];cnt={}
 for id,(site,place,county) in SITES.items():
    p=D/(id+'.html');s=p.read_text();u=B+id;cnt[id]=0
    if not all(x in s for x in ('App Received','App. Comp.','Public Notice','Decision*','Status')):raise ValueError('Air table schema changed')
    for z in tr(s):
        t=[strip(x) for x in re.findall(r'<td\b[^>]*>(.*?)</td>',z,re.S|re.I)]
        if not t:continue
        if len(t)!=9:raise ValueError(t)
        _,no,kind,received,complete,notice,decision,status,_=t;cnt[id]+=1
        for key,raw,role,st in [('app',received,'application received','Application received'),('complete',complete,'application complete date','Application complete'),('notice',notice,'public notice date','Public Notice'),('dec',decision,'permit decision date',status)]:
            if not raw or raw=='X':continue # no affirmative, dated decision in that case
            dt=datetime.strptime(raw,'%m/%d/%Y').date().isoformat()
            rows.append(rec('WI','air-'+id+'-'+no+'-'+key,A,no,'Air permit / '+kind,st,dt,role,u,'Permit '+no+'; '+role+'; include inactive permits',site,place,county,p,issuer='Wisconsin DNR',register_status=status,permit_type=kind,facility_key=id))
 return rows,cnt
