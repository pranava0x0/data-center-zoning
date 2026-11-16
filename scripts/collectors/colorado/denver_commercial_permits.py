"""City and County of Denver: commercial construction permits (Open Data Catalog feature service) at the verified
4300 N Brighton Blvd data-center site, plus the narrative search of the same layer that must return nothing."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.records import rec, CUT
from lib.files import unpack
from lib.arcgis import snapshot as arc
from lib.text import ms
from lib.terms import pred
from lib.net import get_simple as get, query
from lib.paths import CACHE
from collectors.colorado import cdphe_apcd_air_permits as air
D=CACHE/'co';AP=air.AP
DV='https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_DEV_COMMERCIALCONSTPERMIT_P/FeatureServer/317'
def download():
    D.mkdir(exist_ok=True,parents=True)
    arc(DV,pred(['LOCATION','BID_AUTHNAME']),['OBJECTID','PERMIT_NUM','LOCATION','ADDRESS','BID_AUTHNAME','DATE_ISSUED','FINAL_DATE','CANCEL','DATE_RECEIVED','CLASS'],D/'denver.json.gz')
    arc(DV,"UPPER(ADDRESS) LIKE '4300%BRIGHTON%'",['OBJECTID','PERMIT_NUM','ADDRESS','DATE_ISSUED','FINAL_DATE','CANCEL','LOCATION','CLASS','CO_REQUIRED','DATE_CO_ISSUED'],D/'denver-site.json.gz')
def rows(sites):
    rows=[]
    p=D/'denver-site.json.gz';dv=unpack(p)
    if unpack(D/'denver.json.gz')['rows']:raise ValueError('New narrative matches require review')
    for r in dv['rows']:
        if r['ADDRESS'].upper()!='4300 N BRIGHTON BLVD' or not r.get('DATE_ISSUED'):continue
        n=r['PERMIT_NUM'];u=query(DV+'/query',where="PERMIT_NUM='"+n+"'",outFields='PERMIT_NUM,ADDRESS,DATE_ISSUED,FINAL_DATE,CANCEL,CLASS,LOCATION',returnGeometry='false',f='pjson')
        iss,fin,cancel=map(ms,[r['DATE_ISSUED'],r['FINAL_DATE'],r['CANCEL']]);status='CANCEL date recorded' if cancel and cancel<=CUT else 'FINAL_DATE recorded' if fin and fin<=CUT else 'DATE_ISSUED recorded'
        rows.append(rec('CO','den-'+n,'Denver commercial permits at a verified data-center site',n,'Commercial construction permit / '+str(r['CLASS']),status,iss,'issue date',u,n+'; exact Denver site address / state air facility cross-check','Iron Mountain / FORTRUST site — '+str(r['CLASS'])+'; individual work scope not specified.','Denver','Denver County',p,issuer='City and County of Denver',address=r['ADDRESS'],facility_record=AP+'?permit='+sorted(sites)[0],identity_basis='City permit at the existing state-verified data-center address. No permit description claiming data-hall work.',final_date=fin,cancel_date=cancel,issue_date=iss))
    return rows,dv['count'],unpack(D/'denver.json.gz')['count']
