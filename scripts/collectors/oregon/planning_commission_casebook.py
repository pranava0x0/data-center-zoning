"""Oregon county planning commission cases (Morrow, Umatilla, Crook and other counties): pinned extract of manually checked
government documents in data/history/oregon/casebook.json."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, D
import json, re
import lib.files
def rows():
 events={}
 casebook=collector_data('oregon','casebook.json')
 for a in json.loads(casebook.read_text()):
  key='or-local-'+re.sub('[^a-z0-9]+','-',a['record_no'].lower()).strip('-')
  events[key]=dict(id=key,state='OR',dataset='Oregon planning commission cases',**a,details={'issuer':a['jurisdiction']+' Planning Commission','county': 'Morrow County' if a['jurisdiction']=='Morrow County' else 'Umatilla County','evidence_mode':'Manually checked government document via public web index; pinned extract, no locally archived original','archive':'data/history/oregon/casebook.json','extract_sha256':lib.files.sha(casebook.read_bytes())})
 return events
