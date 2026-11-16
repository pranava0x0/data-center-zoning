"""Query Oregon DLCD's public adopted-amendment form; preserves original and POST filter."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.oregon.portland_west_metro import *
from html.parser import HTMLParser
from urllib.request import build_opener, HTTPCookieProcessor,Request
from http.cookiejar import CookieJar
from urllib.parse import urlencode,urljoin
class Inputs(HTMLParser):
 def __init__(self):super().__init__();self.inputs={}
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='input' and d.get('type')=='hidden' and d.get('name'):self.inputs[d['name']]=d.get('value','')
def get():
 m=existing(M);key='or_hil_dlcdfiling';url=SOURCES['or_state_reporting'][1];collect.policy(url)
 op=build_opener(HTTPCookieProcessor(CookieJar()));op.addheaders=[('User-Agent',collect.AGENT)]
 resp=op.open(url,timeout=30);t=resp.read().decode();p=Inputs();p.feed(t)
 q=dict(txtFromDate='10/01/2026',txtToDate='11/16/2026',ddlJurisdictionID='110',btnGo='Go')
 b=op.open(Request(resp.geturl(),data=urlencode(dict(p.inputs,**q)).encode()),timeout=50).read()
 assert b'10/01/2026' in b or b'10/1/2026' in b, 'Form did not retain date filter'
 h=hashlib.sha256(b).hexdigest();fn=D/(h+'.html');fn.write_bytes(b)
 m[key]=dict(url=url,request_method='POST',query_fields=q,sha256=h,bytes=len(b),ext='html',path=str(fn.relative_to(R)),retrieved=datetime.now(timezone.utc).isoformat())
 v=Inputs();v.feed(b.decode());asyncq=dict(v.inputs,txtFromDate=q['txtFromDate'],txtToDate=q['txtToDate'],ddlJurisdictionID=q['ddlJurisdictionID'],__EVENTTARGET='rv$ctl13$Reserved_AsyncLoadTarget',__EVENTARGUMENT='')
 b=op.open(Request(resp.geturl(),data=urlencode(asyncq).encode()),timeout=45).read()
 export=urljoin(url,json.loads(re.search(r'"ExportUrlBase":("[^"]+")',b.decode())[1])+'PDF')
 collect.policy(export);doc=op.open(export,timeout=60).read();assert doc.startswith(b'%PDF'),doc[:100]
 text=' '.join(' '.join(pg.extract_text().split()) for pg in PdfReader(io.BytesIO(doc)).pages)
 print(text[:220],text[-220:]);assert ('10/01/2026' in text or '10/1/2026' in text) and 'Hillsboro' in text, 'Export ignored selected filters'
 sha=hashlib.sha256(doc).hexdigest();path=D/(sha+'.pdf');path.write_bytes(doc)
 m['or_hil_dlcdreport']=dict(url=url,request_method='POST form + public report PDF',query_fields=q,sha256=sha,bytes=len(doc),ext='pdf',path=str(path.relative_to(R)),retrieved=datetime.now(timezone.utc).isoformat());collect.dump(M,m)
 rd=PdfReader(path)
 for pg in rd.pages:
  print(pg.extract_text()[:1150]);print([o.get_object().get('/A',{}).get('/URI') for o in pg.get('/Annots',[])][:15])
if __name__=='__main__':get()
