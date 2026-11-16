"""Offline scope audit of agency notice indexes; positives are review leads, never permits."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, R
from lib.archive import Store
from lib.files import j
import lib.discovery as collect
import re, io, warnings, logging
from html.parser import HTMLParser
from pypdf import PdfReader
logging.getLogger('pypdf').setLevel(logging.ERROR)
class Text(HTMLParser):
 def __init__(self):super().__init__();self.hidden=0;self.words=[]
 def handle_starttag(self,t,a):
  if t in ('style','script','noscript'):self.hidden+=1
 def handle_endtag(self,t):
  if t in ('style','script','noscript'):self.hidden=max(0,self.hidden-1)
 def handle_data(self,t):
  if not self.hidden:self.words.append(t)
def html(b):
 h=Text();h.feed(b.decode('utf8',errors='replace'));return ' '.join(' '.join(h.words).split())
pattern=re.compile(r'\b(?:data\s*cent(?:er|re)s?|co[- ]?location|server\s+(?:farms?|halls?)|critical\s+hub)\b',re.I)
def build():
 all={}
 for st in ('MP','VI','AS'):
  S=Store(st);m=j(collector_data('territories',f'{st.lower()}_supp_sources.json'));seen={};pages=[];other={}
  for key,r in m.items():
   if 'error' in r:pages.append(dict(key=key,url=r['url'],error=r['error']));continue
   if key.startswith('search_'):
    other[key]=[dict(id=v['id'],title=v['title'],url=v['url']) for v in S.read(r)];continue
   if not (key.startswith('link_') or st=='VI' and key in ['q1','q4'] or st=='MP' and key.startswith('packet_')):continue
   if r['sha256'] in seen:continue
   seen[r['sha256']]=1;b=S.read(r);n=1;weakpages=[];err=None
   try:
    if r['ext']=='pdf':
     pdf=PdfReader(io.BytesIO(b));n=len(pdf.pages);txt=[]
     for i,p in enumerate(pdf.pages,1):
      t=' '.join((p.extract_text() or '').split());txt.append(t)
      if len(re.sub(r'[^a-z]','',t.lower()))<65:weakpages.append(i)
    else:txt=[html(b)]
   except Exception as e:txt=[];err=str(e)
   hits=[dict(page=i,excerpt=t[max(0,a.start()-40):a.end()+50]) for i,t in enumerate(txt,1) for a in pattern.finditer(t)]
   if st=='AS':hits=[z for z in hits if 'Copyright' not in z['excerpt']]
   rec=dict(key=key,url=r['url'],sha256=r['sha256'],pages=n,text_poor_pages=weakpages,hits=hits)
   ocr=R/'cache/history/territorial/notice_ocr'/(r['sha256']+'.json')
   if ocr.exists():
    from hashlib import sha256
    extra=j(ocr);assert sorted(int(i) for i in extra)==sorted(weakpages)
    rec['ocr_review']={'path':str(ocr.relative_to(R)),'sha256':sha256(ocr.read_bytes()).hexdigest(),'pages':list(map(int,extra)),'text_poor_after_ocr':[int(i) for i,t in extra.items() if len(re.sub(r'[^a-z]','',t.lower()))<65],'hits':[dict(page=int(i),excerpt=t[max(0,a.start()-40):a.end()+50]) for i,t in extra.items() for a in pattern.finditer(t)]}
   if err:rec['error']=err
   pages.append(rec)
  all[st]=dict(linked_pdf_or_notice_documents=pages,discovery_links=sum(k.startswith('link_') for k in m),wordpress_site_search=other,search_expressions=pattern.pattern)
 collect.dump(collector_data('territories','territorial_review.json'),all)
 for st,z in all.items():
  print(st,len(z['linked_pdf_or_notice_documents']),'unique documents',z['discovery_links'],'linked',sum(bool(p.get('hits')) for p in z['linked_pdf_or_notice_documents']),'text positive,',sum(bool(p.get('text_poor_pages')) for p in z['linked_pdf_or_notice_documents']),'with weak pages',sum('error' in p for p in z['linked_pdf_or_notice_documents']),'errors')
  for p in z['linked_pdf_or_notice_documents']:
   if p.get('hits'):print(' ',p['url'],p['hits'][:2])
if __name__=='__main__':build()
