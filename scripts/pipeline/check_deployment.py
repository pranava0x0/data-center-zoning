"""Verify the deployed Pages release, hashes and tabular downloads over HTTPS."""
import argparse,csv,hashlib,io,json,time,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('base',nargs='?',default='https://pranava0x0.github.io/data-center-zoning/');a=ap.parse_args();base=a.base.rstrip('/')+'/'
 def fetch(path):
  begin=time.perf_counter()
  with urllib.request.urlopen(base+path,timeout=40) as r:b=r.read();headers=dict(r.headers)
  return b,round((time.perf_counter()-begin)*1000),headers
 manifest=json.loads(fetch('downloads/manifest.json')[0]);results=[]
 def verify(item):
  b,ms,headers=fetch('downloads/'+item['name'])
  if hashlib.sha256(b).hexdigest()!=item['sha256']:raise ValueError('Published hash differs: '+item['name'])
  if len(b)!=item['bytes']:raise ValueError('Published size differs: '+item['name'])
  if 'rows' in item and len(list(csv.DictReader(io.StringIO(b.decode()))))!=item['rows']:raise ValueError('Published row count differs: '+item['name'])
  return dict(path=item['name'],bytes=len(b),transfer_ms=ms)
 results=list(ThreadPoolExecutor(max_workers=4).map(verify,manifest['files']))
 pages=[]
 for name in ['index.html','downloads.html','about.html','records.html','telecom.html','llms.txt','robots.txt','sitemap.xml']:
  b,ms,headers=fetch(name)
  if b!=(R/'_site'/name).read_bytes():raise ValueError('Deployed page differs from validated local artifact: '+name)
  pages.append(dict(path=name,bytes=len(b),transfer_ms=ms,cache_control=headers.get('Cache-Control')))
 report=dict(passed=True,base=base,release=manifest['release'],pages=pages,downloads=results)
 (R/'output/deployment_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(f"Verified {len(results)} deployed downloads and {len(pages)} pages against local validated bytes")
if __name__=='__main__':main()
