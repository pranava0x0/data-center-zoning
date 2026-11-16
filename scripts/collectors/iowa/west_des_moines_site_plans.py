"""City of West Des Moines City Council site plan approvals for data center projects, from the pinned review manifest."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
from lib.records import rec
import json
CITY='Council Bluffs Building Division issued permits';WDM='West Des Moines City Council site plans'
def rows():
    rows=[]
    p=collector_data('iowa','local.json')
    for r in json.loads(p.read_text()):
        n,dt,ds,kind,st,place,county,project,u,loc=r
        if ds!=WDM:continue
        rows.append(rec('IA','local-'+n+'-'+dt,ds,n,kind,st,dt,'permit issue date' if ds==CITY else 'council vote date',u,loc,project,place,county,p,source_capture='Reviewed agency document by public search index; hash is of extracted observation manifest, not original PDF.'))
    return rows
