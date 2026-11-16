"""Georgia shared evidence helpers: the content-addressed gzip archive in cache/history/ga (fetch, read, hash check),
the output paths, HTML and PDF text helpers, and the common record builder. Not a source: every issuer module imports it."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.net as netfetch
import collections, csv, datetime as dt, gzip, hashlib, html, io, json, re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode
from pypdf import PdfReader
import lib.discovery as collect
R=Path(__file__).resolve().parents[3];D=R/'cache/history/ga'; C=collector_data('georgia','config.json');M=collector_data('georgia','manifest.json'); O=series_path('ga');RK=collector_data('georgia','rank.json');A=collector_data('georgia','coverage.json'); REVIEW=collector_data('georgia','review.json')
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
def text(h):return ' '.join(html.unescape(re.sub(r'<[^>]+>',' ',h)).split())
def htmlref(r):return read(r,True).decode('utf8','replace')
def links(h):
    p=collect.HTML();p.feed(h);return p.links
DC=re.compile(r'\bdata[ -]*(?:center|centre)s?\b|\bserver farm\b',re.I)
def flatten(t):return ' '.join(t.split())
@lru_cache(maxsize=250)
def pdfpages(h):
    b=gzip.decompress((D/(h+'.pdf.gz')).read_bytes())
    if hashlib.sha256(b).hexdigest()!=h:raise ValueError('PDF digest mismatch')
    return [flatten(p.extract_text() or '') for p in PdfReader(io.BytesIO(b)).pages[:7]]
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def row(ds,key,jur,num,project,kind,status,date,role,ref,locator,**de):
    return dict(id='ga-'+key,state='GA',dataset=ds,jurisdiction=jur,record_no=num,project=project,kind=kind,status=status,date=date,date_role=role,url=ref['url'],locator=locator,details=dict(source_sha256=ref['sha256'],**de))
def docmatch(ref):
    if not ref or 'sha256' not in ref:return None
    for i,t in enumerate(pdfpages(ref['sha256'])):
        q=DC.search(t)
        if q:return (i+1,' '.join(t[:q.start()].split()[-5:]+[q.group()]+t[q.end():].split()[:6]))
def parsedate(s):
    for fmt in ['%B %d %Y','%b %d %Y']:
        try:return dt.datetime.strptime(s.replace(',','').replace('.','').title(),fmt).date().isoformat()
        except ValueError:pass
    return None
def county_names():return {r['geoid'][2:]:r['name'] for r in csv.DictReader((R/'data/national/jurisdictions.csv').open()) if r['state']=='GA' and r['layer']=='counties'}
