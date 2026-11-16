"""Reconcile reviewed claims, byte snapshots and geographies; build offline viewer assets."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, hashlib, json, re, sys
from collections import Counter,defaultdict
from pathlib import Path
import lib.discovery as c
from pipeline.geography import STATES as PILOT
STATES=PILOT+[r['state'] for r in csv.DictReader((c.R/'data/national/priority.csv').open()) if r['state'] not in PILOT]
from pipeline.compass_taxonomy import classify_rule
R=c.R
LEVELS={'state','county','city','town','municipality','township','regional','federal','village','parish','borough','tribal'}
REQ='id state jurisdiction level topic scope summary status locator url authority evidence'.split()
def table(p,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def cat(r):
    return classify_rule(r['topic'])

def bind(r,geo):
    if r.get('geoid'):
        g=geo.get(str(r['geoid']))
        if not g or g['state']!=r['state']:return None
        return g
    if r['level'] in ('regional','federal','tribal'):return None
    n=c.norm(r['jurisdiction'])
    if r['level']=='state':return next((g for g in geo.values() if g['layer']=='state' and g['state']==r['state']),None)
    n=re.sub(r'^(?:city|town|village|county|township) of ','',n)
    for layer in (['counties'] if r['level'] in ('county','parish') else ['place','cousubs','counties']):
        hits=[g for g in geo.values() if g['layer']==layer and g['state']==r['state'] and (c.norm(g['name'])==n or re.sub(r' (?:city|town|village|township)$','',c.norm(g['name']))==n)]
        if len(hits)==1:return hits[0]
    return None
def audit(r,index,baseline,seal):
    src=index.get(c.address(r['url']),{});h=src.get('sha256');why=''
    if not h:why='retrieval_unavailable'
    else:
        p=c.CACHE/(h+'.bin');t=c.CACHE/(h+'.txt')
        if not p.exists() or c.digest(p.read_bytes())!=h or not t.exists() or c.digest(t.read_bytes())!=src.get('text_sha256'):why='snapshot_integrity_failure'
        elif src.get('adapter')=='scan_needs_review':why='scan_needs_review'
        elif c.norm(r['evidence']) not in c.norm(t.read_text()):why='passage_not_matched'
    visual=None
    if why in ('scan_needs_review','passage_not_matched') and src.get('adapter') in ('pdf','scan_needs_review'):
        v={**c.read(R/'data/visual_reviews.json',{}),**c.read(R/'data/extra_visual_reviews.json',{}),**c.read(R/'data/va_visual_reviews.json',{}),**c.read(R/'data/national/visual_reviews.json',{}),**c.read(R/'cache/national_rules_terra/visual_reviews.json',{}),**c.read(R/'data/national/codebook_ocr_visual_reviews.json',{})}.get(r['id'],{})
        if v.get('url')==r['url'] and v.get('sha256')==h and v.get('page',0)>0 and v.get('reviewer') and v.get('method'):
            from pypdf import PdfReader
            if v['page']<=len(PdfReader(p).pages):
                visual=v;why=''
    sig=c.digest(json.dumps(r,sort_keys=True,ensure_ascii=False).encode())
    pin={'sha256':h,'record_sha256':sig}
    if visual:pin['visual_review_sha256']=c.digest(json.dumps(visual,sort_keys=True).encode())
    if not why:
        if r['id'] not in baseline and seal:baseline[r['id']]=pin
        if baseline.get(r['id'])!=pin:why='changed_since_review' if r['id'] in baseline else 'unsealed'
    return dict(check=why or ('visual_source_check' if visual else 'snapshot_match'),sha256=h,visual_review=visual,fetched_at=src.get('fetched_at'),adapter=src.get('adapter'),fetch_error=src.get('error'))
def main():
    a=argparse.ArgumentParser();a.add_argument('--seal-new',action='store_true',help='Pin newly researched records whose anchors match; never replaces an existing pin.')
    a.add_argument('--strict',action='store_true',help='Fail if any research row is held.');args=a.parse_args()
    for part in ['virginia','expansion','utility']:
        if not (R/f'data/{part}.json').exists():raise SystemExit('Missing '+part+' inputs')
    rows=c.rules();geo={g['geoid']:g for g in csv.DictReader((R/'data/jurisdictions.csv').open())}
    wanted={r['geoid'] for r in rows if r.get('geoid')} - set(geo)
    with (R/'data/national/jurisdictions.csv').open() as f:
        for g in csv.DictReader(f):
            if g['geoid'] in wanted:geo[g['geoid']]={k:g.get(k,'') for k in ('geoid','state','layer','name','lat','lon','domain_candidates')}
    ids=set();out=[];baseline=c.read(R/'data/review_pins.json',{});idx=c.read(c.INDEX,{})
    paths=defaultdict(list)
    for pp in csv.DictReader((R/'data/pathways.csv').open()):
        k=pp.pop('rule_id');paths[k].append(pp)
    if set(paths)-{r['id'] for r in rows}:raise ValueError('Unknown linked pathway '+str(set(paths)-{r['id'] for r in rows}))
    for r in rows:
        if any(not isinstance(r.get(k),str) or not r[k].strip() for k in REQ):raise ValueError('Missing required field: '+str(r))
        if r['id'] in ids or r['state'] not in STATES or r['level'] not in LEVELS:raise ValueError('Invalid or duplicate: '+r['id'])
        allowed={'adopted':'adopted','guidance':'agency_guidance','agency_guidance':'agency_guidance','issued_permit':'issued_permit','official_adoption_summary':'official_adoption_summary'}
        if r['status'] not in allowed:raise ValueError('Unrecognized document status: '+r['id'])
        for t in r.get('thresholds',[]):
            if not isinstance(t.get('value'),(int,float)) or not all(t.get(k) for k in ('metric','operator','unit','context')):raise ValueError('Invalid measure: '+r['id'])
        ids.add(r['id']);check=audit(r,idx,baseline,args.seal_new);g=bind(r,geo)
        if r.get('geoid') and not g:raise ValueError('Bad GEOID: '+r['id'])
        if r.get('effective') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',r['effective']):raise ValueError('Bad effective date: '+r['id'])
        out.append(dict(r,**check,category=cat(r),document_status=allowed[r['status']],scope_class={'data center specific':'data_center_specific','high energy facility':'high_energy_facility','general':'general','general infrastructure':'general','generally applicable':'general'}[r['scope'].replace('-',' ')],pathways=paths.get(r['id'],[]),map_geoid=g['geoid'] if g else None))
    if args.seal_new:c.dump(R/'data/review_pins.json',baseline)
    with (R/'data/card_copy.tsv').open() as f:
        copy={r['id']:r for r in csv.DictReader(f,delimiter='\t')}
    if set(copy)-ids:raise ValueError('Card refers to missing ordinance: '+str(set(copy)-ids))
    for r in out:
        if r['id'] in copy:r['reader_title']=copy[r['id']]['title'];r['reader_brief']=copy[r['id']]['brief'] or ''
    out.sort(key=lambda r:(STATES.index(r['state']),r['jurisdiction']!='Loudoun County',r['jurisdiction'],r['topic'],r['id']))
    c.dump(c.OUT/'rules.json',out);table(c.OUT/'rules.csv',out)
    published=[r for r in out if r['check'] in ('snapshot_match','visual_source_check')]
    held=[r for r in out if r['check'] not in ('snapshot_match','visual_source_check')]
    table(c.OUT/'published.csv',published);table(c.OUT/'holds.csv',held)
    hist=c.read(c.OUT/'virginia_screen.json',{}).get('results',[])
    coverage=defaultdict(list)
    for r in out:
        if r['map_geoid']:coverage[r['map_geoid']].append(r)
    sweep={i:r for r in hist for i in r['geoids']}
    searches=c.read(c.OUT/'local_screen.json',{}).get('rows',{})
    national_path=c.OUT/'national_jurisdiction_checks.csv'
    national={z['geoid']:z for z in csv.DictReader(national_path.open())} if national_path.exists() else {}
    members=[]
    for g in geo.values():
        rr=coverage[g['geoid']];sw=sweep.get(g['geoid'])
        status=('matched source' if any(r['check'] in ('snapshot_match','visual_source_check') for r in rr) else 'evidence held' if rr else 'screened: candidate only' if sw and any(d['data_center_mentions'] for d in sw['documents']) else 'screened: limited discovery' if sw and sw['documents'] else 'retrieval failed' if sw else 'not yet screened')
        visit=searches.get(g['geoid'],{});pages=visit.get('pages',[]) or (sw or {}).get('documents',[])
        if not rr and visit.get('pages'):
            status='screened: candidate only' if any(x['hits'] for x in visit['pages']) else 'screened: limited discovery'
        elif not rr and not pages and visit.get('result')=='unavailable':status='retrieval failed'
        n=national.get(g['geoid'],{});read_count=len(pages);seed=(pages[-1]['url'] if pages else None) or (sw or {}).get('url') or visit.get('entry')
        if not rr and not pages and n:
            read_count=int(n['pages']);seed=n['url'] or None
            status=('screened: candidate only' if int(n['mentions']) else 'screened: limited discovery') if read_count else {'Website unavailable':'retrieval failed','No municipal source joined':'no local website identified','Territorial office only':'territorial office only','Statistical geography; no government assumed':'statistical geography'}.get(n['result'],status)
        members.append(dict(g,coverage=status,records=len(rr),seed=seed,leads=len((sw or {}).get('leads',[])),pages_read=read_count))
    table(c.OUT/'coverage.csv',members)
    payload={'rules':out,'geo':[[g[k] for k in ['geoid','state','layer','name','lat','lon','coverage','records','seed','leads','pages_read']] for g in members],
             'ranks':list(csv.DictReader((R/'data/state_priority.csv').open())), 'stats':dict(Counter(r['check'] for r in out)),'date':'2026-11-15'}
    (R/'viewer/data.js').write_text('window.ATLAS='+json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
    report={'rules':len(out),'default_visible_count':len(published),'held_count':len(held),'visible_by_state':dict(Counter(r['state'] for r in published)),'distinct_urls':len(set(r['url'] for r in out)), 'checks':payload['stats'],'locations':len({(r['state'],r['level'],r['jurisdiction']) for r in out}),'states':dict(Counter(r['state'] for r in out)),'coverage_frame':dict(Counter(g['coverage'] for g in members)),'unmapped':[r['id'] for r in out if not r['map_geoid']]}
    c.dump(c.OUT/'validation.json',report);print(json.dumps(report,indent=2))
    if args.strict and any(r['check'] not in ('snapshot_match','visual_source_check') for r in out):sys.exit(1)
if __name__=='__main__':main()
