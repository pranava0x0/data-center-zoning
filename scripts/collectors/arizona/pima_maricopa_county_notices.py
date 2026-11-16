"""Pima County dust enforcement notices of violation and Maricopa County air public notices, as pinned excerpts in
cache/history/az/reviewed-notices.json (each entry carries its own URL). Issuers: Pima County Department of
Environmental Quality and Maricopa County Air Quality Department."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
def download(save):
    k='pima_nov';n='pima-nov.html';save(n,conf[k],lib.net.req(conf[k]))
def register(m):
    """Records the reviewed-notices file in the manifest (hand-verified; not downloaded)."""
    n='reviewed-notices.json';b=(C/n).read_bytes();m[n]={'url':conf['pima_nov'],'sha256':lib.files.sha(b),'bytes':len(b),'method':'Pinned excerpts verified in county PDFs via web reader; each entry contains its own URL'}
def rows(b):
    add=b.add
    n='reviewed-notices.json'
    for v in js((C/n).read_bytes()):
        k='Pima County dust enforcement' if v['record_no']=='PC2605-064' else 'Maricopa County air public notices'
        add(k,n,v['record_no'],v['project'],v['kind'],v['status'],v['date'],v['date_role'],v['jurisdiction'],v['source_url'],v['locator'],{kk:vv for kk,vv in v.items() if kk in ('related_permit','facility_id','comment_end','anchor','note','authority','county')},source=v['context'])
