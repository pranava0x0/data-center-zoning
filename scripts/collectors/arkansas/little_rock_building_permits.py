"""City of Little Rock, Arkansas municipal building permits (ArcGIS Permits MapServer layers 0 and 1)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from lib.paths import CACHE
from lib.net import query
from lib.arcgis import snapshot as arc
from lib.terms import pred, EX
from lib.records import rec
from lib.files import unpack
D=CACHE/'ar';B='https://maps.littlerock.gov/server/rest/services/Permits/MapServer/';F='OBJECTID PermitNumber ProjectDesc AppDate PermitIssueDate PermitStatus PropertyAddress PropertyCity Jurisdiction BldUseDesc PermitMileStone WorkClass PermitType PermitDesc PermitExpireDate CertificateofOccupancyDate LandUseDesc'.split();S=['ProjectDesc','BldUseDesc','PermitDesc','LandUseDesc']
LR='Little Rock municipal permits'
def city(i):arc(B+str(i),pred(S),F,D/('lr-hits-'+str(i)+'.json.gz'))
def download():
 with ThreadPoolExecutor(max_workers=2) as t:list(t.map(city,range(2)))
def rows():
 rows=[];dedup=set()
 for i in range(2):
    p=D/('lr-hits-'+str(i)+'.json.gz')
    for r in unpack(p)['rows']:
        no=r['PermitNumber'];txt=r['ProjectDesc'] or ''
        if 'crypto mining' in txt.casefold() or not EX.search(txt):continue
        if no in dedup:continue
        dedup.add(no);u=query(B+str(i)+'/query',where="PermitNumber='"+no+"'",outFields=','.join(F),returnGeometry='false',f='pjson')
        rows.append(rec('AR','lr-'+no,LR,no,r['PermitDesc'],r['PermitStatus'],(r['PermitIssueDate'] or r['AppDate'] or '')[:10] or None,'municipal issue date' if r['PermitIssueDate'] else 'application date',u,'City permit '+no+'; repeated fee rows collapsed.',txt,'Little Rock','Pulaski County',p,milestone=r['PermitMileStone'],address=r['PropertyAddress']))
 return rows,[unpack(D/('lr-hits-'+str(i)+'.json.gz'))['count'] for i in range(2)]
