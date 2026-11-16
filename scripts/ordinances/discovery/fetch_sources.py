"""Fetch independent publishers concurrently, serially within an origin. Single writer."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, json, threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from urllib.parse import urlsplit
import lib.discovery as c
def main():
    p=argparse.ArgumentParser();p.add_argument('--state');p.add_argument('--refresh',action='store_true');a=p.parse_args()
    groups=defaultdict(list)
    for u in sorted({c.address(r[k]) for r in c.rules() if not a.state or r['state']==a.state for k in ('url','primary_document','corroborating_url') if r.get(k)}):
        groups[urlsplit(u).netloc].append(u)
    # Workers have separate per-origin indexes, merged on the main thread.
    from tempfile import TemporaryDirectory
    import subprocess, sys, os
    def group(urls):
        with TemporaryDirectory(dir=c.OUT) as d:
            path=c.Path(d)
            old=c.read(c.INDEX,{})
            c.dump(path/'source_index.json',{u:old[u] for u in urls if u in old})
            child="""import sys,json,lib.discovery as c
c.OUT=c.Path(sys.argv[1]);c.INDEX=c.OUT/'source_index.json';s=c.SourceStore(sys.argv[2]=='yes')
for u in json.load(sys.stdin):s.get(u)
"""
            subprocess.run([sys.executable,'-c',child,d,'yes' if a.refresh else 'no'],input=json.dumps(urls),text=True,cwd=c.R/'scripts',check=True)
            return c.read(path/'source_index.json',{}),(path/'fetch_history.jsonl').read_text() if (path/'fetch_history.jsonl').exists() else ''
    from concurrent.futures import as_completed
    c.OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=10) as pool:
        for f in as_completed([pool.submit(group,urls) for urls in groups.values()]):
            records,history=f.result();idx=c.read(c.INDEX,{});idx.update(records);c.dump(c.INDEX,idx)
            with (c.OUT/'fetch_history.jsonl').open('a') as stream:stream.write(history)
            print(len(records),'documents from',urlsplit(next(iter(records))).netloc,flush=True)
if __name__=='__main__':main()
