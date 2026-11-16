import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
#!/usr/bin/env python3
"""Check the atlas against the COMPASS release pattern; never infer project legality."""
import argparse
import csv
import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit
from pipeline.permit_status import permit_metrics
from pipeline.compass_taxonomy import UNMAPPED, classify_history, classify_rule, classify_stage

ROOT=Path(__file__).resolve().parents[2]
SCOPES={'VA':'51','OH':'39','TX':'48','AZ':'04','IN':'18','TN':'47','NV':'32','MS':'28','LA':'22','NM':'35'}
with (ROOT/'data/national/priority.csv').open() as _f:
    SCOPES.update({x['state']:x['geoid'] for x in csv.DictReader(_f)})
ACCEPTED={'snapshot_match','visual_source_check'}
STATE_HOSTS={'virginia.gov':'VA','ohio.gov':'OH','texas.gov':'TX','az.gov':'AZ','azleg.gov':'AZ','in.gov':'IN','tn.gov':'TN','nv.gov':'NV','ms.gov':'MS','la.gov':'LA','nm.gov':'NM'}
VA_SERIES={'air','water','loudoun','building','pwc','cases'}
def read(p):return json.loads(p.read_text())
def csvrows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def origin(url):
    host=(urlsplit(url or '').hostname or '').lower()
    return next((s for dom,s in STATE_HOSTS.items() if host==dom or host.endswith('.'+dom)),None)
def history_state(r, imposed=None):
    explicit=(r.get('state') or '').upper()
    ending=re.search(r'(?:,|\s)\s*(VA|OH|TX|AZ|IN|TN|NV|MS|LA|NM)\s*$',r.get('jurisdiction') or '',re.I)
    # A municipal dataset can have no state column; use its documented feed,
    # never the word "county" or a project/operator name as an identifier.
    series=(r.get('series') or '').lower()
    registered='VA' if series in VA_SERIES else None
    prefix=re.match(r'^(va|oh|tx|az|in|tn|nv|ms|la|nm)[_-]',str(r.get('id') or ''),re.I)
    states={s for s in [explicit,imposed,ending[1].upper() if ending else None,registered,prefix[1].upper() if prefix else None] if s}
    return next(iter(states)) if len(states)==1 else None
def rule_errors(r,geos):
    errors=[];st=r['state']
    if classify_rule(r['topic'])==UNMAPPED:errors.append('unmapped rule topic')
    if origin(r['url']) not in {None,st}: errors.append('different state government source')
    if r['level']=='state' and str(r.get('map_geoid') or '')!=SCOPES[st]:errors.append('wrong state geometry')
    for name in ('geoid','map_geoid'):
        g=str(r.get(name) or '')
        if g and (geos.get(g)!=st or not g.startswith(SCOPES[st])):errors.append('GEOID does not belong to state')
    if r['level'] in ['regional','tribal','federal'] and r.get('map_geoid') and not r.get('geoid'):
        errors.append('service authority imputed to ordinary geography')
    if r.get('check') in ACCEPTED:
        if any(not r.get(k) for k in ['authority','url','locator','evidence','scope_class','document_status']):errors.append('published provenance incomplete')
        if not re.fullmatch(r'[0-9a-f]{64}',r.get('sha256') or ''):errors.append('published source hash invalid')
    for p in r.get('pathways',[]):
        if not all(p.get(k) for k in ('path','district_or_area','qualifier')):errors.append('district outcome lacks scope or qualifier')
    for t in r.get('thresholds',[]):
        if not all(t.get(k) for k in ('metric','unit','operator','context')) or not isinstance(t.get('value'),(float,int)):errors.append('incomplete quantitative feature')
    for field in ('adopted','effective','expires'):
        if r.get(field):
            try:dt.date.fromisoformat(r[field])
            except (ValueError,TypeError):errors.append('invalid '+field)
    if r.get('effective') and r.get('expires') and r['effective']>r['expires']:errors.append('effective after expiry')
    return errors
