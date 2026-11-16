"""Metropolitan Government of Nashville and Davidson County, Codes Department: permit history by parcel (Metro parcel permit
service) and the Metro building-permit ArcGIS layers screened for sector terms. Also archives the Grassmere federal court
filing (govinfo), which is fetched but not used for a record. Issuer: Metro Nashville Codes."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt, re
from collectors.tennessee.evidence_store import RX, collect, M, get, read, fetch_layers, fetch_documents
LAYERS=('nash_issued','nash_app','nash_trade');DOCS=('grassmere',)
def download(c,m):
    fetch_layers(c,m,LAYERS);fetch_documents(c,m,DOCS);parcel_fetch(c,m)
def parcel_fetch(c,m):
    lst=m.setdefault('parcel_queries',{});source=c['parcel_layer']+'/query';new={}
    for f in read(m['atlas'])['features']:
        a=f['properties']
        if a['state_abb']=='TN' and a['county']=='Davidson County':
            x,y=f['geometry']['coordinates'];new['point '+str(x)+' '+str(y)]={'geometry':f'{x},{y}','geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects'}
    new.update({'address '+s:{'where':"UPPER(PropAddr) LIKE '"+s+"'"} for s in c['parcel_streets']})
    new.update({'APN '+s:{'where':"APN='"+s+"'"} for s in c['direct_apns']})
    for n,q in new.items():
        if n not in lst:lst[n]=get(source,outFields='OBJECTID,APN,PropAddr,PropCity,LUDesc',returnGeometry='false',**q);collect.dump(M,m)
    pars=m.setdefault('parcels',{})
    for r in lst.values():
        resp=read(r)
        if resp.get('exceededTransferLimit'):raise ValueError('Truncated parcel query')
        for v in resp['features']:
            num=v['attributes']['APN']
            if num not in pars:pars[num]=get(c['parcel_service']+num);collect.dump(M,m);print('Metro parcel',num,len(read(pars[num])),flush=True)
def rows(m,add):
    # Census cities remain distinct from postal localities. Local evidence is Metro issued.
    addrs={}
    for r in m['parcel_queries'].values():
        for v in read(r)['features']:
            a=v['attributes'];addrs[a['APN']]=a['PropAddr']
    permits={}
    for apn,r in m['parcels'].items():
        for v in read(r):
            num=str(v['permitNumber']);purpose=' '.join((v.get('purpose') or '').split())
            if not RX.search(purpose):continue
            if num in permits:
                if permits[num]!=v['pid']:raise ValueError('Two record identities share number '+num)
                continue
            permits[num]=v['pid'];matched=RX.search(purpose);excerpt=purpose[max(0,matched.start()-65):matched.end()+80];excerpt=re.split(r'\b(?:POC|CONTACT)\b|\*{2,}',excerpt,flags=re.I)[0].strip() or matched.group();issue=v['dateIssued'];day=dt.datetime.strptime(issue.split()[0],'%m/%d/%Y').date().isoformat() if issue else None
            add('metro-'+v['pid'],'Metro Nashville Codes Permit History','Nashville',num,' / '.join([addrs[apn],v.get('permitSubType') or v['permitType']]),v['permitType'],v['status'],day,'issue date' if day else 'issue date not reported','https://epermits.nashville.gov/#/search?searchCode=PRMT&page=1&searchText='+num+'&searchType=permit','Parcel '+apn+' / record PID '+v['pid'],r,dict(county='Davidson County',agency='Metropolitan Government of Nashville and Davidson County, Codes Department',parcel=apn,address=addrs[apn],scope_excerpt=excerpt,permit_subtype=v.get('permitSubType'),record_pid=v['pid']))
