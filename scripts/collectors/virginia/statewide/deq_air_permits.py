"""Offline government history + explicit reconciliation to a separately published table.

Run with no args to rebuild pinned release. --check performs a byte-for-byte
rebuild test without writing. --fetch or --html consumes a government register
with the config's header mapping; writes a separate dated snapshot, never
silently overwrites history. All paths relative to repository root except
user-supplied config, html, and output. Reconfigurable for comparable HTML tables.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
from lib.text import TableParser
import lib.net as netfetch
import argparse
import csv
import gzip
from collections import Counter,defaultdict
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin,urlsplit
from urllib.request import Request,urlopen
import lib.discovery as collect

R=Path(__file__).resolve().parents[4]
CACHE=R/'cache/history/air'
CONFIG=collector_data('virginia/statewide/deq_air_permits','config.json')
OUTPUT=series_path('air')
ROOTKEYS=('project','record_no','date','kind','jurisdiction','region')
MIRRORKEYS=('facility','permit','issued','program_type','locality','regional_office')
def clean(s):return ' '.join(s.split())
def norm(s):return re.sub(r'[^a-z0-9]','',s.casefold())
def valid_url(url,hosts):
    u=urlsplit(url)
    return u.scheme in ('http','https') and u.hostname in hosts
def read(p):return json.loads(p.read_text())
def rendered(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def iso(s,c):
    for fmt in c['date_formats']:
        try:return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:continue
    raise ValueError('date not recognized: '+s)
def ck_pairs(fields):return tuple(norm(str(s)) for s in fields)
def encode(c,row,source,method,edition,document=None,**extra):
    if len(row)!=6 or not all(row[i] for i in (0,1,3,4)) or not re.fullmatch(c['record_no_regex'],row[1]):raise ValueError(f"Malformed record {row!r}")
    name,n,when,kind,where,region=row
    dd=iso(when,c) if when or not c.get('allow_missing_date') else None
    if edition and dd and dd>edition:raise ValueError(f"Date {dd} exceeds snapshot date {edition}")
    if document and not valid_url(document,c['allowed_link_hosts']):raise ValueError('non-government PDF reference')
    return dict(id=c['slug']+'-'+n,dataset=c['dataset'],jurisdiction=where,record_no=n,project=name,kind=kind,status=c['default_status'],date=dd,date_role=c['date_role'],url=source,locator=f"Issued register → registration/application {n}",source_url=source,
                details=dict(state=c['state'],region=region or None,source_date_text=when or None,source_asof=edition,evidence_method=method,**({'document_reference':document} if document else {}),**extra))
def parse_html(c,raw,edition=None):
    t=TableParser();t.feed(raw.decode('utf-8-sig'))
    if not edition:
        m=re.search(c['snapshot_heading_date_regex'],clean(' '.join(t.text)))
        if not m:raise ValueError('source edition missing; pass --as-of with an inspected date')
        edition=datetime.strptime(m[1],c['snapshot_date_format']).date().isoformat()
    sets=[]
    for table in t.tables:
        for idx,row in enumerate(table):
            heads=[norm(''.join(x['text'])) for x in row]
            cols={}
            for field,aliases in c['column_labels'].items():
                match=[i for i,x in enumerate(heads) if x in {norm(a) for a in aliases}]
                if len(match)==1:cols[field]=match[0]
            fixed=c.get('constant_fields',{})
            if not set(ROOTKEYS).issubset(set(cols)|set(fixed)):continue
            out=[]
            for i,rr in enumerate(table[idx+1:],idx+2):
                cells=[clean(''.join(x['text'])) for x in rr]
                if not any(cells):continue
                if [norm(x) for x in cells]==heads:continue
                if len(cells)!=len(heads):raise ValueError(f'Unexpected column count in government table row {i}')
                data=[cells[cols[k]] if k in cols else fixed[k] for k in ROOTKEYS]
                linked=c.get('linked_field')
                links=[urljoin(c['source_url'],l) for l in rr[cols[linked]]['links']] if linked in cols else []
                allowed=[l for l in links if valid_url(l,c['allowed_link_hosts'])]
                if len(set(allowed))>1:raise ValueError(f'Ambiguous document URLs at {i}')
                entry=encode(c,data,c['source_url'],'archived government HTML',edition,allowed[0] if allowed else None,table_row=i)
                if 'status' in cols:entry['status']=cells[cols['status']] or c['default_status']
                out.append(entry)
            sets.append(out);break
    if len(sets)!=1 or not sets[0]:raise ValueError('Expected exactly one nonempty matching government register')
    rows=sets[0]
    if len(set(x['record_no'] for x in rows))!=len(rows):raise ValueError('Duplicate agency record number')
    counts=Counter(x['details'].get('document_reference') for x in rows)
    for r in rows:
        u=r['details'].get('document_reference')
        if u and counts[u]>1:r['details']['shared_document_url']=True
    return sorted(rows,key=lambda x:(x['date'] or '',x['record_no']))
def release(c):
    cc=c['release'];source=c['source_url']
    inputs=read(collector_data('virginia/statewide/deq_air_permits','hashes.json'))
    for name,signature in inputs.items():
        if digest((CACHE/name).read_bytes())!=signature:raise ValueError('Archived input checksum mismatch: '+name)
    meta=read(CACHE/c['package'])
    res=next(x for x in meta['resources'] if x['path']==c['republished_url'])
    raw=(CACHE/c['republished_csv']).read_bytes()
    if 'sha256:'+digest(raw)!=res['hash'] or len(raw)!=res['bytes'] or meta['version']!=cc:raise ValueError('Publisher data-package manifest mismatch')
    with (CACHE/c['republished_csv']).open(newline='',encoding='utf-8-sig') as f:mirror=list(csv.DictReader(f))
    if len({x['permit'] for x in mirror})!=len(mirror):raise ValueError('duplicate ID in latest inventory')
    official=defaultdict(list); hashes={}
    for block in read(CACHE/c['official_cells']):
        if not valid_url(block['source_url'],c['allowed_link_hosts']):raise ValueError('nonofficial corroboration')
        date=block.get('source_asof')
        if date:date=datetime.strptime(date,'%B %d, %Y').date().isoformat()
        for line in block['lines']:
            row=[clean(x) for x in line.split('|')]
            if len(row)!=6 or not re.fullmatch(c['record_no_regex'],row[1]):raise ValueError(f'Partial indexed row: {row}')
            # Some cached fragments end at a column boundary. Retain them in
            # the archive; do not count an incomplete or malformed observation.
            if not all(row) or row[5].endswith('...') or len(row[0])>240:continue
            item=(row,date,block['source_url'])
            if item not in official[row[1]]:official[row[1]].append(item)
    alt={x['record_no']:x for x in read(CACHE/c['vpt_cells'])}
    inventory={r['permit']:r for r in mirror}
    urls=Counter(r['source_url'] for r in mirror)
    public=[];held=[]
    for n,record in inventory.items():
        values=[record[k] for k in MIRRORKEYS]
        matches=[a for a in official[n] if ck_pairs(a[0])==ck_pairs(values)]
        safe_doc=record['source_url'] if urls[record['source_url']]==1 else None
        info=dict(snapshot_membership='in dated November republication',republished_snapshot=cc,republished_snapshot_url=c['republished_url'])
        if matches:
            m=sorted(matches,key=lambda a:(a[1] or '',a[2]==source),reverse=True)[0]
            o=encode(c,m[0],source,'six fields matched to indexed government register',m[1],None,indexed_page=m[2],**info)
            # The source register text verifies row values; supplement, but do
            # not represent mirror-extracted document links as validated PDFs.
            if safe_doc:o['details']['republished_document_reference']=safe_doc
            else:o['details']['ambiguous_republished_document_url']=record['source_url']
            public.append(o)
        elif n in alt:
            v=alt[n]
            if not valid_url(v['url'],['permits.virginia.gov']) or v['status']!='Approved':raise ValueError('bad official cross-check')
            if iso(v['date'],c)!=iso(record['issued'],c):raise ValueError('date differs in independent state source; needs review')
            o=encode(c,values,source,'government application tracker (approval; not issuance)',cc,None,**info)
            o.update(jurisdiction=v['locality'],project=v['facility'],kind=v['kind'],status=v['status'],date=iso(v['date'],c),date_role='application completion',url=v['url'],source_url=v['url'],locator=v['locator'])
            o['details'].update(issuance_register=source,republished_locality=record['locality'],source_asof=None,source_date_text=v['date'],region=None,republished_document_reference=safe_doc,republished_issue_date=record['issued'])
            public.append(o)
        else:
            o=encode(c,values,source,'republication only — official row not corroborated',cc,None,**info)
            o['details']['republished_document_reference']=safe_doc
            held.append(o)
    # Historical actions no longer listed in November; not equivalent to denial,
    # revocation, retirement or a current permit. Preserve only unambiguous rows.
    for n,items in official.items():
        if n in inventory:continue
        complete=[a for a in items if all(a[0])]
        interpretations={ck_pairs(a[0]) for a in complete}
        if len(interpretations)!=1 or not complete:continue
        row,edition,indexed_page=sorted(complete,key=lambda a:(a[1] or '',a[2]==source),reverse=True)[0]
        public.append(encode(c,row,source,'indexed government register — earlier listing',edition,None,indexed_page=indexed_page,snapshot_membership='earlier official listing; absent from November republication'))
    # Official government ArcGIS Hub independently identifies FACILITIES only.
    # No issue date or permit-action suffix can be inferred from this layer.
    item=read(CACHE/'deq_air_sites.item.json');iid=c['air_sites_item']
    if item['id']!=iid or item.get('owner')!='maddie.moore_VADEQ':raise ValueError('Air Sites publisher mismatch')
    with gzip.open(CACHE/'deq_air_sites.csv.gz','rt',encoding='utf-8-sig',newline='') as fp:
        source_sites=list(csv.DictReader(fp))
    sites=[s for s in source_sites if s['PLA_DATA_CENTER_YN'].strip().upper()=='Y']
    by_site={s['PLA_REG_NUM']:s for s in sites}
    if len(by_site)!=len(sites):raise ValueError('ambiguous Air Sites identifier')
    inv_ids={r['permit'].split('-')[0] for r in mirror}
    crosswalk=[]
    for reg in sorted(set(by_site)|inv_ids):
        g=by_site.get(reg)
        crosswalk.append(dict(registration=reg,in_republished_permit_register=reg in inv_ids,in_official_dc_flagged_air_sites=bool(g),
            site_name=g['PLA_NAME'] if g else None,site_status=g['AIR_OP_STATUS'] if g else None,
            objectid=g['OBJECTID'] if g else None,source_url=f"https://www.arcgis.com/home/item.html?id={iid}"))
    for r in public+held:
        reg=r['record_no'].split('-')[0];site=by_site.get(reg)
        r['details']['deq_air_sites_match']={'registration':reg,'matched':bool(site),'objectid':site['OBJECTID'] if site else None,
            'source_url':f"https://www.arcgis.com/home/item.html?id={iid}",'scope':'facility identity only; no permit action dates'}
    public.sort(key=lambda x:(x['date'] or '',x['record_no']));held.sort(key=lambda x:(x['date'] or '',x['record_no']))
    assert len({x['id'] for x in public+held})==len(public)+len(held)
    assert len(held)+sum(r['record_no'] in inventory for r in public)==len(inventory)
    return public,held,crosswalk
def applications(c, decisions, site_rows):
    groups=read(CACHE/c['vpt_rolling_file'])
    if [g['query'] for g in groups]!=c['vpt_terms']:raise ValueError('VPT scope differs from config')
    hits={}; terms=defaultdict(list)
    for g in groups:
        if len(g['data'])!=g['count'] or len({r['id'] for r in g['data']})!=g['count']:raise ValueError('incomplete VPT search')
        for r in g['data']:
            if r['agency']!='DEQ' or r['programType']!='Air Permits':continue
            k=r['id']
            if k in hits and r!=hits[k]:raise ValueError('conflicting VPT snapshots for same id')
            hits[k]=r;terms[k].append(g['query'])
    exact=defaultdict(list); facility=defaultdict(list)
    for o in decisions:
        exact[o['record_no']].append(o['id']);facility[o['record_no'].split('-')[0]].append(o['id'])
    sites={x['registration'] for x in site_rows if x['in_official_dc_flagged_air_sites']}
    accepted=[]; review=[]
    for k,r in sorted(hits.items()):
        n=r['applicationNumber'] or r['permitNumber'];reg=n.split('-')[0];site=clean(r['facility']) or None
        if not re.fullmatch(c['record_no_regex'],n):raise ValueError('unrecognized VPT air permit number')
        external=c['vpt_project_association'].get(n)
        if reg in facility or reg in sites:method='exact DEQ registration number in a government data-center inventory'
        elif re.search(r'(?i)\bdata[ -]?cent(?:er|re)s?\b', site or ''):method='explicit facility name in government air application'
        elif external and site==external['site'] and r['locality']==external['locality']:method='named government project notice, same facility and jurisdiction'
        else:method=None
        d=r.get('applicationReceivedDate')
        if d:
            dd=datetime.fromisoformat(d).date().isoformat()
            if dd>'2026-11-15':raise ValueError('future application received date')
        else:dd=None
        u='https://permits.virginia.gov/Permit/Details/'+str(k)
        o=dict(id='va-vpt-air-'+str(k)+'-application',dataset='Virginia Permit Transparency — DEQ air applications',jurisdiction=r['locality'],record_no=n,project=site or clean(r['applicantName']),kind=r['permitType'],status=r['status'],date=dd,date_role='application received',url=u,source_url=u,locator=f'VPT search result ID {k}, applicationReceivedDate and applicationNumber',
            details=dict(state='VA',vpt_id=k,agency=r['agency'],program_type=r['programType'],permit_status=r['permitStatus'],registration=reg,match_basis=method,explicit_project_source=external,discovery_queries=terms[k],exact_register_action_ids=exact.get(n,[]),same_facility_history_ids=sorted(facility.get(reg,[])),source_table='https://permits.virginia.gov/Permit/Search', evidence_method='archived government VPT search response',snapshot_membership='rolling VPT public search sample'))
        (accepted if method else review).append(o)
    return sorted(accepted,key=lambda o:(o['date'] or '',o['id'])),review

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=Path,default=CONFIG);ap.add_argument('--refresh-vpt',action='store_true',help='fetch a new dated raw VPT sample without altering the pinned release');ap.add_argument('--check',action='store_true')
    grp=ap.add_mutually_exclusive_group();grp.add_argument('--html',type=Path);grp.add_argument('--fetch',action='store_true');ap.add_argument('--as-of');ap.add_argument('--out',type=Path);a=ap.parse_args()
    c=read(a.config);CACHE.mkdir(exist_ok=True,parents=True)
    if a.refresh_vpt:
        import collectors.virginia.statewide.deq_water_permits as water
        groups=[]
        for term in c['vpt_terms']:
            collect.policy(water.VPT+'SearchDatatable');groups.append(water.get_vpt(term))
        s=rendered(groups);p=CACHE/('vpt-search-'+digest(s.encode())[:16]+'.json');p.write_text(s);print(p);return
    if a.fetch or a.html:
        if a.fetch:
            # Save blocked requests as failures, never bypass consent or switch to a hidden proxy.
            r=netfetch.request(c['source_url'],timeout=20,retries=1,limit=collect.LIMIT)
            if r.mime not in ('text/html','application/xhtml+xml'):raise ValueError('unexpected MIME')
            raw=r.body
            if len(raw)>collect.LIMIT:raise ValueError('too large')
        else:raw=a.html.read_bytes()
        rows=parse_html(c,raw,a.as_of);sha=digest(raw)
        outfile=a.out or series_path('air').with_name(f"deq_air_permits_{c['slug']}_{rows[0]['details']['source_asof']}_{sha[:12]}.json")
        if not a.check:(CACHE/(sha+'.html')).write_bytes(raw)
        result={outfile:rows}
    else:
        rows,held,crosswalk=release(c)
        apps,unconfirmed=applications(c,rows,crosswalk)
        combined=sorted(rows+apps,key=lambda x:(x['date'] or '',x['id']))
        if len({x['id'] for x in combined})!=len(combined):raise ValueError('event key collision')
        result={a.out or OUTPUT:combined,collector_data('virginia/statewide/deq_air_permits','held.json'):held,collector_data('virginia/statewide/deq_air_permits','site_crosswalk.json'):crosswalk,collector_data('virginia/statewide/deq_air_permits','applications.json'):apps,collector_data('virginia/statewide/deq_air_permits','application_leads.json'):unconfirmed}
    for p,v in result.items():
        s=rendered(v)
        if a.check:
            if not p.exists() or s!=p.read_text():raise SystemExit(f'{p.name} absent or differs')
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
        print(f"{p.name}: {len(v)}")
if __name__=='__main__':main()
