"""Texas Department of Licensing and Regulation (TDLR): Architectural Barriers (TABS) project registrations, fetched by project number."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.files import dump, sha
from lib.net import req
from lib.terms import MATCH, patterns
from lib.text import isodate, Fields
import lib.arcgis as arcgis
import gzip, json, re
from urllib.parse import urlencode, quote
from collections import Counter
from collectors.texas.common import ROOT, C, CONFIG, saver
def download(m):
    save=saver(m)
    x=CONFIG['tabs']
    for no in x['ids']:
        url=x['url']+no;save(no+'.html.gz',req(url),url)
def tabs_parse(b,no):
    h=Fields();h.feed(b.decode('utf-8-sig'));v=h.parts
    def val(k):return v[v.index(k)+1]
    assert val('Project Number:')==no
    # Project header has registration date; do not use future estimated completion.
    d=re.search(r'Registration Date:\s*(\d{1,2}/\d{1,2}/\d{4})',' '.join(v)).group(1)
    addr=v[v.index('Location Address:')+1:v.index('Location County:')]
    city=re.search(r'([^,]+),\s*(?:TX|Texas)\s+\d{5}',addr[-1],re.I).group(1).strip()
    detail={'scope':val('Scope of Work:'),'facility':val('Facility Name:'),'type_of_work':val('Type of Work:'),'county':val('Location County:')+' County','postal_city':city,'issuer':'Texas Department of Licensing and Regulation'}
    if not MATCH.search(' '.join([detail['scope'],detail['facility'],val('Project Name:')])):raise ValueError('No scope evidence '+no)
    return city,val('Project Name:'),val('Current Status:'),isodate(d),detail
def rows(m,add,exclusions):
    for no in CONFIG['tabs']['ids']:
        n=no+'.html.gz';city,name,status,dt,extra=tabs_parse(gzip.decompress((C/n).read_bytes()),no)
        add('tabs',n,no,name,'State accessibility project registration',status,dt,'Registration date',CONFIG['tabs']['url']+no,'Architectural Barriers Project Details, Registration Date and PROJECT',extra,city)
