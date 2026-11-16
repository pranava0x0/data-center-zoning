"""Iowa Department of Natural Resources signed Title V air operating permits (PDFs on iowadnr.gov) for data center plants."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import datetime
import fitz
from lib.net import get_simple as get
from lib.paths import CACHE
from lib.records import rec
D=CACHE/'ia'
ATT='https://www.iowadnr.gov/media/{}/download?inline'
OPS={'2742':('543','16-TV-002R1','2021-09-07','2026-09-06'),'9555':('10747','26-TV-003','2026-04-10','2031-04-09'),'7168':('11432','24-TV-005','2024-12-09','2029-12-08'),'6245':('7968','24-TV-004','2024-10-17','2029-10-16'),'2908':('11381','18-TV-007R1','2024-04-08','2029-04-07')}
TV='Iowa DNR signed Title V operating permits'
def download():
    D.mkdir(parents=True,exist_ok=True)
    for i in OPS:(D/('op-'+i+'.pdf')).write_bytes(get(ATT.format(i)))
def rows(names):
    rows=[]
    for i,(id,n,dt,exp) in sorted(OPS.items()):
        name,place,county,facility=names[id];p=D/('op-'+i+'.pdf');doc=fitz.open(p);cover=' '.join(doc[0].get_text().split());day=datetime.fromisoformat(dt);expday=datetime.fromisoformat(exp)
        variants=lambda day:[day.strftime(fmt) for fmt in ['%m/%d/%Y','%-m/%-d/%Y','%m/%d/%y','%-m/%-d/%y','%B %-d, %Y']]
        if not (n in cover and facility in cover and any(v in cover for v in variants(day)) and any(v in cover for v in variants(expday))):raise ValueError('Changed signed cover '+i)
        if id=='11381' and '518210' not in ''.join(x.get_text() for x in doc):raise ValueError('Siculus association changed')
        rows.append(rec('IA','tv-'+i,TV,n,'Title V air operating permit','Issued',dt,'signed issue date',ATT.format(i),'Page 1, signed Title V cover; facility file '+facility,'Gable Corporation (Questa LLC)' if id=='543' else name,place,county,p,plant_number=facility,printed_expiration=exp))
    return rows
