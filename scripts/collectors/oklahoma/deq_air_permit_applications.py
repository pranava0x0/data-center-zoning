"""Oklahoma DEQ air permit applications: register rows whose proof is an active-review CSV entry or a DEQ application
page, giving a status date or application-receipt date rather than an issued instrument."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re, datetime as dt
from lib.text import htmltext
from collectors.oklahoma.common import ST
def dat(s):return dt.datetime.strptime(s,'%m/%d/%Y').date().isoformat()
def from_csv(m,active,i,fac,county,r,holds):
    """Register row with no archived proof: look the facility up in the active-review CSV. None means held."""
    ff=[a for a in active if a['Facility Name'].upper()==fac and a['County'].upper()==county]
    if len(ff)!=1:holds.append(dict(row=i,name=fac,reason=r.get('error')));return None
    a=ff[0];num=a['Permit Number'];day=a['Last Status Date'];role='last status date';status=a['Last Status'];kind='Air permit application';r=m['active_csv'];url=r['url'];ds='Oklahoma DEQ permit applications'
    return num,day,role,status,kind,r,url,ds
def from_html(r):
    h=ST.read(r).decode();q=h.index('header-left');t=htmltext(h[q:q+3000].encode());ns=re.search(r'\|\s*([A-Z0-9/-]+(?: M-\d+)?)\s*\((?:AQD|WQD)\)',t);date=re.search(r'Application Receipt Date:\s*(\d+/\d+/\d+)',t)
    if not ns or not date:raise ValueError(t[:200])
    num=ns[1];day=dat(date[1]);role='application receipt date';status=t.split('Status: ',1)[1].split('Application Receipt Date:',1)[0].strip();kind=t.split(') Tier ',1)[-1].split('Step:')[0].strip();ds='Oklahoma DEQ permit applications'
    return num,day,role,status,kind,ds
