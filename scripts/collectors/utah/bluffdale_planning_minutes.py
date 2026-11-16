"""Bluffdale City Planning Commission: minutes of the 6 December 2023 meeting (Project Inabi Edge Data Center site plan)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import fitz
from lib.paths import CACHE
from lib.net import get_simple as get
from lib.records import rec
D=CACHE/'ut'
BL='https://www.bluffdale.gov/AgendaCenter/ViewFile/Minutes/_12062023-1316'
def download():(D/'bluffdale.pdf').write_bytes(get(BL))
def rows():
    p=D/'bluffdale.pdf';d=fitz.open(p);t=' '.join(' '.join(d[i].get_text().split()) for i in (10,11))
    if not all(x in t for x in ('2023-24','motion passed unanimously','South Valley Sewer District')):raise ValueError('Bluffdale primary minutes changed')
    return [rec('UT','bluffdale-inabi','Bluffdale Planning Commission decisions','2023-24','Conditional site plan decision','motion passed unanimously','2023-12-06','commission vote date',BL,'PDF pp. 11–12, site plan motion, eleven conditions, 5–0 vote','Project Inabi Edge Data Center','Bluffdale','Salt Lake County',p,issuer='Bluffdale Planning Commission',conditions='UDOT access, sewer district approval, Phase 2 municipal boundary and plat, easements, stamped drawings, fire review and site plan requirements.')]
