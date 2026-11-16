"""City of Franklin, Tennessee: Municipal Planning Commission site plan actions (Franklin Legistar matters and histories) and the
Franklin building-permit ArcGIS layers (2016-2019) screened for sector terms. Issuer: City of Franklin."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from urllib.parse import urlencode
import lib.net as netfetch
from collectors.tennessee.evidence_store import collect, M, get, read, fetch_layers
LAYERS=('frank2016','frank2017','frank2018','frank2018q4','frank2019')
def download(c,m):
    fetch_layers(c,m,LAYERS)
    if 'franklin_matters' not in m or netfetch.REFETCH:
        uri='https://webapi.legistar.com/v1/franklintn/matters?'+urlencode({'$filter':"substringof('Data Center',MatterTitle) eq true",'$top':1000})
        r=get(uri);rr=read(r)
        if len(rr)>=1000:raise ValueError('Truncated Legistar result')
        m['franklin_matters']=r;m['franklin_histories']={str(a['MatterId']):get('https://webapi.legistar.com/v1/franklintn/matters/'+str(a['MatterId'])+'/histories') for a in rr};collect.dump(M,m)
def rows(m,add):
    for a in read(m['franklin_matters']):
        mid=str(a['MatterId']);r=m['franklin_histories'][mid]
        for h in read(r):
            if h['MatterHistoryActionName']!='approved' or h['MatterHistoryPassedFlag']!=1:continue
            add('franklin-'+str(h['MatterHistoryId']),'Franklin Municipal Planning Commission site plans','Franklin',a['MatterFile'],a['MatterTitle'],'Site plan approval',h['MatterHistoryActionName'],h['MatterHistoryActionDate'][:10],'commission action date','https://franklintn.legistar.com/LegislationDetail.aspx?ID='+str(a['MatterId'])+'&GUID='+a['MatterGuid'],'Matter '+mid+', history '+str(h['MatterHistoryId']),r,dict(agency=h['MatterHistoryActionBodyName'],action=h['MatterHistoryActionText'],matter_status=a['MatterStatusName'],title_source=m['franklin_matters']['url']))
