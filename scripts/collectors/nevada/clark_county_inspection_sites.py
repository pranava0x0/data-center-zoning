"""Clark County Building Department: inspection-sites ArcGIS layer (permits with issue dates and scope of work)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.text
from datetime import datetime
from collectors.nevada.common import candidates, pull_layer
def download(m,stats):pull_layer(m,stats,'clark_inspection')
def rows(add,excluded):
 k='clark_inspection'
 for a,n,o,loc,u in candidates(k,excluded):
      dt=lib.text.isodate(a['Permit_Issued_Date']);assert dt,(o,'Missing issue date')
      add(k,n,a['Permit_Number'],a['Scope_of_Work'].strip(),a['Type']+' building permit','Issued',dt,'Permit issue date','Clark County',loc,dict(county='Clark County',issuer='Clark County Building Department',inspection_type=a['Last_Inspection'],last_inspection_date=datetime.strptime(a['Last_Inspection_Date'],'%Y%m%d').date().isoformat() if a['Last_Inspection_Date'] else None,grading_description=a['Description_of_Grading'],address=a['Address']),u)
