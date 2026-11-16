"""Retrieve Louisiana DEQ published quarter reports, screen every table row. Local cache for deterministic replay."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urljoin,urlsplit
import csv, re, json, hashlib, gzip, sys
import lib.net as netfetch
from html import unescape
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[3];CACHE=ROOT/'cache/history/la'
INDEX={'air':'https://www.deq.louisiana.gov/page/permits-issued-by-calendar-quarter','water':'https://www.deq.louisiana.gov/page/lpdes'}
def download(url,p):
    p.write_bytes(netfetch.get(url,timeout=45))
def files():
    for kind,url in INDEX.items():
        t=(CACHE/f'{kind}-index.html').read_text()
        for path,label in re.findall(r'<a\b[^>]+href="([^"]+)"[^>]*>(.*?)</a>',t,re.S):
            if kind=='air' and not re.search(r'\.(xlsx|xls)$',path,re.I):continue
            if kind=='water' and not re.match(r'(January|April|July|October)',re.sub('<[^>]*>','',label).strip()):continue
            full=urljoin(url,unescape(path)); name=urlsplit(full).path.rsplit('/',1)[-1];yield kind,full,CACHE/name
def fetch():
    CACHE.mkdir(parents=True,exist_ok=True)
    for k,u in INDEX.items():download(u,CACHE/f'{k}-index.html')
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda x:download(x[1],x[2]),files()))
if __name__=='__main__' and '--refresh' in sys.argv:fetch()
