"""Colorado Springs (Legistar land-use appeals): Project Taurus / Corporate Ridge Filing No. 1 development plan appeal
before the City Planning Commission and City Council."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.records import rec
from lib.net import get_simple as get
from lib.paths import CACHE
import re, html
D=CACHE/'co'
TAUR='https://coloradosprings.legistar.com/LegislationDetail.aspx?GUID=853D9C19-EC34-4B05-9143-0ED4D10307E4&ID=8206955'
def text(s):return ' '.join(html.unescape(re.sub('<[^>]+>',' ',s)).split())
def download():
    D.mkdir(exist_ok=True,parents=True);(D/'taurus.html').write_bytes(get(TAUR))
def rows():
    rows=[]
    p=D/'taurus.html';s=text(p.read_text())
    for dt,term,st,agency in [('2026-07-23','7/23/2026','approved','City Planning Commission'),('2026-09-17','9/17/2026','postpone to a date certain','City Council')]:
        if not (term in s and st in s and 'denied multiple appeals' in s):raise ValueError('Appeal docket changed')
        rows.append(rec('CO','taurus-'+dt,'Colorado Springs land-use appeals','APPL PROJ. TAURUS','Development plan appeal',st,dt,'commission/council action date',TAUR,'History tab: passed motion, '+agency+'; case summary and related files.','Project Taurus / Corporate Ridge Filing No. 1, 1565 High Tech Way','Colorado Springs','El Paso County',p,issuer='Colorado Springs '+agency,scope='Commission denied appeals and approved modification with conditions. Council later postponed action, not final Council approval.'))
    return rows
