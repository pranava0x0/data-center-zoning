"""City of New Albany community-development project-updates page: commercial data-building leads (new_albany_leads.json)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt, json, re
from lib.paths import collector_data
import lib.discovery as collect
import lib.net as netfetch
from collectors.ohio.common import DIR, sha, dump
def new_albany_leads(refresh=False):
    import gzip
    pagesource='https://newalbanyohio.org/community-development/project-updates/'
    marker=collector_data('ohio','new_albany_leads_source.json')
    if refresh:
        b=netfetch.get(pagesource,timeout=30,limit=5*1024*1024)
        checksum=sha(b);(DIR/(checksum+'.html.gz')).write_bytes(gzip.compress(b,mtime=0));dump(marker,{'url':pagesource,'sha256':checksum,'bytes':len(b),'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat()})
    ref=json.loads(marker.read_text());b=gzip.decompress((DIR/(ref['sha256']+'.html.gz')).read_bytes())
    if sha(b)!=ref['sha256'] or len(b)!=ref['bytes']:raise ValueError('Commercial lead source hash mismatch')
    page=b.decode('utf-8','replace');heads=list(re.finditer(r'<h2\b[^>]*>(.*?)</h2>',page,re.I|re.S));out=[]
    def htmltext(raw):
        pa=collect.HTML();pa.feed(raw);return ' '.join(' '.join(pa.parts).split())
    for idx,hdr in enumerate(heads[:-1]):
        text=htmltext(page[hdr.end():heads[idx+1].start()]);title=htmltext(hdr[1])
        match=re.search(r'Project description:\s*(New data (?:building|center))\b',text,re.I)
        if match:out.append({'project':title,'municipality':'New Albany','description':match[1],'basis':'City commercial project update; no permit number, issue date or confirmed operation','url':pagesource})
    if not out:raise ValueError('New Albany list layout changed')
    dump(collector_data('ohio','new_albany_leads.json'),out)
