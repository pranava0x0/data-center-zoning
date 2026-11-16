"""Florida helpers shared by the source modules: the FL evidence store, record builder, ArcGIS batch reader and the
generic ArcGIS download loop (config keys select which sources a module fetches)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from lib.archive import Store
from lib.arcgis import arcstore
from urllib.parse import urlencode
from pathlib import Path
import datetime as dt, re
from zoneinfo import ZoneInfo
import lib.discovery as collect
import lib.net as netfetch
R=Path(__file__).resolve().parents[3]
ST=Store('FL'); M=collector_data('florida','manifest.json')
def stage_keys(c,m,keys):
    for k,s in c.items():
        if k not in keys:continue
        if k in m and not netfetch.REFETCH:continue
        fields=s['fields'];terms=s.get('terms',['%DATA%CENTER%','%DATACENTRE%','%COLOCATION%','%EQUINIX%','%TERREMARK%','%NAP OF THE AMERICAS%','%FLEXENTIAL%','%QTS DATA%','%COPT DATA%','%CORE%SITE%'])
        where=s.get('where') or ' OR '.join("UPPER("+f+") LIKE '"+v+"'" for f in fields for v in terms);m[k]=arcstore(ST,s['url'],where,s['out']);collect.dump(M,m)
DC=re.compile(r'\bdata\s*(?:cent(?:er|re)|backup cent(?:er|re))\b',re.I)
def dated(ms):
    if not ms:return None
    t=dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc)
    return (t if t.time()==dt.time() else t.astimezone(ZoneInfo('America/New_York'))).date().isoformat()
def fc(ds,prefix,num,name,jur,kind,s,day,role,ref,locator,localurl=None,**det):
    return dict(id='fl-'+prefix,state='FL',dataset=ds,jurisdiction=jur,record_no=str(num),project=name,kind=kind,status=s,date=day,date_role=role,url=localurl or ref['url'],source_url=ref['url'],locator=locator,details=dict(source_sha256=ref['sha256'],**det))
def tab(s,k,store=ST):
    for b in s['batches']:
        for x in store.read(b)['features']:
            a=x['attributes'];key=s['oid'];u=s['url']+'/query?'+urlencode(dict(f='pjson',where=key+'='+str(a[key]),outFields='*',returnGeometry='false'));yield a,b,u
