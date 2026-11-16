"""Replay specific votes from cited lines/pages. Decisions and permits remain separate."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, collections, json, datetime, io, re
from pypdf import PdfReader
import lib.discovery as c
from lib.url_archive import Archive
D=c.R/'data/national'
def main(fetch=False):
 a=Archive('casebook',fetch,owner='multistate/meeting_votes');store=collections.defaultdict(list);docs={}
 for case in c.read(D/'docket_cases.json',[]):
    url=case['url'];b,h=a.get(url)
    if url not in docs:docs[url]=PdfReader(io.BytesIO(b)) if b.startswith(b'%PDF') else c.parse(b,'text/html',url)[1]
    doc=docs[url];pages=case.get('pages',[])
    s=' '.join(doc.pages[i-1].extract_text() or '' for i in pages) if pages else doc
    text=c.norm(s)
    if not all(c.norm(k) in text for k in case['anchors']):raise ValueError('Missing '+str([k for k in case['anchors'] if c.norm(k) not in text])+' '+case['no'])
    if datetime.date.fromisoformat(case['date'])>datetime.date(2026,11,15):continue
    out=dict(id=case['state'].lower()+'-case-'+c.digest('|'.join(case[k] for k in ['no','date','status','kind']).encode())[:13],state=case['state'],dataset=case['dataset'],jurisdiction=case['jurisdiction'],county=case['county'],record_no=case['no'],project=case['project'],kind=case['kind'],status=case['status'],date=case['date'],date_role=case['role'],url=url+('#page='+str(pages[0]) if pages else ''),source_url=url,source_sha256=h,locator=case['locator'],details=dict(decision=case['summary'],evidence=case['anchors'][0]))
    store[case['state']].append(out)
 for st,v in store.items():c.dump(series_path('case_'+st.lower()),v)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');main(p.parse_args().fetch)
