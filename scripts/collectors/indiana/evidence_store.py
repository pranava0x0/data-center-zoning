"""Indiana shared evidence store: the pinned-bytes capture helpers and file locations used by every Indiana source module
(Indiana DHS, IM3 atlas, IDEM and Hobart decisions)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.net as netfetch
import collections, datetime as dt, gzip, hashlib, html, io, json, re
from pathlib import Path
from pypdf import PdfReader
import lib.discovery as collect
R=Path(__file__).resolve().parents[3]; D=R/'cache/history/in'; M=collector_data('indiana','manifest.json'); C=collector_data('indiana','config.json')
RANK=collector_data('indiana','rank.json'); OUT=series_path('in'); AUDIT=collector_data('indiana','coverage.json')
def sha(b):return hashlib.sha256(b).hexdigest()
def get(u,ext):
    b=netfetch.get(u,timeout=55,limit=40*1024*1024)
    if len(b)>40*1024*1024:raise ValueError('response exceeds 40 MiB')
    if ext=='pdf' and not b.startswith(b'%PDF'):raise ValueError('not a PDF')
    if ext=='json' and 'error' in json.loads(b):raise ValueError('ArcGIS error')
    k=sha(b);p=D/(k+'.'+ext+'.gz');D.mkdir(parents=True,exist_ok=True)
    if not p.exists():p.write_bytes(gzip.compress(b,mtime=0))
    return dict(url=u,ext=ext,bytes=len(b),sha256=k)
def read(x):
    b=gzip.decompress((D/(x['sha256']+'.'+x['ext']+'.gz')).read_bytes())
    if len(b)!=x['bytes'] or sha(b)!=x['sha256']:raise ValueError('Corrupt capture: '+x['url'])
    return b
def txt(x):return ' '.join(html.unescape(re.sub('<[^>]+>','',x)).split())
def parse_date(s):return dt.datetime.strptime(s,'%m/%d/%Y').date().isoformat()
def j(p):return json.loads(p.read_text())
DETAILS=collector_data('indiana','project_forms.json'); DREF=collector_data('indiana','document_refs.json'); INDEX=collector_data('indiana','notice_index.json'); REVIEW=collector_data('indiana','documents.json')
def make_adder(c,out):
    def add(id,dataset,num,project,kind,status,date,role,url,locator,ref,county,details,city=None):
        if date and date>c['cutoff']:return
        out.append(dict(id='in-'+id,state='IN',dataset=dataset,jurisdiction=city or county,record_no=str(num),project=project,kind=kind,status=status,date=date,date_role=role,url=url,locator=locator,source_url=ref['url'],source_sha256=ref['sha256'],details=dict(**({'county':county} if county else {}),**details)))
    return add
def review_rows(c,m,add,keep):
    refs=j(DREF);index=j(INDEX);idx=txt(read(index).decode('utf8','replace'))
    for row in j(REVIEW):
        if not keep(row):continue
        r=refs[row['doc']];reader=PdfReader(io.BytesIO(read(r)));evidence={}
        for pg,anchor in row['checks']:
            st=' '.join(reader.pages[pg-1].extract_text().split())
            if row.get('verified_scan'):
                ocr=j(collector_data('indiana','minutes_ocr.json'))[row['doc']]
                if ocr['sha256']!=r['sha256']:raise ValueError('Scanned decision changed; review new minutes')
                st=' '.join(ocr['pages'][pg-1])
            if collect.norm(anchor) not in collect.norm(st):raise ValueError(f'{row["num"]} missing PDF anchor page {pg}: {anchor}')
            evidence.setdefault(str(pg),[]).append(anchor)
        detail={'agency':row['issuer'],'page_checks':evidence}
        if row.get('scope_note'):detail['decision_scope']=row['scope_note']
        if row.get('posting'):
            rr=read(index).decode('utf8','replace');matches=[s for s in re.findall('<tr\\b.*?</tr>',rr,re.S|re.I) if row['num'].replace(' ','') in txt(s).replace(' ','')]
            if len(matches)!=1 or row['posting'] not in txt(matches[0]):raise ValueError('Notice row or date mismatch '+row['num'])
            detail.update(posting_register=index['url'],posting_register_sha256=index['sha256'])
        add(('hobart-pc-' if row.get('verified_scan') else 'idem-')+re.sub(r'[^a-z0-9-]','',row['num'].lower()),row['dataset'],row['num'],row['name'],row['kind'],row['status'],row['date'],row['role'],r['url'],'PDF '+', '.join('p. '+p for p in evidence),r,row['county'],detail,row.get('city'))
