"""Pinned casebook extract (data/history/north_carolina/casebook.json) of primary-source records: City of Charlotte rezoning
petitions and NC DEQ air application reviews (Caldwell County). Offline only; nothing to download."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import json
import lib.files
from collectors.north_carolina.evidence_store import D, add
casebook=collector_data('north_carolina','casebook.json')
def rows(events):
 for i,a in enumerate(json.loads(casebook.read_text())):
  n,proj,kind,stat,date,role,url,loc,evidence=a;j='Charlotte' if url.startswith('https://www.charlottenc.gov') else 'Caldwell County';ds='Charlotte rezoning petitions' if j=='Charlotte' else 'NC DEQ air application reviews';d={'issuer':'City of Charlotte' if j=='Charlotte' else 'North Carolina DEQ Division of Air Quality','county':'Mecklenburg County' if j=='Charlotte' else j,'evidence':evidence,'archive':'data/history/north_carolina/casebook.json','extract_sha256':lib.files.sha(casebook.read_bytes()),'archive_type':'Pinned extract from primary government source'}
  add(events,'nc-curated-'+str(i),ds,n,proj,j,kind,stat,date,role,url,url,loc,d)
