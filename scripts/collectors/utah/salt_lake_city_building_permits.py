"""Salt Lake City Building Services: Accela permit workflow layers from the city's public GIS (maps.slc.gov)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import CACHE
from lib.arcgis import snapshot as arc
from lib.terms import pred, EX
from lib.text import ms
from lib.files import unpack
from lib.net import query
from lib.records import rec
from concurrent.futures import ThreadPoolExecutor
D=CACHE/'ut';SL='https://maps.slc.gov/server/rest/services/Accela/Accela_Permits_v2/MapServer/'
LAY={0:(['DescriptionOfWork'],['OBJECTID','permitNumber','permitType','permitOpenDate','permiteStatus','workType','DescriptionOfWork','siteAddress']),1:(['ProjectName','WorkDescription'],['OBJECTID','PermitNumber','RecordType','ProjectName','WorkDescription','ApplicationStatus','TypeOfWork','FULL_','AppliedDate','PermitIssuance','CertificateIssuance']),2:(['Description'],['OBJECTID','PermitNumber','B1_PER_TYPE','Description']),3:(['freshFromSQL_ProjectName','freshFromSQL_Description'],['OBJECTID','freshFromSQL_PermitNum','freshFromSQL_ProjectName','freshFromSQL_Description','freshFromSQL_ApplicationStatus','freshFromSQL_AppliedDate','freshFromSQL_IssuedDate','freshFromSQL_ApplicationSubType'])}
def download():
    D.mkdir(exist_ok=True,parents=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda v:arc(SL+str(v),pred(LAY[v][0]),LAY[v][1],D/('slc-'+str(v)+'.json.gz')),LAY))
def rows():
    """Records plus the per-layer row counts the validation file reports."""
    rows=[];qc={}
    for i in LAY:
        p=D/('slc-'+str(i)+'.json.gz');a=unpack(p);qc['Salt Lake City layer '+str(i)]=a['count']
        for r in a['rows']:
            if not EX.search(' '.join(str(r.get(k) or '') for k in LAY[i][0])):continue
            if i!=1:raise ValueError('New live non-building match requires source classification '+str(i))
            n=r['PermitNumber'];u=query(SL+'1/query',where="PermitNumber='"+n+"'",outFields=','.join(LAY[i][1]),returnGeometry='false',f='pjson');iss=ms(r.get('PermitIssuance'));rows.append(rec('UT','slc-'+n,'Salt Lake City building permit workflow',n,r['RecordType'],r['ApplicationStatus'],iss or ms(r['AppliedDate']),'issue date' if iss else 'application date',u,'City GIS permit '+n,r['WorkDescription'] or r['ProjectName'],'Salt Lake City','Salt Lake County',p,issuer='Salt Lake City Building Services',registered_issue_date=iss,scope='Demolition application; removal, not new supply.'))
    return rows,qc
