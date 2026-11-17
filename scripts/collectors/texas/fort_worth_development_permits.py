"""City of Fort Worth: development permits (ArcGIS feature layer), keyword-matched on the configured search fields."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.files import dump, sha
from lib.net import req
from lib.terms import MATCH, patterns
from lib.text import isodate, Fields
import lib.arcgis as arcgis
import gzip, json, re
from urllib.parse import urlencode, quote
from collections import Counter
from urllib.parse import urlencode
from collectors.texas.common import ROOT, C, CONFIG, saver
K='fort_worth'
def download(m):
    save=saver(m)
    x=CONFIG['fort_worth'];off=[0]
    def g(u,**p):
        b=req(u,p)
        if 'returnIdsOnly' in p:name='fort_worth-ids.json.gz'
        else:name=f'fort_worth-{off[0]}.json.gz';off[0]+=125
        save(name,b,u+'?'+urlencode(p));return json.loads(b)
    r=arcgis.pull(g,lambda j:j,x['url'],patterns(x['search'],'UPPER'),x['fields'],'ObjectId',125,id_params={'f':'json'},page_params={'f':'json'})
    print('fort_worth',len(r['ids']['objectIds']),flush=True)
def rows(m,add,exclusions):
    k,city='fort_worth','Fort Worth';x=CONFIG[k]
    for n in sorted(m):
        if not re.fullmatch(k+r'-\d+\.json\.gz',n):continue
        r=json.loads(gzip.decompress((C/n).read_bytes()))
        for a in ([z['attributes'] for z in r['features']] if k=='fort_worth' else r):
            text=' | '.join(str(a.get(f) or '') for f in x['search']);match=MATCH.search(re.sub(r"(?<=[a-z])(?=[A-Z])"," ",text))
            if not match:
                exclusions.append((k,a.get('rowid',a.get('ObjectId')),'no explicit keyword',text[:200]));continue
            no=a['Permit_No'];oid=a['ObjectId'];desc=a.get('B1_WORK_DESC') or '';name=a.get('B1_SPECIAL_TEXT') or '';kind=' / '.join(str(a[key]) for key in ['Permit_Type','Permit_SubType','Permit_Category'] if a.get(key) not in (None,'','NA'));dt=isodate(a['Status_Date']) or isodate(a['File_Date']);role='Status date' if isodate(a['Status_Date']) else 'File date';status=a['Current_Status'];url=x['url']+'/query?'+urlencode({'where':"Permit_No = '"+no.replace("'","''")+"'","outFields":x['fields'],'returnGeometry':'false','f':'pjson'});loc=f'permit {no}';extra={'file_date':isodate(a.get('File_Date')),'source_status_date':isodate(a.get('Status_Date')),'land_use':a.get('Specific_Use'),'work_description':desc,'project_label':name,'address':a['Full_Street_Address']};project=name or (a['Full_Street_Address'] or desc[:100])
            extra['matched_text']=match.group();add(k,n,no,project,kind,status,dt,role,url,loc,extra,city,row_id=oid)
def coverage(m):
    """Replay check that every candidate id was archived; returns the candidate ids."""
    fw=json.loads(gzip.decompress((C/'fort_worth-ids.json.gz').read_bytes()))['objectIds']
    observed_fw=[a['attributes']['ObjectId'] for n in m if re.fullmatch('fort_worth-\\d+\\.json\\.gz',n) for a in json.loads(gzip.decompress((C/n).read_bytes()))['features']]
    if sorted(fw)!=sorted(observed_fw):raise ValueError('Fort Worth replay coverage failed')
    return fw
