"""Colorado Department of Public Health and Environment, Air Pollution Control Division: public notices of proposed
construction permits (EdgeConneX Denver Campus draft air permit notice, Douglas County)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.records import rec
from lib.net import get_simple as get
from lib.paths import CACHE
import fitz
D=CACHE/'co'
NOT='https://publicnotices.douglasco.gov/files/public-notices/1-6-2026-State-of-Colorado-Dept-of-Public-Health-Environment-Draft-Air-Permit.pdf'
def download():
    D.mkdir(exist_ok=True,parents=True);(D/'edge-notice.pdf').write_bytes(get(NOT))
def rows():
    rows=[]
    p=D/'edge-notice.pdf'
    if '25DG0038' not in fitz.open(p)[0].get_text():raise ValueError('Draft notice changed')
    rows.append(rec('CO','edge-notice','Colorado APCD public notices','25DG0038','Draft air construction permit','Notice of a Proposed Construction Permit Warranting Public Comment','2026-01-06','notice period begins',NOT,'p. 1 permit and start date','EdgeConneX Denver Campus, second building','Douglas County','Douglas County',p,issuer='Colorado Air Pollution Control Division',mailing_city='Englewood',address='8451 Highfield Pkwy'))
    return rows
