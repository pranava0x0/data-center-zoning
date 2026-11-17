"""Clark County Building Department: inspection-sites ArcGIS layer (permits with issue dates and scope of work)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.text
from datetime import datetime
from urllib.parse import urlencode
from collectors.nevada.common import candidates, pull_layer, GIS
def download(m,stats):pull_layer(m,stats,'clark_inspection')
def rows(add,excluded):
 k='clark_inspection'
 for a,n,o,_loc,_u in candidates(k,excluded):  # the shared helper's OBJECTID locator/link are replaced below by permit-number ones
      no=a['Permit_Number'];loc='permit '+no;u=GIS[k][0]+'/query?'+urlencode(dict(where=f"Permit_Number='{no}'",outFields=GIS[k][2],returnGeometry='false',f='pjson'))
      dt=lib.text.isodate(a['Permit_Issued_Date']);assert dt,(o,'Missing issue date')
      add(k,n,a['Permit_Number'],a['Scope_of_Work'].strip(),a['Type']+' building permit','Issued',dt,'Permit issue date','Clark County',loc,dict(county='Clark County',issuer='Clark County Building Department',inspection_type=a['Last_Inspection'],last_inspection_date=datetime.strptime(a['Last_Inspection_Date'],'%Y%m%d').date().isoformat() if a['Last_Inspection_Date'] else None,grading_description=a['Description_of_Grading'],address=a['Address'],portal_row_id_at_capture=o),u)
