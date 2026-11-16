"""City of Columbus Accela citizen-access portal (portal.columbus.gov): individual building-permit detail pages,
captured per permit number into portal_manifest.json and read back for the project description."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt, json, re
from urllib.parse import urlencode
from lib.paths import collector_data
import lib.discovery as collect
import lib.net as netfetch
from collectors.ohio.common import DIR, MAN, sha, dump, records
PORTAL=collector_data('ohio','portal_manifest.json')
def current_url(value):
    from urllib.parse import parse_qs,urlsplit
    q=parse_qs(urlsplit(value).query)
    if len(set(q)&{'capID1','capID2','capID3'})!=3:raise ValueError('Missing official Accela case keys')
    return 'https://portal.columbus.gov/Permits/Cap/CapDetail.aspx?'+urlencode({'Module':'Building','TabName':'Building',**{k:q[k][0] for k in ('capID1','capID2','capID3')},'agencyCode':'COLUMBUS'})
def portal_fetch(m,reuse=False):
    import gzip
    old=json.loads(PORTAL.read_text()).get('documents',{}) if PORTAL.exists() and reuse else {}
    result={}
    for p in m['joins']:
        for a,_ in records(p):
            num=a['B1_ALT_ID'];url=current_url(a['ACA_URL'])
            if num in result:continue
            if num in old and 'sha256' in old[num] and old[num]['url']==url:
                result[num]=old[num];continue
            try:
                b=netfetch.get(url,timeout=20,retries=1,limit=3*1024*1024)
                if b'<html' not in b.lower():raise ValueError('Unexpected portal response')
                k=sha(b);pfile=DIR/(k+'.html.gz')
                if not pfile.exists():pfile.write_bytes(gzip.compress(b,mtime=0))
                result[num]={'url':url,'sha256':k,'bytes':len(b),'ext':'html.gz'}
            except (ValueError,OSError) as e:result[num]={'url':url,'error':str(e)}
            if len(result)%30==0:print('Municipal individual records:',len(result),flush=True)
    dump(PORTAL,{'captured_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'gis_manifest_sha256':sha(MAN.read_bytes()),'documents':result})
def portal_read(ref,num):
    import gzip
    if 'sha256' not in ref:return None
    b=gzip.decompress((DIR/(ref['sha256']+'.html.gz')).read_bytes())
    if sha(b)!=ref['sha256'] or len(b)!=ref['bytes']:raise ValueError('Portal archive integrity failure')
    html=b.decode('utf-8','replace')
    parser=collect.HTML();parser.feed(html);top=' '.join(' '.join(parser.parts).split())[:420]
    if not re.search(r'\bRecord\s+'+re.escape(num)+r'\s*:',top,re.I):return None
    found=re.search(r'Project Description:</span></h1>.*?<td[^>]*>\s*</td>\s*<td[^>]*>(.*?)</td>',html,re.S|re.I)
    if not found:return None
    parser=collect.HTML();parser.feed(found[1]);return ' '.join(' '.join(parser.parts).split())
