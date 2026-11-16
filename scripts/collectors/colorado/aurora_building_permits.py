"""City of Aurora Building Division: issued commercial building permit and certificates of occupancy for the QTS DEN1
accessory booth (public records search, Arapahoe County)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.records import rec
from lib.net import get_simple as get
from lib.paths import CACHE
from lib.epa_icis import digest
from urllib.parse import urljoin
import re, html, fitz
D=CACHE/'co'
AUR='https://coaapps.auroragov.org/publicdocuments/publicrecordsearch.aspx?locationkey=227486'
def aurls():
    s=(D/'aurora.html').read_text();ret={}
    for tr in re.findall('<tr[^>]*>(.*?)</tr>',s,re.I|re.S):
        found=re.search(r'\b(B\d{7})\b',tr);ln=re.search(r'''href=['"]([^'"]+)''',tr)
        if found and ln:ret[found[1]]=urljoin(AUR,html.unescape(ln[1]))
    return ret
def download():
    D.mkdir(exist_ok=True,parents=True);(D/'aurora.html').write_bytes(get(AUR))
    for n,fn in [('B1911702','aurora-permit'),('B1973703','B1973703'),('B1982975','B1982975')]:
        (D/(fn+'.pdf')).write_bytes(get(aurls()[n]))
def rows():
    rows=[]
    au=aurls()
    for num,fn,day,role,kind,st,sha in [('B1911702','aurora-permit','2023-11-07','issue date','Commercial building permit','Issued',None),('B1973703','B1973703','2024-06-04','temporary certificate issue date','Temporary certificate of occupancy','Issued temporary','228fd96fcc34725b5d90bdde5238af25221b5e67815a0d5892255ab0b0dc85b6'),('B1982975','B1982975','2024-07-03','certificate issue date','Certificate of occupancy','Issued','9f1d3da81f5f07a357cda984a34770d798c74a3a4d2530c2bdc75ca0385c4856')]:
        p=D/(fn+'.pdf')
        if sha and digest(p)!=sha:raise ValueError('Changed visually reviewed certificate; recheck before release')
        if not sha and '2023-2389684 CM' not in fitz.open(p)[0].get_text():raise ValueError('Issued permit no longer verifies')
        rows.append(rec('CO','aurora-'+num,'Aurora Building Division issued permit and certificates','2023-2389684 CM' if not sha else '2023-2389684-00 CM',kind,st,day,role,au[num],'City document '+num+', p. 1 (date on issued document, not indexing date).','QTS DEN1 – DC1 accessory booth, 1164 N Gun Club Rd','Aurora','Arapahoe County',p,issuer='City of Aurora Building Division',register_url=AUR,scope='Accessory structure only; the certificate does not grant campus-wide occupancy.',certificate_expiration='2024-07-01' if num=='B1973703' else None))
    return rows
