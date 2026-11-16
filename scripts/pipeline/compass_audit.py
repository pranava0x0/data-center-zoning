"""Re-audit public edition workbooks and downloaded search manifests; never execute document code."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, gzip, io
from urllib.request import urlopen,Request
from openpyxl import load_workbook
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import lib.discovery as c
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--fetch',action='store_true',help='Download missing archive files');a=ap.parse_args()
    folder=c.R/'cache/compass';folder.mkdir(exist_ok=True)
    def acquire(url,sha):
        f=folder/sha
        if not f.exists():
            if not a.fetch:raise ValueError('Missing cached OEDI resource; use --fetch')
            with urlopen(Request(url,headers={'User-Agent':c.AGENT}),timeout=60) as r:b=r.read()
            if c.digest(b)!=sha:raise ValueError('Source drift: '+url)
            f.write_bytes(b)
        b=f.read_bytes()
        if c.digest(b)!=sha:raise ValueError('Corrupt cached file: '+url)
        return b
    def check(r):
        urls=r['resources'];audit=r['workbook_audit']
        url=next(x for x in urls if x.lower().endswith('.xlsx'))
        book=load_workbook(io.BytesIO(acquire(url,audit['sha256'])),read_only=True,data_only=True)
        rows=book['All Ordinances'].values;heads=next(h for h in rows if 'State' in h and 'Feature' in h);st=heads.index('State');ft=heads.index('Feature')
        freq=Counter(str(x[ft]).strip() for x in rows if x[st] and x[ft]);book.close()
        if freq!=Counter(audit['feature_frequencies']):raise ValueError('Feature frequencies differ: '+r['technology'])
        out=dict(technology=r['technology'],rows=sum(freq.values()),url=url,sha256=audit['sha256'])
        if r.get('search_manifest_audit'):
            m=r['search_manifest_audit'];u=next(u for u in urls if '.csv' in u.lower())
            b=acquire(u,m['sha256_download'])
            if b.startswith(b'\x1f\x8b'):b=gzip.decompress(b)
            n=sum(1 for x in csv.DictReader(io.StringIO(b.decode('utf-8-sig'))) if any(x.values()))
            if m['data_rows']!=n:raise ValueError('Manifest row mismatch')
            out['search_rows']=n
        return out
    src=[r for r in c.read(c.R/'data/compass_sources.json',{})['releases'] if r['release_kind']=='compass']
    with ThreadPoolExecutor(max_workers=3) as pool:out=list(pool.map(check,src))
    c.dump(c.OUT/'compass_audit.json',out);print(len(out),'workbooks;',sum(x['rows'] for x in out),'feature rows')
if __name__=='__main__':main()
