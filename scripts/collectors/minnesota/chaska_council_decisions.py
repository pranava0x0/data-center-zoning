"""City of Chaska Planning Commission and City Council decisions on the Cloud HQ campus. Issuers: Chaska
Planning Commission and City Council."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import html, re
from lib.net import get_simple as get, query
from lib.files import pack, unpack
from lib.records import rec
from lib.paths import CACHE
import json
D=CACHE/'mn'
C='https://www.chaskamn.gov/841/Cloud-HQ'
def download():
    D.mkdir(parents=True,exist_ok=True);(D/'cloud-hq.html').write_bytes(get(C))
def rows():
    rows=[]
    p=D/'cloud-hq.html';page=' '.join(html.unescape(re.sub('<[^>]+>',' ',p.read_text())).split())
    for stage,ds,dt,board,item in [('Concept approval','August 10th, 2022','2022-08-10','Planning Commission','7C'),('Concept approval','August 15th, 2022','2022-08-15','City Council','8B'),('Final AUAR adoption','January 9, 2023','2023-01-09','City Council','9.M'),('Conditional use permit decision','October 11th, 2023','2023-10-11','Planning Commission','7A'),('Conditional use permit decision','October 16th, 2023','2023-10-16','City Council','9B'),('Preliminary site plan and plat decision','October 9th, 2024','2024-10-09','Planning Commission','7A'),('Preliminary site plan and plat decision','October 21st, 2024','2024-10-21','City Council','8A')]:
        if ds not in page:raise ValueError('Chaska source shifted '+ds)
        rows.append(rec('MN','chaska-'+dt,'Chaska Cloud HQ municipal decisions',dt+' item '+item,stage,'adopted' if 'adoption' in stage else 'Approval',dt,'board action date',C,board+' agenda item '+item,'Cloud HQ, 2007 Schoolmaster Dr.','Chaska','Carver County',p,issuer='Chaska '+board,scope='City distinguishes preliminary approvals from unsubmitted final site/plat application.'))
    return rows
