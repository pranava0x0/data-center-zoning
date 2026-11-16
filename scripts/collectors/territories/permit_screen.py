"""Check disclosed descriptions in the CNMI's two public permit layers and named territorial primary sources."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import argparse, collections, csv, io, json, re
from lib.url_archive import Archive
import lib.discovery as c
D=c.R/'data/national'
APP='https://www.arcgis.com/sharing/rest/content/items/8e9515c7297542d091cfd6c0a94176d2/data?f=json'
DEF=re.compile(r'\b(?:data[ -]*cent(?:er|re)s?|centros? de (?:datos|[cóo]mputos)|server farm|hyperscal(?:e|er))\b',re.I)
def run(fetch):
 a=Archive('territorial',fetch,owner='territories',name='territorial_sources.json');published=a.json(APP);mapset=next(r for r in published['operationalLayers'] if r.get('title')=='Permit Information (Saipan only)')
 specs=[('CNMI permitted sites','866adabc4cf0488abe15aa031765de67','0'),('Saipan permit information',mapset['itemId'],mapset['url'].rsplit('/',1)[1])];records=[]
 for title,id,layer in specs:
    url=f'https://hub.arcgis.com/api/download/v1/items/{id}/csv?layers={layer}'
    try:b,sha=a.get(url);data=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
    except Exception as e:
        if not fetch:raise
        records.append(dict(state='MP',name=title,url=url,outcome='Unavailable',error=str(e)));continue
    fields=[k for k in (data[0] if data else {}) if k in ('project_de','name_of_pr','permit_typ') or re.search('descrip|project name|dba|project type',k,re.I)]
    if not fields:
        if b.startswith(b'{') and json.loads(b).get('status')=='Pending':
            records.append(dict(state='MP',name=title,url=url,sha256=sha,outcome='Publisher preparing CSV; no records examined'));continue
        raise ValueError('Missing project-description fields in '+url)
    hits=[{k:r[k] for k in fields} for r in data if DEF.search(' '.join(r[k] or '' for k in fields))]
    records.append(dict(state='MP',name=title,url=url,sha256=sha,rows=len(data),described_rows=sum(any((r[k] or "").strip() for k in fields) for r in data),fields=fields,candidates=hits,outcome='Explicit project name/description checked; not a legal absence finding'))
 # The parent office and its actual public-review pages are not a substitute for an exhaustive case register.
 ua='https://dpnr.vi.gov/coastal-zone-management/what-we-do/coastal-zone-permitting/'
 b,sha=a.get(ua);text=c.parse(b,'text/html',ua)[1];records.append(dict(state='VI',name='Major CZM permits currently offered for public review',url=ua,sha256=sha,scope='Public posting titles only, not every attachment or historical decision',candidates=[text[max(0,m.start()-40):m.end()+70] for m in DEF.finditer(text)]))
 pr='https://gis.jp.pr.gov/mipr/';idx=c.read(c.INDEX,{});src=c.read(D/'initial_rule_sources.json',[])[5];records.append(dict(state='PR',name='Planning Board/OGPe construction permit history',url=pr,catalog=src,catalog_sha256=idx[c.address(src)]['sha256'],outcome=idx.get(c.address(pr),{}).get('error','Check service'),scope='Statistics Institute documents exclusions for some autonomous municipalities. A failed service connection is not a no-permit result.'))
 u='https://doc.as.gov/application-center';s=idx.get(c.address(u),{});records.append(dict(state='AS',name='Department of Commerce application center',url=u,sha256=s['sha256'],scope='Publishes application forms; no list of signed data center decisions located on page.'))
 records.append(dict(state='GU',name='Guam Hybrid Land Use Commission minutes',url='https://dlm.guam.gov/wp-dlm-content/uploads/2024/02/GHLUC-MAY122022.pdf',scope='Two Tamuning votes in the published local history.'))
 pr_rows=c.read(series_path('pr'),[]);pr_audit=c.read(collector_data('puerto_rico','coverage.json'),{})
 if pr_rows:
    records.append(dict(state='PR',name='Planning Board permit and consultation layers (working service)',url='https://sigejp.pr.gov/server/rest/services/MIPR/Permisos/MapServer',rows=pr_audit['unique_features'],published=len(pr_rows),held=pr_audit['held'],municipalities=pr_audit['municipalities'],scope='Named case reviews and dated decisions. Original GIS launch page failure does not describe this working register.'))
 for st,z in c.read(collector_data('territories','territorial_review.json'),{}).items():
    docs=z['linked_pdf_or_notice_documents'];records.append(dict(state=st,name='Agency notices and supporting documents',url=docs[0]['url'],documents_checked=len(docs),review_manifest='data/history/territories/territorial_review.json',scope='Public notices and published attachments only. No individual data center authorization verified from these documents.'))
 gu=c.read(series_path('guref_gu'),[])
 if gu:records.append(dict(state='GU',name='Interagency referrals',url=gu[0]['url'],published=len(gu),scope='Agency referrals; do not count as issued permits.'))
 c.dump(D/'territory_history_checks.json',records);print([(r['state'],r.get('rows'),len(r.get('candidates',[]))) for r in records])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
