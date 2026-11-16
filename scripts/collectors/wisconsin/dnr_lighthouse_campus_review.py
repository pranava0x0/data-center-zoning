"""Wisconsin DNR Lighthouse (Vantage, Port Washington) campus review page: state project actions for the sewer area, water main,
stormwater, wetland, environmental analysis and air hearing."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import CACHE
from lib.records import rec
from lib.net import get_simple as get
from lib.text import strip
D=CACHE/'wi';E='https://dnr.wisconsin.gov/topic/EIA/Portwashington.html';P='Wisconsin DNR Lighthouse campus review'
def download():
 D.mkdir(parents=True,exist_ok=True);(D/'port.html').write_bytes(get(E))
def rows():
 rows=[]
 p=D/'port.html';s=strip(p.read_text());place='Port Washington';site='Vantage Lighthouse data center';county='Ozaukee County'
 def e(key,n,kind,st,dt,role,phrase):
    if phrase not in s:raise ValueError('Changed project record '+phrase)
    rows.append(rec('WI','lighthouse-'+key,P,n,kind,st,dt,role,E,phrase,site,place,county,p,issuer='Wisconsin DNR',record_number_is='Project action locator unless a permit is explicitly numbered'))
 for key,n,kind,st,dt,role,phrase in [
 ('sewer-plan','Lighthouse / sewer service area amendment','Sewer service area amendment','submitted a request','2025-09-22','request submitted','submitted a request for administrative approval'),
 ('water-main','Lighthouse / water supply main','Water supply main plan','plans & specifications','2025-09-25','city plan submitted','construction of a water supply main'),
 ('sewer-main','Lighthouse / sanitary sewer interceptor','Sanitary sewer interceptor plan','plans & specifications','2025-09-25','city plan submitted','construction of a sanitary sewer interceptor'),
 ('storm-app','Lighthouse / stormwater request','Construction stormwater application','request for coverage','2025-10-10','request submitted','request for coverage under the stormwater'),
 ('wet-ex','Lighthouse / wetland exemption determinations','Nonfederal wetland determinations','granted','2025-12-11','exemption determination date','granted nonfederal wetland exemption determinations'),
 ('storm-cov','Lighthouse / stormwater coverage','Construction stormwater coverage','conveyed','2025-12-11','coverage decision date','conveyed stormwater permit coverage'),
 ('ea','Lighthouse / environmental analysis','Environmental review','Environmental Analysis Summary','2025-12-09','report release date','released an Environmental Analysis Summary'),
 ('wepa','Lighthouse / WEPA','Environmental review','Compliance Determination','2025-12-11','decision date','issued a WEPA Compliance Determination'),
 ('eas','Lighthouse / supplementary environmental analysis','Environmental review','supplemental report','2026-06-12','report release date','released a supplemental report'),
 ('hear','25-MIN-094 / 24618528A-F01','Air public hearing','public hearing held','2026-04-14','public hearing date','public hearing held on April 14, 2026')]:e(key,n,kind,st,dt,role,phrase)
 return rows
