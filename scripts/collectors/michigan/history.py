"""Michigan permit history: combines the EGLE, MPSC, Saline Township, Van Buren Township and Southfield sources below into
output/history/michigan/history.json and data/history/michigan/coverage.json. Offline replay by default; --fetch re-downloads every source;
--review-scans re-runs OCR on the scanned PDFs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, R
import lib.net as netfetch
import argparse, io, collections
from pypdf import PdfReader
import lib.discovery as collect
from lib.files import j
from lib.geo import geofetch, rank
from collectors.michigan.evidence_store import ST, M, C, O, A, make
from collectors.michigan import egle_air_permits as egle_air, egle_water_withdrawals as egle_water, saline_township_proceedings as saline, mpsc_special_contracts as mpsc, van_buren_planning_commission as van_buren, southfield_site_plan_review as southfield
SOURCES=(egle_air, mpsc, saline, southfield, egle_water, van_buren)
def fetch(m):
    if 'geo' not in m or netfetch.REFETCH:m['geo']=geofetch(ST,'26');collect.dump(M,m)
    for s in SOURCES:s.download(m)
    order=['geo']+list(j(C));m.update({k:m.pop(k) for k in sorted(m,key=lambda k:order.index(k) if k in order else len(order))});collect.dump(M,m)  # keep manifest keys in config order
def scans(m):
    import subprocess, tempfile
    from pypdf import PdfWriter
    dest=collector_data('michigan','ocr.json');out=j(dest) if dest.exists() else {}
    for k,nums in [('vbt_feb',[1,19,20]),('ptiorig',[1,2]),('ptisecond',[1]),('saline_water',[1,2])]:
        if k in out:continue
        ref=m[k];doc=PdfReader(io.BytesIO(ST.read(ref)));q=PdfWriter()
        for n in nums:q.add_page(doc.pages[n-1])
        with tempfile.TemporaryDirectory(dir=ST.d) as tmp:
            p=R/tmp/'subset.pdf'
            with p.open('wb') as f:q.write(f)
            res=subprocess.run(['swift',str(R/'scripts/lib/ocr_vision.swift'),str(p),str(len(nums))],check=True,capture_output=True)
        import json
        out[k]=dict(sha256=ref['sha256'],pages=dict(zip(map(str,nums),json.loads(res.stdout))));collect.dump(dest,out)
def build(m):
    rank(ST,m['geo']);out=[];txt,add=make(m,out)
    egle_air.rows(m,txt,add);egle_water.rows(m,txt,add);saline.rows(m,txt,add);mpsc.rows(m,txt,add);van_buren.rows(m,txt,add);southfield.rows(m,txt,add)
    if len(out)!=len({v['id'] for v in out}):raise ValueError('duplicate Michigan ID')
    collect.dump(O,sorted(out,key=lambda v:v['id']));collect.dump(A,dict(cutoff='2026-11-16',counts=dict(collections.Counter(x['dataset'] for x in out)),undated=sum(x['date'] is None for x in out),sourced_failures={k:x.get('error') for k,x in m.items() if 'error' in x},legacy_inventory_as_of='2024-12-08',direct_issued_air_numbers=['91-16','112-16','112-16A']))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--review-scans',action='store_true');args=p.parse_args();m=j(M) if M.exists() else {}
    if args.fetch:fetch(m)
    if args.review_scans:scans(m)
    build(m)
