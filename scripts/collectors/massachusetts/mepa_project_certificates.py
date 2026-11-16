"""Massachusetts Executive Office of Energy and Environmental Affairs MEPA certificates (EEA 15988, Markley Data Center and 2385 Line
Maintenance Project) and the MassDEP 401 certification the Secretary certificate cites."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import CACHE
from lib.records import rec
from lib.net import get_simple as get
import fitz
D=CACHE/'ma'
MEPA='https://eeaonline.eea.state.ma.us/EEA/emepa/mepacerts/2020/sc/npc/15988%20NPC%20Markley%20Data%20Center%202385%20Line%20FINAL.pdf'
def download():
 D.mkdir(exist_ok=True,parents=True);(D/'mepa.pdf').write_bytes(get(MEPA))
def rows():
 rows=[]
 p=D/'mepa.pdf';s=' '.join(' '.join(pg.get_text().split()) for pg in fitz.open(p))
 for id,dt,role,kind,status,phrase in [('notice','2020-10-22','monitor notice date','Notice of project change','Notice of Project Change','October 22, 2020'),('cert','2020-11-23','secretary decision date','MEPA project change determination','does not require an Environmental Impact Report','November 23, 2020')]:
    if phrase not in s or '15988' not in s:raise ValueError('MEPA certificate changed')
    rows.append(rec('MA','mepa-'+id,'Massachusetts MEPA project certificates','15988',kind,status,dt,role,MEPA,'Certificate page 1; project municipalities and project scope.','Markley Data Center and 2385 Line Maintenance Project','Middlesex County','Middlesex County',p,project_places=['Lowell','Billerica','Tewksbury'],scope='Electrical distribution upgrades serving data center and broader grid; not a campus building permit.'))
 if '401 Water Quality Certification (WQC) from the MassDEP which was issued on July 11, 2019' not in s:raise ValueError('MassDEP certificate source changed')
 rows.append(rec('MA','mepa-401','MassDEP prior certifications cited in MEPA','EEA 15988 / 401 WQC','State water quality certification','issued','2019-07-11','prior certificate issue date',MEPA,'Secretary certificate, permits and jurisdiction discussion; individual 401 certificate number not provided.','Markley 2385 distribution line','Middlesex County','Middlesex County',p,scope='Power line supporting Markley; EEA number is not a 401 permit number.'))
 return rows
