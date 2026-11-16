"""Village of Mount Pleasant (Racine County) Plan Commission minutes: site plan votes for data center projects, from the pinned
index of minutes."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
from lib.records import rec
import json
M='Mount Pleasant Plan Commission minutes'
def rows():
 rows=[]
 p=collector_data('wisconsin','local.json')
 for id,n,project,dt,st,loc in json.loads(p.read_text()):
    rows.append(rec('WI','city-'+n,M,n,'Municipal site plan review',st,dt,'commission vote date','https://www.mtpleasantwi.gov/Archive.aspx?ADID='+id,loc,project,'Mount Pleasant','Racine County',p,issuer='Village of Mount Pleasant Plan Commission',source_capture='Municipal minutes checked via indexed PDF; hash of evidence manifest.'))
 return rows
