"""Optional macOS OCR review for text-poor official notice pages; snapshots are portable."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, R
import io, json, subprocess, tempfile
from pypdf import PdfReader,PdfWriter
from lib.archive import Store
from lib.files import j
import lib.discovery as collect
def run():
 base=R/'cache/history/territorial/notice_ocr';base.mkdir(exist_ok=True,parents=True)
 with tempfile.TemporaryDirectory(dir=base) as tmp:
  from pathlib import Path
  d=Path(tmp);exe=d/'ocr';subprocess.run(['swiftc',str(R/'scripts/lib/ocr_vision.swift'),'-o',str(exe)],check=True)
  for st,x in j(collector_data('territories','territorial_review.json')).items():
   if st=='AS':continue
   s=Store(st);m=j(collector_data('territories',f'{st.lower()}_supp_sources.json'))
   for z in x['linked_pdf_or_notice_documents']:
    if not z.get('text_poor_pages'):continue
    out=base/(z['sha256']+'.json')
    if out.exists():continue
    pdf=PdfReader(io.BytesIO(s.read(m[z['key']])));w=PdfWriter()
    for p in z['text_poor_pages']:w.add_page(pdf.pages[p-1])
    pp=d/'selected.pdf';w.write(pp);lines=json.loads(subprocess.check_output([exe,pp,str(len(z['text_poor_pages']))]));collect.dump(out,{str(n):' '.join(v) for n,v in zip(z['text_poor_pages'],lines)})
if __name__=='__main__':run()
