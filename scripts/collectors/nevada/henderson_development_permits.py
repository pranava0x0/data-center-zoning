"""City of Henderson: open development permits (OpenDevPermits ArcGIS service, 'other' and 'grading' layers)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.text
from collectors.nevada.common import candidates, pull_layer
KEYS=('henderson_other','henderson_grading')
def download(m,stats):
 for k in KEYS:pull_layer(m,stats,k)
def rows(add,excluded):
 for k in KEYS:
  for a,n,o,loc,u in candidates(k,excluded):
       iss=lib.text.isodate(a['ISSUEDATE']);submitted=lib.text.isodate(a['APPLICATIONDATE']);desc=a['DESCRIPTION'].strip()
       add(k,n,a['CASENUMBER'],a['PROJECTNAME'] or desc,a['CASETYPE']+' / '+a['CASEWORKCLASS'],a['STATUS'],iss or submitted,'Permit issue date' if iss else 'Application date','Henderson',loc,dict(description=desc,issue_date=iss,application_date=submitted,expiration_date=lib.text.isodate(a['EXPIREDATE']),issuer='City of Henderson',address=a['MAIN_ADDRESS_LINE1']),u)
