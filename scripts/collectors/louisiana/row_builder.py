"""Louisiana record builder shared by the DEQ, USACE, Bossier Parish and Shreveport modules, plus the explicit data-center text screen."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from lib.epa_icis import digest
EXPLICIT=re.compile(r'\bdata[\s-]*cent(?:er|re)s?\b',re.I)
def row(ds,ident,city,co,num,project,kind,status,day,role,url,loc,cache,**extra):
    if not co.endswith(' Parish'):raise ValueError(co)
    return dict(id='la-'+ident,state='LA',dataset=ds,jurisdiction=city or co,record_no=num,project=project,kind=kind,status=status,date=day,date_role=role,url=url,source_url=url,source_sha256=digest(cache),locator=loc,details={'county':co,'issuer':'Louisiana Department of Environmental Quality','source_locality':city,**extra})
