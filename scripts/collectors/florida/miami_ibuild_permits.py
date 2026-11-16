"""City of Miami: iBuild permits (ArcGIS Maps/iBuildPermits). Direct matches are history rows; permits found only by the
Equinix parcel folio (miami_parcel layer) are returned as related, not confirmed history."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.text import slug
from collectors.florida.common import ST, fc, tab, dated, DC, stage_keys
KEYS=('miami','miami_parcel')
def download(c,m):stage_keys(c,m,KEYS)
def rows(m):
    out=[]
    for a,b,u in tab(m['miami'],'miami'):
        if not (DC.search(a['ProjectName'] or '') or (a['ProjectName']=='EQUINIX - MI1 IBX FACILITY' and a['FOLIO']=='0101030801050')):continue
        n=a['PermitNumber'] or a['ApplicationNumber'];reg=a['PermitNumber'] is not None
        out.append(fc('City of Miami iBuild permits','miami-'+slug(n),n,a['ProjectName'],'Miami',a['PermitType'] or a['ApplicationType'],a['PermitStatus'] or 'No permit status reported',dated(a['PermitIssuedDate']),'permit issue date' if reg else 'date unavailable',b,'PermitNumber / ApplicationNumber; '+n,u,permit_no=a['PermitNumber'],application_no=a['ApplicationNumber'],address=a['FULLADDR'],folio=a['FOLIO'],scope=a['ScopeOfWork']))
    return out
def related(m,direct):
    related=[]
    for a,b,u in tab(m['miami_parcel'],'miami_parcel'):
        n=a['PermitNumber'] or a['ApplicationNumber']
        if n in direct:continue
        related.append(dict(record_no=n,objectid=a['OBJECTID'],permit_no=a['PermitNumber'],application_no=a['ApplicationNumber'],folio=a['FOLIO'],scope=a['ScopeOfWork'],status=a['PermitStatus'],date=dated(a['PermitIssuedDate']),url=u,source_sha256=b['sha256'],basis='Parcel match only; excluded from confirmed history.'))
    return related
