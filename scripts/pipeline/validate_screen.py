"""Check the website search ledger against its compressed source bytes."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
from collections import Counter
import csv, gzip, hashlib, json
from pathlib import Path
import lib.discovery as c
def main():
    d=json.loads((c.OUT/'local_screen.json').read_text());frame=list(csv.DictReader((c.R/'data/jurisdictions.csv').open()));ids={r['geoid'] for r in frame}
    assert sum(d['counts'].values())==len(ids)
    hashes=set();hits=0
    for gid,r in d['rows'].items():
        assert gid in ids
        if r['result'] in ('possible mention','no keyword match'):
            assert r['pages'] and r['entry']
            assert bool(any(p['hits'] for p in r['pages']))==(r['result']=='possible mention')
        else:assert not r['pages']
        for p in r['pages']:
            h=p['sha256'];assert p['url'].startswith(('http://','https://'))
            if h not in hashes:
                b=gzip.decompress((c.R/'cache/local-screen/pages'/(h+'.gz')).read_bytes())
                assert hashlib.sha256(b).hexdigest()==h;hashes.add(h)
    c.dump(c.OUT/'local_screen_checks.json',dict(geographies=len(ids),unique_pages_verified=len(hashes),counts=d['counts']))
    print(len(hashes),'local source snapshots verified;',len(ids),'geographies reconciled')
if __name__=='__main__':main()