def extraction_errors(r,rule):
    if not rule:return ['extraction linked to unknown rule']
    err=[]
    if (r.get('state'),r.get('source_url'),r.get('sha256'))!=(rule['state'],rule['url'],rule.get('sha256')):err.append('candidate crossed state, source, or snapshot')
    if r.get('status')!='extracted_candidate':err.append('unreviewed candidate presented as definitive')
    if not r.get('condition') or not r.get('unit') or not r.get('metric'):err.append('candidate lost metric, unit or condition')
    return err
def history_event_errors(r):
    ds=(r.get('dataset') or '').lower();kind=(r.get('kind') or '').lower(); role=(r.get('date_role') or '').lower(); status=(r.get('status') or '').lower();issues=[]
    if ds=='tdlr architectural barriers registrations' and ('registr' not in role or 'registr' not in kind):issues.append('TDLR accessibility filing promoted beyond a registration')
    if ds=='fort worth development permits' and role.startswith(('issue','issuance')):issues.append('Fort Worth status/filing date promoted to issuance date')
    if 'permit transparency' in ds and role!='application received':issues.append('VPT application date relabeled as decision/issuance')
    if 'new albany' in ds and ('withdraw' in status or status=='wthd') and role.startswith(('adopt','issu','permit issu','permit adopt')):issues.append('Withdrawn New Albany case promoted to adoption/issuance')
    if r.get('date') and r.get('month') and r['date'][:7]!=r['month']:issues.append('Exact and month-only dates disagree')
    if r.get('month') and not re.fullmatch(r'[0-9]{4}-(0[1-9]|1[012])',r['month']):issues.append('Invalid month precision')
    return issues

