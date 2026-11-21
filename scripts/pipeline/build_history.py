"""Validate and export separate permit histories through a common interchange schema."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, csv, io, json, re
from datetime import date
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
import lib.discovery as c
import lib.geo_labels as geo_labels
from pipeline.permit_status import permit_metrics
from pipeline import dc_link
from pipeline.compass_taxonomy import classify_history
from pipeline.card_identity import history_identity, dataset_table, office_table, agency_table, find_office
with (c.R/'data/history/series.csv').open() as f:
    SERIES_STATES={r['series']:r['state'] for r in csv.DictReader(f)}
PARTS=list(SERIES_STATES)
CUTOFF=date(2026,11,15)
def locality(v):
    s=str(v or '').strip()
    if not s:return 'Unspecified'
    s=re.sub(r',?\s+VA\.?$','',s,flags=re.I)
    s=re.sub(r'\s+Co\.?$',' County',s,flags=re.I)
    if s.lower().startswith('city of '):s=s[8:]+' City'
    if re.fullmatch(r'Loudoun(?:\s+(?:County|Co\.?))?',s,re.I):return 'Loudoun County'
    return s
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parts',nargs='+',default=PARTS,choices=PARTS);a=ap.parse_args()
    with (c.R/'data/national/jurisdictions.csv').open() as f:
        county_names={(x['state'],x['name'].casefold()):x['name'] for x in csv.DictReader(f) if x['layer']=='counties'}
    keep=geo_labels.exceptions()
    full=[];seen=set()
    federal=c.read(c.R/'data/national/federal_links.json',{})
    inherited={'FERC preliminary permit applications':'Federal Energy Regulatory Commission','USACE Vicksburg District regulatory notices':'US Army Corps of Engineers'}
    for part in a.parts:
        f=series_path(part);rows=json.loads(f.read_text())
        if not isinstance(rows,list) or not rows:raise ValueError('Empty or invalid history: '+part)
        for r in rows:
            for k in ['id','dataset','jurisdiction','record_no','project','kind','status','date','date_role','url','locator']:
                if k not in r:raise ValueError(f'{part}: missing {k}')
            if r['id'] in seen:raise ValueError('Duplicate ID: '+r['id'])
            seen.add(r['id'])
            # The dedicated structure inventory has GIS IDs, but no permit numbers.
            if part=='building' and r['kind']=='Data-center structure observation':continue
            if r['date'] and date.fromisoformat(r['date'])>CUTOFF:raise ValueError('Future observation: '+r['id'])
            if urlsplit(r['url']).scheme not in ('http','https'):raise ValueError('Non-public source: '+r['id'])
            state=r.get('state','VA')
            if state!=SERIES_STATES[part]:raise ValueError('Invalid state: '+r['id'])
            loc=locality(r['jurisdiction'])
            detail=r['details'] if isinstance(r.get('details'),dict) else {}; raw_county=str(r.get('county') or detail.get('county') or '').strip()
            county=loc if re.fullmatch(r".+ County",loc,re.I) else loc if loc.endswith(' Parish') else ''
            if raw_county and raw_county.lower() not in {'unknown','n/a','multiple','unspecified'} and all(ch.isalpha() or ch in " .'-" for ch in raw_county):
                suffix='Parish' if state=='LA' else 'County'
                county=county_names.get((state,raw_county.casefold())) or (re.sub(r' (County|Parish)$','',raw_county,flags=re.I).strip()+' '+suffix)
            if state=='PR' and detail.get('municipio'):
                county=county_names.get((state,detail['municipio'].casefold().strip()+' municipio'),county)
            county=county_names.get((state,county.casefold()),county)
            preview=''
            for field in ('evidence_excerpt','work_description','scope','description'):
                value=detail.get(field)
                if isinstance(value,str) and value.strip():
                    text=' '.join(value.split())
                    if text.casefold() not in str(r.get('project') or '').casefold():
                        preview=(text[:135].rsplit(' ',1)[0]+'…') if len(text)>135 else text
                    break
            issuer=detail.get('federal_issuer') or federal.get(r['id'],{}).get('issuer') or inherited.get(r['dataset']) or ''
            issuer={'US Environmental Protection Agency':'U.S. Environmental Protection Agency','US Army Corps of Engineers - Regulatory':'US Army Corps of Engineers','U.S. Army Corps of Engineers':'US Army Corps of Engineers','Fish and Wildlife Service':'U.S. Fish and Wildlife Service'}.get(issuer,issuer)
            if r['id'] in federal:detail={**detail,'federal_source_match':federal[r['id']]}
            out=dict(r,details=detail,federal_issuer=issuer,category=classify_history(r['kind'],series=part,dataset=r['dataset'],program=detail.get('program','')),locality=loc,county=county,series=part,state=state,preview=preview);out['source_sha256']=r.get('source_sha256') or detail.get('source_sha256') or detail.get('sha256');full.append(out)
    annotated=permit_metrics(full,as_of=CUTOFF.isoformat())
    for row in full:row.update(annotated[row['id']])
    table,offices,agencies=dataset_table(),office_table(),agency_table()
    with (c.R/'data/card_identity_state_agencies.tsv').open() as f:agency_citations={r['state']:r['citation'] for r in csv.DictReader(f,delimiter='\t') if not r['alias']}
    for row in full:
        t,tb,iss,role,ib=history_identity(row,row['details'],table,{},offices,agencies)
        office=find_office(offices,row) if ib=='office_table' else None
        evidence=office['citation'] if office else agency_citations.get(row['state'],row['url']) if ib=='state_agency_table' else (table.get(row['dataset'],{}).get('citation') or row['url']) if ib=='dataset_table' else row['url']
        row.update(issuer_evidence=evidence,issuer_verification='inferred' if office and office['evidence']=='inferred' else 'source_attributed',title=t,title_basis=tb,issuer=iss,issuer_role=role,issuer_basis=ib)
        basis,why=dc_link.link(row);row.update(dc_link_basis=basis,dc_link=why,review_class=dc_link.review_class(row,basis))
    from pipeline.case_timelines import attach
    c.dump(c.OUT/'case_timelines.json',attach(full))
    full.sort(key=lambda r:((r['date'] or (r.get('month') or '')),r['id']),reverse=True)
    # GIS changes row identifiers; retain full source-specific provenance in source exports.
    cols='id state series dataset category locality county jurisdiction record_no title title_basis issuer issuer_role issuer_basis issuer_evidence issuer_verification project kind status date date_role month url source_url source_sha256 locator federal_issuer permit_key permit_bucket permit_representative permit_reason case_group review_class dc_link_basis dc_link details'.split()
    with (c.OUT/'permit_history.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,cols,extrasaction='ignore');w.writeheader()
        for r in full:
            def cell(x):
                s=json.dumps(x,ensure_ascii=False,separators=(',',':')) if isinstance(x,(dict,list)) else str(x) if x is not None else ''
                return "'"+s if s.startswith(('=','+','-','@','\t','\r')) else s
            w.writerow({k:cell(r.get(k)) for k in cols})
    federal_rows=[r for r in full if r['federal_issuer']]
    with (c.OUT/'federal_history.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,cols,extrasaction='ignore');w.writeheader()
        for r in federal_rows:w.writerow({k:cell(r.get(k)) for k in cols})
    c.dump(c.OUT/'federal_summary.json',dict(events=len(federal_rows),states=Counter(r['state'] for r in federal_rows),agencies=Counter(r['federal_issuer'] for r in federal_rows),distinct_permits=Counter(r['permit_bucket'] for r in federal_rows if r['permit_representative']),cutoff=CUTOFF.isoformat()))
    keys='id state category dataset locality county record_no title title_basis issuer issuer_role issuer_basis issuer_evidence issuer_verification project kind status date date_role url month locator preview permit_bucket permit_representative permit_reason federal_issuer case_group review_class'.split()
    viewer=c.R/'viewer';index={};viewer_bytes=0
    detail_bytes=0;map_counts={};federal_counts={}
    for state in sorted({r['state'] for r in full}):
        items=[r for r in full if r['state']==state]
        counts=Counter(g for r in items for g in {r['locality'],r['county']} if g);index[state]=dict(sorted(counts.items()))
        counts_by_area={};fc={}
        if any(r['federal_issuer'] for r in items):federal_counts[state]=fc
        for r in items:
            if not r['permit_representative'] or not r['permit_key']:continue
            names={geo_labels.key(g,state,keep) for g in [r['locality'],r['county']] if g}
            for place in names|{'*'}:
                ct=counts_by_area.setdefault(place,Counter());ct[r['permit_bucket']]+=1
                if r['federal_issuer']:fc.setdefault(place,Counter())[r['permit_bucket']]+=1
        map_counts[state]=counts_by_area
        payload=[[(int(r['review_class']=='land_use') if k=='review_class' else r.get(k)) for k in keys] for r in items]
        file=viewer/('history-'+state+'.js')
        file.write_text('window.PERMIT_CHUNKS['+json.dumps(state)+']='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n')
        viewer_bytes+=file.stat().st_size
        # Defer verbose register fields until a reader opens a permit card.
        detail_file=viewer/('history-'+state+'-details.js')
        detail_file.write_text('window.PERMIT_DETAILS['+json.dumps(state)+']='+json.dumps({r['id']:{**(r.get('details') or {}),**({'dc_link':code} if (code:=dc_link.encode(r,r['dc_link_basis'],r['dc_link'])) else {})} for r in items if r.get('details') or dc_link.encode(r,r['dc_link_basis'],r['dc_link'])},ensure_ascii=False,separators=(',',':'))+';\n')
        detail_bytes+=detail_file.stat().st_size
    (viewer/'history-index.js').write_text('window.HISTORY_INDEX='+json.dumps({'keys':keys,'areas':index,'metrics':map_counts,'federalMetrics':federal_counts,'nameExceptions':keep,'totals':dict(Counter(r['state'] for r in full)),'datasetLinks':dict(sorted(dc_link.DATASETS.items()))},ensure_ascii=False,separators=(',',':'))+';window.PERMIT_CHUNKS={};window.PERMIT_DETAILS={};\n')
    checks={}
    for part in a.parts:
        rr=[r for r in full if r['series']==part];dd=sorted(r['date'] for r in rr if r['date'])
        checks[part]=dict(rows=len(rr),datasets=Counter(r['dataset'] for r in rr),dated=len(dd),earliest=dd[0] if dd else None,latest=dd[-1] if dd else None)
    csv_bytes=(c.OUT/'permit_history.csv').stat().st_size
    viewer_bytes+=(viewer/'history-index.js').stat().st_size
    storage=dict(csv_bytes=csv_bytes,viewer_bytes=viewer_bytes,detail_bytes=detail_bytes,archive_bytes=sum(p.stat().st_size for p in (c.R/'cache/history').rglob('*') if p.is_file()),at_100000_similar_rows_MB={'csv':round(csv_bytes/len(full)*.1,1),'viewer':round(viewer_bytes/len(full)*.1,1)})
    c.dump(c.OUT/'permit_history_summary.json',dict(storage=storage,as_of=CUTOFF.isoformat(),rows=len(full),loudoun_rows=sum(r['locality']=='Loudoun County' for r in full),states=dict(Counter(r['state'] for r in full)),permit_status_counts={s:v.get('*',{}) for s,v in map_counts.items()},sources=checks,unit='Agency records and dated events, not unique projects or approvals. A case can appear in more than one source.'))
    print('Exported',len(full),'history records.')
if __name__=='__main__':main()
