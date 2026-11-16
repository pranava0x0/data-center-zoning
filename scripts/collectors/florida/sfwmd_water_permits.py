"""South Florida Water Management District (SFWMD): environmental resource permit register (water_permits layer) and
permit application actions (water_files layer), statewide-district ArcGIS Regulation_ApplicationPermits service."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.text import slug
from collectors.florida.common import ST, fc, tab, dated, DC, stage_keys
KEYS=('water_files','water_permits')
def download(c,m):stage_keys(c,m,KEYS)
def rows(m):
    out=[];held=[];wreg={}
    for k in ('water_permits','water_files'):
        for a,b,u in tab(m[k],k):
            if not DC.search(a['PROJECT_NAME']):
                held.append(dict(group=k,project=a['PROJECT_NAME'],key=a['APP_NO'],reason='Name-only candidate; no explicit facility use.'));continue
            if a.get('IsTestData'):continue
            key=(a['APP_NO'],a['PERMIT_NO'])
            if key in wreg:
                prev=wreg[key]
                if a['AppStatus']!=prev['details']['application_status']:raise ValueError('Contradictory app status')
                continue
            ispermit=k=='water_permits'; n=a['PERMIT_NO'] if ispermit else a['APP_NO']; day=dated(a['IssueDate']) if ispermit else None;role='permit issue date' if day else 'application final action date';day=day or dated(a['AppFinalActionDate'])
            if not day:day=dated(a['AppReceivedDate']);role='application received' if day else 'date unavailable'
            rec=fc('South Florida Water Management District '+('permit register' if ispermit else 'application actions'),'sfwmd-'+slug(a['APP_NO'])+'-'+slug(a['PERMIT_NO'] or 'no-permit'),n,a['PROJECT_NAME'],'South Florida Water Management District',(a['PermitFamily'] or '')+' — '+(a['PermitSubFamilyDesc'] or a['AppTypeDesc'] or 'application'),a['PermitStatus'] if ispermit else a['AppStatus'],day,role,b,'Application '+a['APP_NO']+'; '+('permit '+a['PERMIT_NO'] if a['PERMIT_NO'] else 'no permit number'),u,permit_no=a['PERMIT_NO'],application_no=a['APP_NO'],application_status=a['AppStatus'],permit_status=a['PermitStatus'],application_type=a['AppTypeDesc'],land_use=a['LandUse'],received_date=dated(a['AppReceivedDate']),action_date=dated(a['AppFinalActionDate']),issue_date=dated(a['IssueDate']),expires=dated(a['PermitExpirationDate']));wreg[key]=rec
    out+=list(wreg.values())
    return out,held
