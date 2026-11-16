"""Replay state construction water rules against independent official source archives; network only for --refresh."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, concurrent.futures, csv, json, re, shutil
from collections import Counter
from html import unescape
from pathlib import Path
from urllib.request import Request,urlopen
import lib.discovery as c
R=c.R; D=R/'data'; BASE=R/'cache/state-construction'; SOURCES=BASE/'sources'; INDEX=BASE/'source_index.json'; CAND=D/'state_construction_candidates.json'; REVIEW=D/'state_construction_review.tsv'; RULES=D/'state_construction_rules.json'; COVER=D/'state_construction_coverage.json'
EXIST={'VA':'va-va-construction-gp','TX':'tx-construction-runoff','AZ':'az-stormwater','OH':'oh-stormwater','IA':'ia-dnr-storm'}
EPA={'AS','DC','GU','MA','MP','NH','NM','PR'}
def fetch(url):
    key=c.address(url)
    try:
        c.policy(key)
        with urlopen(Request(key,headers={'User-Agent':c.AGENT}),timeout=24) as resp:
            b=resp.read(c.LIMIT+1);mime=resp.headers.get_content_type();final=resp.url
        if len(b)>c.LIMIT:raise ValueError('source exceeds size limit')
        kind,s,links=c.parse(b,mime,final);h=c.digest(b)
        SOURCES.mkdir(exist_ok=True,parents=True);(SOURCES/(h+'.bin')).write_bytes(b);(SOURCES/(h+'.txt')).write_text(s);c.dump(SOURCES/(h+'.links.json'),links)
        return key,dict(url=key,resolved=final,fetched_at=c.now(),sha256=h,text_sha256=c.digest(s.encode()),bytes=len(b),adapter=kind)
    except Exception as e:return key,dict(url=key,attempted_at=c.now(),error=f'{type(e).__name__}: {e}')
def refresh(cs,states):
    # Serialize per host, including robots and crawl delay, while fetching distinct hosts concurrently.
    from urllib.parse import urlsplit
    by={}
    for st,urls in cs.items():
        if states and st not in states:continue
        for u in urls:
            group=by.setdefault(urlsplit(u).hostname,[])
            if u not in group:group.append(u)
    ix=c.read(INDEX,{})
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for group in pool.map(lambda group:[fetch(u) for u in group],by.values()):
            for key,x in group:
                if x.get('error') and ix.get(key,{}).get('sha256'):ix[key]['last_failed_refresh']=x
                else:ix[key]=x
    c.dump(INDEX,ix)
def verified(u,ix):
    x=ix[c.address(u)];h=x['sha256'];s=(SOURCES/(h+'.txt')).read_bytes()
    assert c.digest((SOURCES/(h+'.bin')).read_bytes())==h and c.digest(s)==x['text_sha256'],u
    return s.decode()
def snippets(cs,ix):
    for st,urls in cs.items():
        if st=='EPA':continue
        for u in urls:
            x=ix.get(c.address(u),{});print(st,u)
            if not x.get('sha256'):print(' ERROR',x.get('error'));continue
            t=' '.join(verified(u,ix).split());ms=list(re.finditer(r'\b(?:acres?|common plan|square feet)\b',t,re.I))
            if not ms:print(' NO TRIGGER IN TEXT')
            end=0
            for m in ms[:13]:
                if m.start()<end:continue
                end=m.end()+190;print(' ',t[max(0,m.start()-110):end])
def stage(ix,urls):
    # No write to shared source_index.json. Only new hash-named objects; any existing object must match.
    selected={c.address(u):ix[c.address(u)] for u in urls}
    for u,x in selected.items():
        verified(u,ix)
        for ext in ['.bin','.txt','.links.json']:
            src=SOURCES/(x['sha256']+ext);dest=c.CACHE/src.name
            if dest.exists():
                if dest.read_bytes()!=src.read_bytes():raise ValueError(f'content collision: {dest}')
            else:shutil.copyfile(src,dest)
    c.dump(BASE/'reviewed_index.json',selected)
def main():
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--state',action='append');p.add_argument('--snippets',action='store_true');p.add_argument('--stage-cache',action='store_true');a=p.parse_args();cs=c.read(CAND,{})
    if a.refresh:refresh(cs,set(a.state or []))
    ix=c.read(INDEX,{})
    if a.snippets:snippets({k:v for k,v in cs.items() if not a.state or k in a.state},ix);return
    if REVIEW.exists():build(cs,ix,a.stage_cache)

def build(cs,ix,staging):
    from urllib.parse import urlsplit
    import hashlib
    pri=list(csv.DictReader((D/'national/priority.csv').open()));g={r['state']:r for r in pri};manual=list(csv.DictReader(REVIEW.open(),delimiter='\t'))
    assert len(set(x['state'] for x in manual))==len(manual)
    directory,contact,appendix=cs['EPA'];epa=verified(appendix,ix);contacts=verified(contact,ix);verified(directory,ix)
    contactraw=(SOURCES/(ix[c.address(contact)]['sha256']+'.bin')).read_text(errors='replace')
    ceiling={'NY':[(5000,'square feet','disturbance within NYC East of Hudson watershed'),(20000,'square feet','disturbance inside NYC boundaries'),(5000,'square feet','impervious area created inside NYC')],
      'CT':[(5,'acre','locally approvable private large construction; state registration')], 'MI':[(5,'acre','notice of coverage for sites at or above five acres')],
      'LA':[(5,'acre','large construction including phases of a qualifying plan; notice of intent')],
      'WY':[(5,'acre','large construction category')],'MS':[(5,'acre','large construction category')]}
    rules=[];cand={}
    for r in manual:
        st=r['state'];assert st in g and st not in EXIST and st not in EPA
        u=cs[st][int(r['source_index'])];s=verified(u,ix);anchor=r['evidence'];norm=c.norm
        assert norm(anchor) in norm(s) and len(anchor.split())<=19,(st,anchor)
        x=ix[c.address(u)];locator=r['locator']
        if x['adapter']=='pdf':
            pages=re.split(r'\[Page (\d+)\]\n',s)
            pg=next((p for p,t in zip(pages[1::2],pages[2::2]) if norm(anchor) in norm(t)),None)
            assert pg,(st,anchor);locator+='; PDF p. '+pg
        stored=dict(id=st.lower()+'-state-construction-water-screen',state=st,jurisdiction=g[st]['name'],geoid=g[st]['geoid'],level='state',topic='construction_stormwater',scope='general',status='adopted' if st in {'GA','MN','AR','NE','RI','ME','CO','KS'} else 'agency_guidance',summary=r['summary'],locator=locator,url=u,authority=r['authority'],evidence=anchor,trigger='See the disturbance, discharge, location and common-plan qualifications in the summary and cited source.',common_plan_review=r['common_plan'])
        stored['thresholds']=[dict(metric='disturbed_area',operator='>=',value=1,unit='acre',context='Base screening threshold for the instrument or category described in the summary; below-threshold sites can still qualify.')]
        if st in ('KS','CO','VI'):
            stored['screen_kind']={'KS':'filing_decision_deadline','CO':'statutory_point_source_discharge','VI':'territorial_application_requirements'}[st]
            stored['thresholds']=[dict(metric='agency_decision_deadline',operator='<=',value=45,unit='day',context='After the complete filing; not a permit by lapse of time.')] if st=='KS' else []
            stored['trigger']={'CO':'Point-source pollutant discharge into Colorado state waters. Construction CGP acreage remains unresolved.','KS':'Submission of the complete filing and required supporting documents. Construction CGP acreage remains unresolved.','VI':'Application for a qualifying VIGSA0000 project. The controlling acreage boundary and common-plan terms remain unresolved.'}[st]
        for v,unit,ctx in ceiling.get(st,[]):stored['thresholds'].append(dict(metric='impervious_area_created' if 'impervious' in ctx else 'disturbed_area',operator='>=',value=v,unit=unit,context=ctx))
        rules.append(stored);cand[st]=stored
    covered=[];notes={'KS':'KDHE and the KDOT copy returned an unsuccessful robots preflight; no primary text archived for a positive statewide claim.','CO':'CDPHE/fact-sheet host did not pass public robots preflight; the separately accessible CDOT portal did not establish a numeric threshold.','VI':'The current DPNR summary describes property in excess of one acre; the 2023 fact sheet includes equality and common plans while the current portal links a 2012 instrument. Exact controlling version not resolved; no numeric provision published.'}
    for a in pri:
        st=a['state'];pub=cand.get(st);office=contact+'#'+st.lower() if re.search('id=["\x27]'+st.lower()+'["\x27]',contactraw,re.I) else contact
        row=dict(state=st,jurisdiction=a['name'],directory_priority=a['count_rank'] or None,office=office,epa_coverage_authority=appendix)
        if pub:row.update(disposition='reviewed_narrower_provision' if pub.get('screen_kind') else 'reviewed_state_rule',rule_id=pub['id'],url=pub['url'],common_plan=pub['common_plan_review'])
        if pub and pub.get('screen_kind'):row.update(scope_limit=notes[st],candidate_sources=cs[st])
        elif pub:pass
        elif st in EXIST:row.update(disposition='existing_state_record',rule_id=EXIST[st],note='Existing atlas authoring record, not counted twice. Its publication status is determined by the shared audit.')
        elif st in EPA:
            eid=st+'R100000';assert eid in epa,(st,eid)
            row.update(disposition='epa_primary_cgp',epa_permit_number=eid,note='Use the federal CGP Appendix B and area-specific conditions; separate state, territorial and local approvals can still apply.')
        else:row.update(disposition='held_state_source',note=notes[st],candidate_sources=cs.get(st,[]))
        covered.append(row)
    assert len(covered)==56 and len({x['id'] for x in rules})==len(rules)
    c.dump(RULES,sorted(rules,key=lambda r:r['state']));c.dump(COVER,covered)
    sel={c.address(z['url']):ix[c.address(z['url'])] for z in rules}
    c.dump(BASE/'reviewed_index.json',sel)
    if staging:stage(ix,[r['url'] for r in rules])
    print(json.dumps(dict(rules=len(rules),coverage=dict(Counter(r['disposition'] for r in covered)),sha256=c.digest(RULES.read_bytes())),sort_keys=True))
if __name__=='__main__':main()
