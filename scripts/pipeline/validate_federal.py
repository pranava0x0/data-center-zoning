"""Check issuer, action type and instrument coverage against source-level evidence, offline."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, collections, json
import lib.discovery as c
from collectors.federal.epa_npdes import CACHE
def read(p):
 with p.open() as f:return list(csv.DictReader(f))
def run():
 allrows=read(c.OUT/'permit_history.csv');fed=read(c.OUT/'federal_history.csv');known={r['id']:r for r in fed};expect={r['id'] for r in allrows if r['federal_issuer']}
 if len(known)!=len(fed) or set(known)!=expect:raise ValueError('Federal subset diverges from full history')
 data=c.read(CACHE,{})
 permits={(q['permit']['EXTERNAL_PERMIT_NMBR'],q['permit']['VERSION_NMBR']):q['permit'] for q in data['rows']}
 if any(r['dataset']=='State-issued water permits reported to EPA' and r['id'] in known for r in allrows):raise ValueError('Federal hosting mistaken for federal issuance')
 links=c.read(c.R/'data/national/federal_links.json',{});reps=set();decisions=set();pending=0
 for r in fed:
    d=json.loads(r['details']);u=r['url'];k=r['permit_key'];name=r['dataset']
    if not u.startswith('https://') or not r['locator']:raise ValueError('Missing public case citation '+r['id'])
    if r['id'] in links or name in ('U.S. EPA water discharge permits','EPA water permit timeline'):
        p=permits[(r['record_no'],str(d['version']))]
        if (p['AGENCY_TYPE_CODE'],p['ISSUING_AGENCY'])!=('EP6','U.S. EPA'):raise ValueError('Cannot establish EPA as issuer')
    if ('orm_view' in d and d['orm_view'] in ('pending','jds','nepa_ea')) or name in ('Army Corps prior permit amendments','Department of Energy land and developer milestones','Interior insular data-center financial assistance','FAA airspace determinations','FERC interconnection decisions','Army Corps consultation history','US Army Corps of Engineers district public notices','USACE Vicksburg District regulatory notices','FERC preliminary permit applications','FAST-41 federal permitting milestones','FAST-41 timetable decisions','Department of Energy NEPA determinations'):
        if k:raise ValueError('Non-permit federal action counted as permit: '+r['id'])
        pending+=1
    if k and r['permit_representative']=='True':
        if k in reps:raise ValueError('Duplicate federal permit representative '+k)
        reps.add(k)
    decisions.add(d.get('shared_decision') or r['id'])
 if len(reps)!=sum(c.read(c.OUT/'federal_summary.json',{})['distinct_permits'].values()):raise ValueError('Federal totals inconsistent')
 if any('townsite' in r['id'] and r['permit_bucket']=='active' for r in fed):raise ValueError('Stayed Townsite permit represented as active')
 report=dict(agency_events=len(fed),distinct_events_after_multistate_crosswalk=len(decisions),distinct_instrument_keys=len(reps),non_authorizing_actions_checked=pending,host_is_not_issuer=True,corps_current_status='No active status assigned without affirmative evidence.',national_first_pass=c.read(c.OUT/'national_scope_check.json',{}).get('local_first_pass_complete'))
 if fed and not report['national_first_pass']:raise ValueError('Federal collection predates reconciled geographic screening')
 c.dump(c.OUT/'federal_quality.json',report);print('Federal identity checks:',report)
if __name__=='__main__':run()
