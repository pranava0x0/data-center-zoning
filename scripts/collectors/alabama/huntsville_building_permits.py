"""City of Huntsville (Alabama) building permits and certificates of occupancy for the 100 Profile Pl NW campus
(Madison County), from the city's Licenses/BuildingPermits ArcGIS MapServer, plus the city's context page."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json, re, math
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
U='https://maps.huntsvilleal.gov/server/rest/services/Licenses/BuildingPermits/MapServer'
S={'hsv-identity.html.gz':'https://www.huntsvilleal.gov/data-center-expansion-to-benefit-north-huntsville-local-schools/'}
def query(l):return U+'/'+str(l)+'/query?'+urlencode(dict(where="UPPER(Address) LIKE '100 PROFILE PL NW%'",outFields='*',returnGeometry='true',outSR=4326,f='json'))
def stable(l,field,value):return U+'/'+str(l)+'/query?'+urlencode(dict(where=f'{field}={value}',outFields='*',f='html'))  # issuer identifier, never the portal OBJECTID
def download(A):
 for n,u in S.items():A.fetch(n,u)
 for l in [0,1]:A.fetch(f'hsv-{l}.json.gz',query(l))
def rows(A):
 out={};plots=[f['geometry']['coordinates'] for f in json.loads(A.read('points.geojson.gz'))['features'] if f['properties']['state_abb']=='AL' and f['properties']['name']=='Meta Huntsville Data center'];assert len(plots)>=1
 def add(n,k,ds,no,title,j,kind,stat,date,role,loc,url=None,**d):
  src=A.files[n]['url'];key='al-'+k
  out[key]=dict(id=key,state='AL',dataset=ds,record_no=str(no),project=title,jurisdiction=j,kind=kind,status=stat,date=date,date_role=role,url=url or src,source_url=src,locator=loc,details={**d,'archive':'cache/history/al/'+n,'archive_sha256':A.files[n]['sha256']})
 def epoch(v):return datetime.fromtimestamp(v/1000,ZoneInfo('America/Chicago')).date().isoformat() if v else None
 co=set()
 for l in (1,0):
  n=f'hsv-{l}.json.gz';data=json.loads(A.read(n));assert not data.get('exceededTransferLimit');assert len({f['attributes']['OBJECTID'] for f in data['features']})==len(data['features'])
  for f in data['features']:
   a=f['attributes'];geo=f['geometry'];address=a['Address'];assert re.fullmatch(r'100 PROFILE PL NW(?: UNIT \d+)?',address);distance=min(math.hypot((x-geo['x'])*91200,(y-geo['y'])*111200) for x,y in plots);assert distance<550,(address,distance)
   no=str(a['PermitID']);oid=a['OBJECTID'];url=stable(l,'PermitID',no);proj='Huntsville campus — '+address;d=dict(issuer='City of Huntsville',address=address,source_occupancy_class=a['OccupancySubtype'],site_match='Exact street base plus independently located named PNNL Meta building within 550 m; campus-associated, specific equipment or tenant not stated by permit issuer.',nearest_marker_m=round(distance),issue_date=epoch(a['Permit_Issue_DateTime']),co_date=epoch(a.get('Occupancy_Issue_DateTime')),marker_source='https://github.com/IMMM-SFA/datacenter-atlas',municipal_context=S['hsv-identity.html.gz'])
   if l==1:
    co.add(no);oc=str(a['OccupancyNumber']);d['building_permit_id']=no;d['portal_row_id_at_capture']=oid;add(n,'occupancy-'+oc,'Huntsville occupancy certificates',oc,proj,'Huntsville','Certificate of occupancy','Occupancy certificate issued',d['co_date'],'Certificate issue date','OccupancyCerts OccupancyNumber '+oc,stable(l,'OccupancyNumber',oc),**d)
   d['portal_row_id_at_capture']=oid;older=out.get('al-building-'+no);d['certificate_observed']=no in co
   if older:
    assert older['date']==d['issue_date']
    d['co_date']=older['details']['co_date']
   add(n,'building-'+no,'Huntsville building permits',no,proj,'Huntsville','Building permit — '+str(a['TypeOfWork']),'Permit issued',d['issue_date'],'Municipal building permit issue date','City layer '+str(l)+'; PermitID '+no,url,**d)
 return out
