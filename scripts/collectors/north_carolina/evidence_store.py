"""North Carolina shared evidence archive (cache/history/nc) and record helpers used by every source module."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import lib.arcgis as arcgis
import json, re
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from lib.archive import NamedArchive as Archive
from lib.paths import R, D
A=Archive('NC')
seen=set()
def epoch(v):
 if not v:return None
 t=datetime.fromtimestamp(v/1000,timezone.utc)
 # Preserve advertised GIS date-only midnights; locally timed timestamps use Eastern.
 return (t if (t.hour,t.minute,t.second)==(0,0,0) else t.astimezone(ZoneInfo('America/New_York'))).date().isoformat()
def iso(v):return v.date().isoformat() if v else None
def add(events,k,ds,num,title,j,kind,status,date,role,url,src,loc,d):
 assert k not in seen;seen.add(k);events.append(dict(id=k,state='NC',dataset=ds,record_no=num,project=title,jurisdiction=j,kind=kind,status=status,date=date,date_role=role,url=url,source_url=src,locator=loc,details=d))
def gis_download(k,url,cols,fields):
 offset=[0]
 def g(q,**p):
  if 'returnIdsOnly' in p:n=k+'-ids.json.gz'
  else:n=f'{k}-{offset[0]}.json.gz';offset[0]+=100
  return json.loads(A.fetch(n,q+'?'+urlencode(p)))
 r=arcgis.pull(g,lambda a:a,url,lib.terms.patterns(cols.split(','),'UPPER'),fields,batch=100,id_params={'f':'json'},page_params={'f':'json'})
 print(k,len(r['ids']['objectIds'] or []),flush=True)
def gis_rows(events,held,k,gis,cols2,parse):
 url,cols,fields=gis
 ids=json.loads(A.read(k+'-ids.json.gz'))['objectIds'];count=0;unique={}
 for n in sorted(n for n in A.files if re.fullmatch(k+r'-\d+\.json\.gz',n)):
  rows=json.loads(A.read(n))['features'];count+=len(rows)
  for row in rows:
   a=row['attributes'];oid=a['OBJECTID'];matched=[str(a.get(c) or '') for c in cols2 if lib.terms.MATCH.search(str(a.get(c) or ''))]
   if not matched:held.append([k,oid,'No explicit sector term in project/description/use fields.']);continue
   num,status,issued,scope,kind,d,ds=parse(a)
   key=(k,num);finger=(status,issued,kind)
   if key in unique:
    assert unique[key]==finger;continue
   unique[key]=finger;d.update(source_objectid=oid,archive='cache/history/nc/'+n,archive_sha256=A.files[n]['sha256'])
   dt=issued or d.get('applied_date');role='Permit issue date' if issued else ('Application date' if dt else 'No date reported');title=' — '.join(dict.fromkeys(matched))[:500]
   add(events,'nc-'+k+'-'+num,ds,num,title,scope,kind,status,dt,role,url+'/'+str(oid),url,'OBJECTID '+str(oid)+'; permit '+num,d)
 assert count==len(ids)
