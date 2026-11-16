"""Bounded search of U.S. EPA-issued CAA air case registers. A text hit is never a permit."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import lib.net as netfetch
import argparse, csv, json, re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin,urlsplit
from pathlib import Path
from urllib.request import Request,urlopen
import lib.discovery as c
R=c.R;BASE=R/'cache/history/federal-air';RAW=BASE/'raw';INDEX=BASE/'manifest.json';OUT=R/'data/national';CONFIG=OUT/'federal_air_sources.tsv'
PAT=re.compile(r'\b(?:data\s*[ -]?cent(?:er|re)s?|cloud (?:comput(?:e|ing)|campus|provider)|hyperscal(?:e|er)|server\s+farms?|data processing|high[ -]performance comput(?:e|ing)|colocation|co-location|Amazon(?: Web Services)?|AWS|Google|Meta Platforms|Microsoft|QTS|Equinix|CoreWeave|Vantage Data|Stack Infrastructure|CyrusOne|Digital Realty|xAI|bitcoin|blockchain|cryptocurrency|Crusoe|Great American Mining)\b',re.I)
def save(k,u):
    meta=dict(key=k,url=u)
    try:
        res=netfetch.request(u,timeout=22,retries=1,limit=c.LIMIT);b=res.body;mime=res.mime;url=res.url
        if len(b)>c.LIMIT:raise ValueError('size limit exceeded')
        h=c.digest(b);RAW.mkdir(exist_ok=True,parents=True);(RAW/(h+'.bin')).write_bytes(b)
        if b.lstrip().startswith(b'<?xml'):
            import xml.etree.ElementTree as ET
            root=ET.fromstring(b);typ='ecfr_xml';s=' '.join(' '.join(root.itertext()).split())
        else:typ,s,links=c.parse(b,mime,url)
        (RAW/(h+'.txt')).write_text(s)
        meta.update(sha256=h,text_sha256=c.digest(s.encode()),adapter=typ,bytes=len(b),resolved=url,fetched_at=c.now())
    except Exception as e:meta.update(error=f'{type(e).__name__}: {e}',attempted_at=c.now())
    return meta
def fetch(spec):
    groups={}
    for r in spec:groups.setdefault(urlsplit(r['url']).hostname,[]).append(r)
    ix=c.read(INDEX,{})
    with ThreadPoolExecutor(3) as ex:
        for batch in ex.map(lambda rs:[save(r['key'],r['url']) for r in rs],groups.values()):
            for d in batch:
                old=ix.get(d['key'],{})
                if old.get('sha256') and d.get('error'):old['last_failed_refresh']=d
                else:ix[d['key']]=d
    c.dump(INDEX,ix)
def plain(html):
    h=c.HTML();h.feed(html);return ' '.join(''.join(h.parts).split())
def elements(html,tag):
    return re.findall('<'+tag+r'\b[^>]*>(.*?)</'+tag+'>',html,re.S|re.I)
def main():
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--fetch-missing',action='store_true');a=p.parse_args()
    spec=list(csv.DictReader(CONFIG.open(),delimiter='\t'))
    if a.refresh:fetch(spec)
    elif a.fetch_missing:
        existing=c.read(INDEX,{});fetch([r for r in spec if not existing.get(r['key'],{}).get('sha256') or existing[r['key']]['url']!=r['url']])
    ix=c.read(INDEX,{});checks=[];rows=[];candidates=[]
    for src in spec:
        k,u=src['key'],src['url'];d=ix[k];chk={**src,'status':'snapshot' if d.get('sha256') else 'unavailable'}
        if not d.get('sha256'):chk['error']=d['error'];checks.append(chk);continue
        h=d['sha256'];b=(RAW/(h+'.bin')).read_bytes();t=(RAW/(h+'.txt')).read_bytes();assert c.digest(b)==h and c.digest(t)==d['text_sha256']
        chk.update(sha256=h);checks.append(chk)
        if src['role'] not in ('federal action register','public notice','PSD authority / public notice route'):continue
        htm=b.decode('utf8','replace');art=elements(htm,'article');main=art[0] if art else (elements(htm,'main') or [htm])[0]
        # EPA regional templates include left navigation inside <main>. Use the field body if present.
        main=re.split(r'<aside\b|<nav\b|<div[^>]*class="[^"]*region--sidebar',main,1)[0]
        ts=elements(main,'table');count=0
        for ti,table in enumerate(ts,1):
            for ri,tr in enumerate(elements(table,'tr'),1):
                if not re.search(r'<td\b',tr,re.I):continue
                cells=[plain(a) for a in re.findall(r'<t[hd]\b[^>]*>(.*?)</t[hd]>',tr,re.S|re.I)];val=' | '.join(cells)
                hh=c.HTML();hh.feed(tr);links=[dict(label=b,url=urljoin(u,a)) for a,b in hh.links if not a.startswith(('mailto:','#'))]
                row=dict(register=k,region=src['region'],table=ti,row=ri,cells=cells,links=links);rows.append(row);count+=1
                hits=sorted(set(m[0] for m in PAT.finditer(val+' '+' '.join(z['url'] for z in links))))
                if hits:candidates.append(dict(register=k,locator=f'table {ti} row {ri}',terms=hits,context=val[:650],url=u))
        # Non-table bodies include facilities, notices or links that a table-only scraper would miss.
        rest=re.sub(r'<table\b.*?</table>',' ',main,flags=re.I|re.S);body=plain(rest)
        for m in PAT.finditer(body):
            candidates.append(dict(register=k,locator='register text outside tables',terms=[m[0]],context=body[max(0,m.start()-90):m.end()+130],url=u))
        chk.update(table_rows=count,tables=len(ts),body_chars=len(body))
    c.dump(OUT/'federal_air_registers.json',checks);c.dump(OUT/'federal_air_register_rows.json',rows);c.dump(OUT/'federal_air_screen_hits.json',candidates)
    decisions=c.read(OUT/'federal_air_decisions.json',{})
    if decisions:
        assert {r['register']+'|'+r['locator']+'|'+','.join(r['terms']) for r in candidates}==set(decisions['hit_dispositions']), 'screen changed; review all new hits'
    if decisions:write_history(ix,rows,decisions)
    print(json.dumps(dict(sources=len(checks),available=sum(r['status']=='snapshot' for r in checks),register_rows=len(rows),screen_hits=len(candidates)),sort_keys=True))

DS='US EPA Region 8 tribal minor NSR final actions'
def write_history(ix,rows,decisions):
    specs=list(csv.DictReader((OUT/'federal_air_cases.tsv').open(),delimiter='\t'))
    data=[];norm=c.norm
    def text(key):return norm((RAW/(ix[key]['sha256']+'.txt')).read_text())
    for rec in specs:
        st=rec['source'];u=ix[st]['url'];d=rec['date'];g=rec['project_key'];rn=rec['record_no'];site='TAT-008149' if g=='crosby' else 'TAT-008173'
        ctx=decisions['government_docket_checks'];ev=text(st)
        assert norm(rec['source_anchor']) in ev and norm(rec['status']) in ev and rec['docket'].lower() in ev
        assert norm('Fort Berthold Indian Reservation') in ev
        is_c=g=='crosby';key='crosby-original' if is_c else 'eagle-model'
        assert ('crosby chase ctb data mining operation' if is_c else 'power small data centers') in text(key)
        site_rows=[r for r in rows if r['register']=='r8' and any(site in s for s in r['cells'])]
        assert len(site_rows)==1
        location=site_rows[0]['cells'][1];county=location.split(', ')[1];assert county.endswith('County')
        assert rn in site_rows[0]['cells'] or rn in ctx['crosby_identifiers']['records']
        det=dict(authority_level='federal',issuer_level='federal',authority='US EPA Region 8, Air and Radiation Division',federal_issuer='US Environmental Protection Agency',county=county,tribal_geography='Fort Berthold Indian Reservation',source_facility_id=site,register_number=rn,source_sha256=ix[st]['sha256'],effective_date=rec['effective'],later_revision_effective=rec['superseded'] or None,source_evidence=rec['source_anchor'],facility_evidence_url=ix[key]['url'],facility_evidence_sha256=ix[key]['sha256'],federal_program='Tribal Minor New Source Review (CAA Title I / 40 CFR Part 49)',application='Onsite generators for small data centers using field gas. No inference of a hyperscale, AI or emergency-only facility.',docket_url='https://www.regulations.gov/docket/'+rec['docket'])
        if is_c:
            det['facility_scope_document']=ctx['crosby_scope']['url']
            if rec['case']!='crosby-2024':det['historical_number_source']=ctx['crosby_identifiers']['url']
        data.append(dict(id='federal-air-'+rec['case'],dataset=DS,state='ND',jurisdiction='US EPA Region 8 — Fort Berthold Indian Reservation',record_no=rn,project='Crusoe Energy Systems, Inc. — '+('Crosby Chase Central Tank Battery' if is_c else 'Charging Eagle 21-25 Pad'),kind=rec['kind'],status=rec['status'],date=d,date_role='EPA issuance of this permit version',url=u,source_url=ix['r8']['url'],locator=rec['docket']+'; EPA final-action summary, opening paragraph; Region 8 final register, tribal minor NSR table',details=det))
    assert len(data)==4 and len(set(r['details']['source_facility_id'] for r in data))==2
    c.dump(series_path('federalair_nd'),sorted(data,key=lambda r:(r['date'],r['id'])))
def classify(r,cutoff,perm,no,app,obs):
    from datetime import date
    if r.get('dataset')!=DS:return None
    dt=r['details'];sup=dt.get('later_revision_effective');when=date.fromisoformat(r['date'])
    if when>cutoff:return no('EPA issued this version after the cutoff.','out_of_period')
    bucket='historical' if sup and date.fromisoformat(sup)<=cutoff else 'unconfirmed'
    why='EPA documents replacement by a subsequent version.' if bucket=='historical' else 'EPA documented issuance; the current register does not independently certify continued effectiveness.'
    return perm('ND:EPA:R8:Part49',bucket,why,when,stable_no=dt['source_facility_id'])
if __name__=='__main__':main()
