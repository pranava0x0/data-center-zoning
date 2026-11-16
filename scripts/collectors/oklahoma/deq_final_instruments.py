"""Oklahoma DEQ final data-center instruments: issued air (AQD), water and land (WQD/LPD) permit PDFs linked from the
DEQ register. rows logic dates and classifies each PDF (optionally from the cover-page OCR cache); ocr() rebuilds it."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re, io, datetime as dt
from urllib.parse import unquote
from pypdf import PdfReader
from lib.paths import collector_data, R
import lib.discovery as collect
from collectors.oklahoma.common import ST
dm=r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}'
def ocr(m):
    import subprocess, tempfile, json
    from pypdf import PdfWriter
    arr=[];w=PdfWriter()
    for u,r in m['proofs'].items():
        if not r.get('sha256'):continue
        b=ST.read(r)
        if not b.startswith(b'%PDF'):continue
        p=PdfReader(io.BytesIO(b));t=' '.join(p.pages[0].extract_text().split())
        if len(t)>90:continue
        for i in range(min(2,len(p.pages))):w.add_page(p.pages[i]);arr.append((r['sha256'],i+1))
    with tempfile.TemporaryDirectory(dir=ST.d) as d:
        p=R/d/'covers.pdf'
        with p.open('wb') as f:w.write(f)
        z=json.loads(subprocess.run(['swift',str(R/'scripts/lib/ocr_vision.swift'),str(p),str(len(arr))],check=True,capture_output=True).stdout)
    dic={}
    for (h,i),lines in zip(arr,z):dic.setdefault(h,{})[str(i)]=lines
    collect.dump(collector_data('oklahoma','ocr.json'),dic)
def from_pdf(m,oo,issued,out,holds,i,div,county,fac,url,r,det):
    """Date and classify one proof PDF. Returns (num,day,role,kind,ds), or None when the row is held."""
    b=ST.read(r);p=PdfReader(io.BytesIO(b))
    def pg(n):return ' '.join(oo[r['sha256']][str(n)]) if r['sha256'] in oo else ' '.join(p.pages[n-1].extract_text().split())
    t=pg(1);role='issuance date not stated';ds='Oklahoma DEQ final data-center instruments';day=None
    if div=='AQD':
        num=re.search(r'\b(\d{4}-\d{3,4}-(?:TVR|AD|C|O)(?: M-\d+)?)',unquote(url),re.I)[1].upper()
        if num=='2025-0940-O' and county!='MUSKOGEE':holds.append(dict(row=i,name=fac,reason='Linked instrument explicitly locates its site in Muskogee County, not the index row county.'));return None
        if num in out:holds.append(dict(row=i,name=fac,reason='Duplicate index row referencing the same document and permit number.'));return None
        kind=('Air applicability determination' if '-AD' in num else 'Air permit by rule registration' if 'PBR Registration' in t else 'Title V operating permit' if 'TVR' in num else 'Air construction permit' if '-C' in num else 'Air operating permit')
        if num in issued:day=issued[num]['Date Issued'];role='agency register issue date';det['date_source']=m['issued_csv']['url']
        else:
            source=t
            if 'CONFIDENTIAL FILE NOTICE' in t:source=pg(2)
            if num=='2007-021-AD M-1':source=pg(2)
            q=re.search(dm,source,re.I)
            if q and ('MEMORANDUM' in source[:140] or num in ('2001-002-O M-1','2022-0496-O','2019-0668-AD M-1')):
                day=dt.datetime.strptime(q[0].title(),'%B %d, %Y').date().isoformat();role='agency memorandum date' if 'MEMORANDUM' in source[:140] else 'agency letter date'
            if num=='2019-0668-AD' and 'AUG 2 1 2019' in t:day='2019-08-21';role='agency letter date'
    else:
        num=re.search(r'(?:DEQ )?Permit No\.\s*((?:WL|SL|OK)[A-Z0-9]+)',t,re.I)[1];kind='Water line construction permit' if num.startswith('WL') else 'Sewer line construction permit' if num.startswith('SL') else 'OPDES industrial wastewater discharge permit'
        q=re.search(dm,t);day=dt.datetime.strptime(q[0],'%B %d, %Y').date().isoformat();role='agency transmittal date'
        if num=='OK0100439':det.update(effective='2025-08-01',expires='2030-07-31')
    det['evidence_page']=1
    return num,day,role,kind,ds
