"""City of Columbus Building and Zoning Services site-engineering permit GIS layer (BuildingZoning/MapServer, Site Engineering Permits)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.ohio.common import fetch_layer, cal, keyurl
def download(c,m,k,l):fetch_layer(c,m,k,l)
def row(add,audit,state,k,l,meta,a,h0,hh,oid,url):
    n=a['B1_ALT_ID'];state['eng'].append(a)
    add('col-eng-'+n,'Columbus engineering filings','Columbus',n,a['B1_SHORT_NOTES'] or a['B1_WORK_DESC'][:100],a['B1_PER_TYPE'],a['B1_APPL_STATUS'],cal(a['B1_FILE_DD']),'filing date',keyurl(l['url'],'B1_ALT_ID',n),'Site Engineering Permits; '+n,l['url'],h0,{'portal_row_id_at_capture':oid,'authority':'City of Columbus Building and Zoning Services','description':a['B1_WORK_DESC'],'parcel':a['B1_PARCEL_NBR'],'applicant_portal_url':a['ACA_URL'],'last_status_date':cal(a['LAST_STATUS_DT']),'matched_fields':list(hh)})
