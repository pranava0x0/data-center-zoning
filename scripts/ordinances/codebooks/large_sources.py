"""Archive the full adopted Atlanta plan and index only the named ordinance page."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, io, hashlib
from urllib.request import Request,urlopen
from pypdf import PdfReader
import lib.discovery as c
URL='https://dca.georgia.gov/document/document/plan-update-2025-4/download';CAP=80*1024*1024
def run(fetch):
 idx=c.read(c.INDEX,{});s=idx.get(URL,{})
 if s.get('adapter')=='pdf_page_excerpt' and s.get('sha256'):p=c.CACHE/(s['sha256']+'.bin')
 elif fetch:
    c.policy(URL)
    with urlopen(Request(URL,headers={'User-Agent':c.AGENT}),timeout=160) as resp:b=resp.read(CAP+1)
    if not b.startswith(b'%PDF') or len(b)>CAP:raise ValueError('Unexpected plan size/type')
    sha=c.digest(b);p=c.CACHE/(sha+'.bin');p.write_bytes(b)
 else:raise ValueError('Run --fetch to pin the plan')
 b=p.read_bytes();sha=c.digest(b)
 if p.stem!=sha:raise ValueError('Plan bytes drifted')
 doc=PdfReader(io.BytesIO(b));pages={}
 for n in range(min(len(doc.pages),130)):
    t=doc.pages[n].extract_text() or ''
    if '24-O-1218' in t and '24-O-1222' in t and 'data center' in t.lower():pages[n+1]=t
 if not pages:raise ValueError('Referenced plan page not found')
 text='\n'.join('[Page '+str(pg)+']\n'+t for pg,t in pages.items());(c.CACHE/(sha+'.txt')).write_text(text);c.dump(c.CACHE/(sha+'.links.json'),[])
 idx=c.read(c.INDEX,{});idx[URL]=dict(url=URL,resolved=URL,fetched_at=s.get('fetched_at') or c.now(),sha256=sha,text_sha256=c.digest(text.encode()),bytes=len(b),adapter='pdf_page_excerpt',indexed_pages=list(pages));c.dump(c.INDEX,idx)
 print('Archived complete plan;',len(b),'bytes; referenced PDF pages:',list(pages))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
