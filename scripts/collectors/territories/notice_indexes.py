"""Fetch public territorial notice indexes and their official eligible links (not portal logins)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, R
import re, sys, hashlib
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin,urlparse,unquote
from html import unescape
from lib.archive import Store
from lib.files import j
import lib.discovery as collect
def run(st,extra):
 S=Store(st);p=collector_data('territories',f'{st.lower()}_supp_sources.json');m=j(p)
 def get(k,url,ext,depth=0):
  if k not in m or 'error' in m[k]:
   try:m[k]=S.get(url,ext)
   except Exception as e:m[k]={'url':url,'error':str(e)}
   collect.dump(p,m)
  if 'error' in m[k]:return ''
  b=S.read(m[k]);return b if isinstance(b,(dict,list)) else b.decode(errors='replace')
 for k,url,ext in extra:
  t=get(k,url,ext)
  if not isinstance(t,str):continue
  links=sorted(set(unescape(urljoin(url,h)) for h in re.findall(r'href=["\']([^"\']+)|<loc>([^<]+)',t) for h in h if h))
  if k=='blog':chosen=[u for u in links if '/post/' in u and re.search(r'pnrs|notice|land-use|public-hearing',u,re.I)]
  elif k=='index' and st=='MP':chosen=[u for u in links if u.startswith('https://dcrm.gov.mp/') and re.search(r'\.pdf($|\?)',u,re.I) ]
  elif k=='index' and st=='VI':chosen=[u for u in links if urlparse(u).hostname in ('dpnr.vi.gov','www.dpnr.vi.gov') and re.search(r'\.pdf($|\?)',u,re.I)]
  else:chosen=[]
  print(st,k,'links',len(links),'eligible',len(chosen),flush=True)
  for u in chosen:
   ext='pdf' if '.pdf' in u.lower() else 'html';get('link_'+hashlib.sha256(u.encode()).hexdigest()[:16],u,ext)
if __name__=='__main__':
 jobs={'AS':[('blog','https://doc.as.gov/blog-posts-sitemap.xml','xml')],'MP':[('index','https://dcrm.gov.mp/our-programs/permitting/notice-of-applications-and-public-notices/','html')],'VI':[('index','https://dpnr.vi.gov/public-notices/','html')]+[(k,'https://dpnr.vi.gov/wp-json/wp/v2/search?per_page=100&search='+v,'json') for k,v in [('search_data','data%20center'),('search_centre','data%20centre'),('search_vingn','viNGN')]]}
 with ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(lambda kv:run(*kv),jobs.items()))
