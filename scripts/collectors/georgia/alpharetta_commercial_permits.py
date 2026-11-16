"""City of Alpharetta (Fulton County) commercial, land disturbance and tree permits, from the city's OpenData_PCE_Full
ArcGIS FeatureServer."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import datetime as dt
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
import lib.arcgis as arcgis
import lib.net as netfetch
import lib.discovery as collect
from collectors.georgia.evidence_store import R, get, read, j, DC, row, slug
ALPH=collector_data('georgia','alpharetta.json')
GISCITY='https://alphagis.alpharetta.ga.us/arcgis/rest/services/OpenData/OpenData_PCE_Full/FeatureServer'
def cityfetch():
    m=j(ALPH) if ALPH.exists() else {};db={1:'Commercial Permits',2:'Land Disturbance Permits',4:'Tree Permits'}
    for i,n in db.items():
        if n in m and not netfetch.REFETCH:continue
        u=GISCITY+'/'+str(i);meta=get(u+'?f=json');m0=read(meta);oid=m0['objectIdField'];fields={v['name'] for v in m0['fields']};lex=['CASE_NAME','LOCATION_NOTES'];terms=['%DATA%CENT%','%DATA%HALL%','%COLOCATION%','%QTS%','%FLEXENTIAL%','%CORE%SITE%','%EQUINIX%','%DIGITAL REALTY%']
        where=' OR '.join("UPPER("+f+") LIKE '"+s+"'" for s in terms for f in lex if f in fields)+" OR UPPER(Location) LIKE '2525%WESTSIDE%'"
        out=[v for v in 'CASE_NUMBER CASE_TYPE_DESC CASE_NAME DATE_ENTERED Location STATUS_CODE TASK_CODE TASK_DESC ACTUAL_START_DATE ACTUAL_END_DATE TASK_COMPLETE_FLAG RESULT_CODE RESULT_DISPLAY LOCATION_NOTES'.split() if v in fields]
        pulled=arcgis.pull(get,read,u,where,','.join([oid]+out),oid,batch=100)
        m[n]=dict(meta=meta,total=get(u+'/query',where='1=1',returnCountOnly='true'),predicate=where,ids=pulled['ids'],batches=pulled['batches'],oid=oid);collect.dump(ALPH,m)
def rows():
    out=[]
    for layer,bucket in j(ALPH).items():
        for b in bucket['batches']:
            for v in read(b)['features']:
                a=v['attributes'];name=a.get('CASE_NAME') or ''
                if not DC.search(name):continue
                if a['TASK_CODE']!='B-ISSUEPER' or a['RESULT_DISPLAY']!='ISSUED' or a['TASK_COMPLETE_FLAG']!='Y':raise ValueError('Review new city status')
                n=a['CASE_NUMBER'];day=dt.datetime.fromtimestamp(a['ACTUAL_END_DATE']/1000,ZoneInfo('America/New_York')).date().isoformat()
                x=row('City of Alpharetta commercial permits','alpharetta-'+slug(n),'Alpharetta',n,name,a['CASE_TYPE_DESC'],a['RESULT_DISPLAY'],day,'issue task completed',b,'CASE_NUMBER '+n+'; task B-ISSUEPER',address=a['Location'],case_status=a['STATUS_CODE'],task=a['TASK_CODE'])
                x['source_url']=b['url'];x['url']=GISCITY+'/1/query?'+urlencode({'where':bucket['oid']+'='+str(a[bucket['oid']]),'outFields':'*','returnGeometry':'false','f':'pjson'});out.append(x)
    return out
