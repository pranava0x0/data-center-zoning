"""Check City of Portland's All Permits descriptions; archive IDs and bounded batches."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.oregon.portland_west_metro import *
from urllib.parse import urlencode
import time
BASE='https://www.portlandmaps.com/arcgis/rest/services/Public/BDS_Permit/MapServer/22'
TERMS=['DATA CENTER','DATA CENTRE','DATACENTER','SERVER FARM']
WHERE=' OR '.join("UPPER("+f+") LIKE '%"+a+"%'" for a in TERMS for f in ['DESCRIPTION','WORK_DESCRIPTION'])
P=R/'data/westmetro_portland_manifest.json'
def fetch_portland():
 x={'layer':S.get(BASE+'?f=json'),'where':WHERE,'ids':S.get(BASE+'/query',where=WHERE,returnIdsOnly='true')}
 ids=sorted(S.read(x['ids']).get('objectIds') or []);print('matched IDs',len(ids),flush=True);x['batches']=[]
 for i in range(0,len(ids),75):
  b=S.get(BASE+'/query',objectIds=','.join(map(str,ids[i:i+75])),outFields='OBJECTID,FOLDERKEY,APPLICATION,STATUS,CITY,COUNTY,PERMIT,TYPE,DESCRIPTION,WORK_DESCRIPTION,ISSUED,FINALED,INTAKECOMPLETEDATE,PORTLAND_MAPS_URL,FOLDERTYPE',returnGeometry='false');x['batches'].append(b)
 collect.dump(P,x)
if __name__=='__main__':fetch_portland()

def replay():
 from datetime import datetime,timezone,date
 from zoneinfo import ZoneInfo
 m=existing(P);ids=set(S.read(m['ids'])['objectIds']);raw=[v['attributes'] for b in m['batches'] for v in S.read(b)['features']]
 assert ids=={v['OBJECTID'] for v in raw} and len(raw)==len(ids)
 assert len({v['FOLDERKEY'] for v in raw})==len(raw)
 out=[];needle=re.compile(r'data\s*cent(?:er|re)|server farm',re.I)
 def day(x):return datetime.fromtimestamp(x/1000,timezone.utc).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat() if x else None
 for v in raw:
  d=v.get('DESCRIPTION') or '';w=v.get('WORK_DESCRIPTION') or ''
  assert needle.search(d+' '+w)
  # Match admits enterprise rooms and renovations. Neutral case caption avoids suggesting a stand-alone facility.
  dates={k:day(v[k]) for k in ['ISSUED','FINALED','INTAKECOMPLETEDATE']}
  dt=dates['ISSUED'] or dates['INTAKECOMPLETEDATE']
  if dt and dt>'2026-11-16':continue
  if any(t and t>'2026-11-16' for t in dates.values()):continue  # do not assign a future status retrospectively
  key=str(v['FOLDERKEY']);kind=v['PERMIT'];num=v['APPLICATION'];status=v['STATUS']
  assert num and kind and status
  det=dict(folderkey=key,object_id=v['OBJECTID'],case_type=v['TYPE'],work_type=w,source_dates=dates,scope='A record explicitly mentioning a data center or server farm; includes accessory rooms, equipment and tenant work, not proof of a standalone campus.',matched_term=needle.search(d+' '+w).group(0))
  if v.get('COUNTY'):det['county']=v['COUNTY']+' County'
  url=v['PORTLAND_MAPS_URL'] or BASE+'/'+str(v['OBJECTID'])
  out.append(dict(id='westmetro-portland-'+key,state='OR',jurisdiction='Portland',dataset='PortlandMaps all permits',record_no=num,project='Data center work — '+(w or v['TYPE'] or kind)+' ('+num+')',kind=kind,status=status,date=dt,date_role='Issued' if dates['ISSUED'] else 'Intake completed' if dt else 'Date not available',url=url,source_url=BASE+'/'+str(v['OBJECTID']),locator='All Permits layer 22; folder '+key,details=det))
 return out
