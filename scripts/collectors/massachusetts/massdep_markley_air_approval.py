"""MassDEP Markley Group (Lowell) air approval NE-25-002 and adjudication rulings, from the pinned index of primary MassDEP rulings."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
from lib.records import rec
import json
def rows():
 rows=[]
 p=collector_data('massachusetts','cases.json')
 for id,n,kind,st,dt,role,u,loc in json.loads(p.read_text()):
    rows.append(rec('MA',id,'MassDEP Markley air approval and adjudication',n,kind,st,dt,role,u,loc,'Markley Group data center, Lowell','Lowell','Middlesex County',p,air_permit='NE-25-002',source_capture='Indexed primary MassDEP ruling; SHA-256 covers the extracted manifest.'))
 return rows
