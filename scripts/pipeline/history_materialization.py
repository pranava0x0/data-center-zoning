"""Verify bytes for archive receipts across the various local collector layouts (offline, no AI)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, gzip, hashlib, json, os, re
from collections import Counter,defaultdict
from pathlib import Path
import lib.discovery as c
def sha_stream(fp):
 h=hashlib.sha256()
 for b in iter(lambda:fp.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(strict=False):
 with (c.OUT/'receipts/evidence.csv').open() as fp:rr=list(csv.DictReader(fp))
 by=defaultdict(list)
 for r in rr:by[r['sha256']].append(r['id'])
 targets=set(by);found={};seen=set()
 def check(p):
    if p in seen or not p.is_file():return
    seen.add(p)
    with p.open('rb') as fp:
        header=fp.read(2);fp.seek(0);h=sha_stream(fp)
    if h in targets:found.setdefault(h,(str(p.relative_to(c.R)),'stored bytes'))
    if header!=b'\x1f\x8b':return
    with gzip.open(p,'rb') as fp:h=sha_stream(fp)
    if h in targets:found.setdefault(h,(str(p.relative_to(c.R)),'decompressed bytes'))
 for r in rr:
    if r['archive_path']:check(c.R/r['archive_path'])
 # Prior index gives future releases a fast path but is never trusted without rechecking bytes.
 previous=c.OUT/'receipts/evidence_files.csv'
 if previous.exists():
    with previous.open() as fp:
        for r in csv.DictReader(fp):
            if r['sha256'] in targets and r['file']:check(c.R/r['file'])
 files=[]
 for base,dirs,names in os.walk(c.R/'cache'):
    dirs[:]=[d for d in dirs if not d.startswith('chrome-test-')]
    for n in names:
        p=Path(base)/n;stem=n.split('.')[0]
        if stem in targets and stem not in found:check(p)
        elif ('/cache/history/' in str(p) or '/cache/westmetro/' in str(p)) and not re.fullmatch('[0-9a-fA-F]{64}',stem):files.append(p)
 if targets-set(found):
    for p in sorted(files+list((c.R/'data').rglob('*.json')),key=lambda x:x.stat().st_size):
        if not targets-set(found):break
        check(p)
 with previous.open('w',newline='') as fp:
    w=csv.writer(fp);w.writerow(['sha256','file','hash_applies_to','history_records'])
    for h,ids in sorted(by.items()):w.writerow([h,*found.get(h,('','not matched to a whole stored file')),len(set(ids))])
 matched={i for h in found for i in by[h]};missing=sorted(targets-set(found))
 c.dump(c.OUT/'receipts/materialization.json',dict(unique_receipt_hashes=len(targets),matched_files=len(found),history_records_with_matched_bytes=len(matched),history_records=len({r['id'] for r in rr}),unmatched_hashes=len(missing),limits='Whole stored or decompressed byte match only. An excerpt file is still an excerpt; agency URLs and original capture methods are in the row receipts. A receipt may be for a derived excerpt or a response inside another container. Do not treat unmatched values as on-disk verification.'))
 print(len(found),'of',len(targets),'distinct receipts matched by recomputing file hashes;',len(matched),'records')
 if strict and (missing or len(matched)!=len({r['id'] for r in rr})):raise SystemExit('Missing evidence bytes; see output/receipts/evidence_files.csv')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--strict',action='store_true');run(p.parse_args().strict)
