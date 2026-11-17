"""City of Hartford building and trade permits (Hartford Open Data, Building Permits 2020-01-01 to current),
screened for data centers. Issuer: City of Hartford."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import json
from datetime import datetime,timezone
from urllib.parse import urlencode
U='https://utility.arcgis.com/usrsvcs/servers/d595ae995fb049d3ac54919ebf24b1ac/rest/services/HartfordOpenDataTables/FeatureServer/0';fields='OBJECTID,RECORD_ID,DESCRIPTION,DATE_OPENED,DATE_CLOSED,RECORD_TYPE_TYPE,B1_APP_TYPE_ALIAS,RECORD_STATUS,PROPERTY_ADDRESS,DateIssued'
def download(A):
 A.fetch('hartford.json.gz',U+'/query?'+urlencode(dict(where=lib.terms.patterns(['DESCRIPTION'],'UPPER'),outFields=fields,returnGeometry='false',f='json')))
def rows(A,add):
 """Adds events through add(); returns the held record ids."""
 held=[]
 h=json.loads(A.read('hartford.json.gz'));assert not h.get('exceededTransferLimit')
 for f in h['features']:
  a=f['attributes'];s=a['DESCRIPTION'];m=lib.terms.MATCH.search(s)
  if not m:held.append(a['RECORD_ID']);continue
  d=lambda v:datetime.fromtimestamp(v/1000,timezone.utc).date().isoformat() if v else None
  n='hartford.json.gz';dt=d(a['DateIssued']);i=m.start();text=s[max(0,i-75):i+130].strip();add('Hartford building and trade permits',a['RECORD_ID'],text,'Hartford',a['B1_APP_TYPE_ALIAS'] or a['RECORD_TYPE_TYPE'],a['RECORD_STATUS'],dt or d(a['DATE_OPENED']),'Permit issue date' if dt else 'Date opened',U+'/query?'+urlencode(dict(where=f"RECORD_ID='{a['RECORD_ID']}'",outFields='*',f='html')),'Hartford Building Permits 20200101 to Current / '+a['RECORD_ID'],issuer='City of Hartford',archive='cache/history/ct/'+n,archive_sha256=A.files[n]['sha256'],issue_date=dt,closed_date=d(a['DATE_CLOSED']),address=a['PROPERTY_ADDRESS'],portal_row_id_at_capture=a['OBJECTID'])
 return held
