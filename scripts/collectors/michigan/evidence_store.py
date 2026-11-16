"""Michigan shared evidence store (hash-pinned archive for MI) plus the text-extraction and record helpers used by every source module."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R
import io, datetime as dt
import lib.net as netfetch
import lib.discovery as collect
from pypdf import PdfReader
from lib.archive import Store
from lib.files import j
from lib.text import htmltext
ST=Store('MI');M=collector_data('michigan','manifest.json');C=collector_data('michigan','config.json');O=series_path('mi');A=collector_data('michigan','coverage.json')
def fetch_keys(m,keys):
    for k,x in j(C).items():
        if k not in keys:continue
        if k in m and not netfetch.REFETCH:continue
        try:ref=ST.get(x['url'],x['ext'])
        except (OSError,ValueError) as e:ref=dict(url=x['url'],error=str(e))
        m[k]=ref;collect.dump(M,m)
def make(m,out):
    from functools import lru_cache
    ocr=j(collector_data('michigan','ocr.json'))
    @lru_cache()
    def doc(k):
        return PdfReader(io.BytesIO(ST.read(m[k])))
    def txt(k,p):
        if k in ocr and str(p) in ocr[k]['pages']:
            if ocr[k]['sha256']!=m[k]['sha256']:raise ValueError('OCR snapshot differs')
            ST.read(m[k]);return ' '.join(ocr[k]['pages'][str(p)])
        if m[k]['ext']=='pdf':return ' '.join(doc(k).pages[p-1].extract_text().split())
        return htmltext(ST.read(m[k]))
    def add(k,p,needle,id,ds,jur,num,proj,kind,status,day,role,loc,**de):
        t=txt(k,p);norm=lambda s:' '.join(s.lower().split())
        if norm(needle) not in norm(t):raise ValueError(k+' missing '+needle)
        r=m[k];out.append(dict(id='mi-'+id,state='MI',dataset=ds,jurisdiction=jur,record_no=num,project=proj,kind=kind,status=status,date=day,date_role=role,url=r['url']+('#page='+str(p) if p and r['ext']=='pdf' else ''),source_url=r['url'],locator=loc,details=dict(source_sha256=r['sha256'],evidence=needle,**de)))
    return txt,add