def measure(p):return {k:v for k,v in sorted(p.items())}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=ROOT);ap.add_argument('--states',nargs='+',choices=sorted(SCOPES),default=list(SCOPES));ap.add_argument('--extra-history',metavar='STATE=FILE',action='append',default=[],help='Complete replacement source array for one state BEFORE consolidation; superseded combined rows for that state are excluded');ap.add_argument('--output',type=Path);ap.add_argument('--strict-taxonomy',action='store_true',help='Also fail on unrecognized historical kinds')
    a=ap.parse_args();out=a.root/'output';states=set(a.states);errors=[];warnings=[]
    def problem(scope,ident,why):errors.append(dict(source=scope,id=ident,reason=why))
    baseline={r['technology']:r for r in read(a.root/'data/compass_sources.json')['releases'] if r.get('workbook_audit')};audits=read(out/'compass_audit.json')
    if {r['technology'] for r in audits}!=set(baseline):problem('NLR','releases','Technology sets differ; rerun compass_audit')
    for r in audits:
        w=baseline.get(r['technology'],{}).get('workbook_audit',{})
        if (r['rows'],r['sha256'])!=(w.get('data_rows_with_state_and_feature'),w.get('sha256')):problem('NLR',r['technology'],'Workbook count or SHA-256 differs')
        missing_features={'State','Feature','Summary','Value','Units','Section','Source URL'}-set(w.get('all_ordinances_columns',[]))
        if missing_features:problem('NLR',r['technology'],'Missing upstream columns: '+','.join(sorted(missing_features)))
    geography=csvrows(a.root/'data/jurisdictions.csv');geos={g['geoid']:g['state'] for g in geography}
    national=csvrows(a.root/'data/national/jurisdictions.csv');geos.update({g['geoid']:g['state'] for g in national})
    frame=Counter(g['state'] for g in national);governments=Counter(g['state'] for g in csvrows(a.root/'data/national/government_units.csv'));screens=read(out/'national_local_summary.json')
    coverage=csvrows(out/'coverage.csv'); allrules=read(out/'rules.json');rules={r['id']:r for r in allrules}; ids=set()
    pub={r['id'] for r in csvrows(out/'published.csv')};held={r['id'] for r in csvrows(out/'holds.csv')}
    if pub&held or pub|held!=set(rules):problem('rules','partition','Published and held files must partition source rows')
    if len(rules)!=len(allrules):problem('rules','identity','Duplicate rule ID')
    if pub!={k for k,r in rules.items() if r['check'] in ACCEPTED}:problem('rules','publication','Accepted snapshot checks do not match published IDs')
    stateinfo={}
    for s in sorted(states):
        rr=[v for v in allrules if v['state']==s];visible=[v for v in rr if v['id'] in pub];cc=[c for c in coverage if c['state']==s]
        if {i['geoid'] for i in cc}!=({i['geoid'] for i in geography if i['state']==s}|{r['map_geoid'] for r in allrules if r['state']==s and r.get('map_geoid')}):problem('coverage',s,'Frame coverage does not match jurisdiction inventory')
        if len(cc)!=len({i['geoid'] for i in cc}):problem('coverage',s,'Repeated geography')
        activegeo={str(v['map_geoid']) for v in visible if v.get('map_geoid')}
        for g in cc:
            if (g['coverage']=='matched source')!=(g['geoid'] in activegeo):problem('coverage',g['geoid'],'Matched geography must have accepted provision')
        for r in rr:
            for err in rule_errors(r,geos):problem('rule',r['id'],err)
            if r in visible and classify_rule(r['topic'])!=r.get('category'):
                warnings.append(dict(id=r['id'],reason='viewer category differs from crosswalk',suggested=classify_rule(r['topic'])))
        stateinfo[s]=dict(published_rules=len(visible),held_rules=len(rr)-len(visible),jurisdiction_frame=frame[s],government_roster=governments[s],local_search=screens.get(s,{}),pilot_frame=len(cc),coverage_labels=measure(Counter(i['coverage'] for i in cc)),document_types=measure(Counter(v['document_status'] for v in visible)),published_families=measure(Counter(classify_rule(v['topic']) for v in visible)),explicit_district_pathways=sum(len(v.get('pathways',[])) for v in visible),embedded_thresholds=sum(len(v.get('thresholds',[])) for v in visible))
    extracts=read(out/'extracted_values.json')
    for x in extracts:
        if x.get('state') not in states and rules.get(x['rule_id'],{}).get('state') not in states:continue
        for err in extraction_errors(x,rules.get(x['rule_id'])):problem('numeric extraction',x['rule_id'],err)
    spotchecks=[]
    for fixture in read(a.root/'data/compass_validation_cases.json'):
        if fixture['state'] not in states:continue
        r=rules.get(fixture['id'],{}); bad=[]
        for k in ('state','level','url','document_status',*[f for f in ('expires','effective','adopted') if f in fixture]):
            if fixture[k]!=r.get(k):bad.append(k)
        if fixture['id'] not in pub:bad.append('not published in current snapshot; adjudicate changed/held source')
        for k in fixture.get('qualifiers',[]):
            if k.lower() not in (r.get('summary') or '').lower():bad.append('missing qualifying concept: '+k)
        if 'path' in fixture and not any(p.get('path')==fixture['path'] and all(d.lower() in (p.get('district_or_area') or '').lower() for d in fixture['district_signals']) for p in r.get('pathways',[])):bad.append('district-specific outcome')
        for k,available in [('measure',r.get('thresholds',[])),('candidate_measure',[v for v in extracts if v['rule_id']==fixture['id']])]:
            if fixture.get(k) and not any([m.get(f) for f in ('metric','operator','value','unit')]==fixture[k] for m in available):bad.append(k)
        spotchecks.append(dict(rule_id=fixture['id'],state=fixture['state'],source=fixture['url'],locator=fixture['checked_against'],mismatches=bad))
        for reason in bad:problem('curated source fixture',fixture['id'],reason)
    hist=csvrows(out/'permit_history.csv')
    extra=[];overridden=set();missing=defaultdict(Counter);families=defaultdict(Counter);series=defaultdict(Counter)
    for arg in a.extra_history:
        st,eq,path=arg.partition('=')
        if st not in SCOPES or not eq:ap.error('expected STATE=path')
        if st in overridden:ap.error('Only one complete replacement array per state')
        overridden.add(st);extra.extend((st,r) for r in read(Path(path)))
    registered=csvrows(a.root/'data/history/series.csv')
    for st in states-overridden:
        if st=='VA':continue # Virginia's GIS structure observations are intentionally excluded on publication.
        feeds=[x['path'] for x in registered if x['state']==st]
        wanted={r['id']:(r.get('status') or '',r.get('date') or '',r.get('date_role') or '') for feed in feeds for r in read(out/feed)}
        got={r['id']:(r.get('status') or '',r.get('date') or '',r.get('date_role') or '') for r in hist if history_state(r)==st}
        if wanted!=got:problem('history assembly',st,'Combined CSV differs from registered government source arrays')
    tagged=[(None,r) for r in hist if history_state(r) not in overridden]+extra
    unnumbered=Counter(); stages=defaultdict(Counter); observed=defaultdict(list)
    for override,r in tagged:
        rid=r.get('id');resolved=history_state(r,override)
        if not resolved:problem('history',rid,'Ambiguous or missing state provenance; declare state or register the source');continue
        if resolved not in states:continue
        if rid in ids:
            problem('history',rid,'Duplicate history ID');continue
        ids.add(rid); observed[resolved].append(dict(r,state=resolved))
        for err in history_event_errors(r):problem('event semantics',rid,err)
        if rid in rules:problem('history',rid,'Rule/permit identifier collision')
        if origin(r.get('url')) not in {None,resolved}:problem('history',rid,'Primary agency domain belongs to a different state')
        if not all(r.get(k) for k in ['project','kind','status','url','locator','date_role']):problem('history',rid,'Permit history lacks identity, provenance, or date role')
        if not r.get('record_no'):
            unnumbered[resolved]+=1
            if not (r.get('source_sha256') and (r.get('date') or r.get('month'))):problem('history',rid,'Unnumbered event needs pinned citation and at least month precision')
        details=r.get('details') or {}
        if isinstance(details,str):
            try:details=json.loads(details) or {}
            except ValueError:details={}
        if not isinstance(details,dict):details={}
        fam=classify_history(r['kind'],series=r.get('series',''),program=details.get('program') or '',dataset=r.get('dataset',''))
        stages[resolved][classify_stage(r['kind'],r['status'])]+=1;families[resolved][fam]+=1;series[resolved][r.get('dataset') or 'Unspecified']+=1
        if fam==UNMAPPED:missing[resolved][r['kind']]+=1
    for s in sorted(states):
        stateinfo[s].update(history_rows=sum(families[s].values()),unnumbered_cited_events=unnumbered[s],history_families=measure(families[s]),history_stages=measure(stages[s]),history_datasets=measure(series[s]),unmapped_history_kinds=measure(missing[s]))
        annotations=permit_metrics(observed[s],as_of=read(out/'permit_history_summary.json')['as_of'])
        reps=[v for v in annotations.values() if v['permit_representative']]
        keys={v['permit_key'] for v in annotations.values() if v['permit_key']}
        if len(keys)!=len(reps):problem('permit status',s,'Not exactly one representative per permit identity')
        counts=Counter(v['permit_bucket'] for v in reps)
        skipped=Counter(v['permit_event_type'] for v in annotations.values() if v['permit_key'] is None)
        unrecognized=Counter(r['dataset']+' / '+r['status'] for r in observed[s] if annotations[r['id']]['permit_event_type']=='unknown')
        stateinfo[s].update(distinct_identified_permits=len(keys),permit_snapshot_buckets={k:counts[k] for k in ('active','historical','unconfirmed')},excluded_event_types=measure(skipped),unrecognized_permit_semantics=measure(unrecognized))
        for r in observed[s]:
            if 'permit_bucket' in r and r['permit_bucket']!=annotations[r['id']]['permit_bucket']:problem('permit status',r['id'],'Published status bucket differs; rebuild history and map')
        if unrecognized and a.strict_taxonomy:problem('permit status',s,'Unmapped source/status; verify before adding: '+', '.join(sorted(unrecognized)))
        if missing[s] and a.strict_taxonomy:problem('history taxonomy',s,'Unmapped kinds: '+', '.join(sorted(missing[s])))
    result=dict(check='fail' if errors else 'pass',upstream_releases=len(audits),upstream_feature_rows=sum(x['rows'] for x in audits),states=stateinfo,curated_source_checks=spotchecks,errors=errors,warnings=warnings,units='Rule rows, jurisdiction-frame rows and permit events are separate units. Passing checks do not measure legal accuracy or discovery recall.')
    dest=a.output or out/'compass_crosscheck.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(result['check'].upper(),f'{len(errors)} errors, {len(warnings)} viewer-label notices; '+', '.join(f"{s}: {d['published_rules']} provisions / {d['history_rows']} history rows" for s,d in stateinfo.items()))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
