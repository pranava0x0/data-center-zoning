"""Miami-Dade County: building permits (MD_LandInformation ArcGIS layer). The dade_parcel layer is fetched only for the
raw-hit counts in the coverage file."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.text import slug
from collectors.florida.common import ST, fc, tab, dated, DC, stage_keys
KEYS=('dade','dade_parcel')
def download(c,m):stage_keys(c,m,KEYS)
def rows(m):
    out=[];held=[]
    for a,b,u in tab(m['dade'],'dade'):
        if not DC.search(a['FFRMLINE'] or ''):
            held.append(dict(group='Miami-Dade County',key=a['ID'],title=(a['FFRMLINE'] or '').strip(),reason='Telecom colocation or unspecified colocation; no positive data-center scope.'));continue
        n=str(a['ID']);statuscodes=next(x['domain']['codedValues'] for x in ST.read(m['dade']['meta'])['fields'] if x['name']=='BPSTATUS');status=next(x['name'] for x in statuscodes if x['code']==a['BPSTATUS'])
        out.append(fc('Miami-Dade County building permits','dade-'+n,n,a['FFRMLINE'].strip(),'Miami-Dade County',a['TYPE']+' — '+a['DESC1'].strip(),status,dated(a['ISSUDATE']),'permit issue date',b,'County ID '+n+'; PROCNUM '+a['PROCNUM'],u,county='Miami-Dade County',raw_status_code=a['BPSTATUS'],address=a['ADDRESS'].strip(),folio=a['FOLIO'],master_permit=str(a['MPRMTNUM']),process_number=a['PROCNUM']))
    return out,held
