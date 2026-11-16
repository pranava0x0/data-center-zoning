"""Read dated federal review steps already disclosed in USACE project files.
The Corps is the reporting agency. Partners (including state/tribal 401 authorities)
are not reassigned as federal issuers. No consultation is itself counted as a permit.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import csv, collections, re, json
import lib.discovery as c
D=c.R/'data/national';DS='Army Corps consultation history'
LABEL={'esa':'Endangered Species Act consultation','s106Nhpa':'Historic preservation consultation','wqc401':'Section 401 water quality certification review','efh':'Essential fish habitat consultation'}
def classify(r,cutoff,perm,no,app,obs):return no('Dated compliance step in a federal case file. It does not establish issuance of the Corps permit.','decision')
def run():
 regs=list(csv.DictReader((c.R/'data/history/series.csv').open()));cases={};fast=[];ret=collections.defaultdict(list);held=[];links=[]
 for s in regs:
    if s['series'].startswith('fast_'):fast.extend(c.read(series_path(s['series']),[]))
    if not s['series'].startswith('corps_'):continue
    for r in c.read(series_path(s['series']),[]):
        d=r['details'];da=d.get('da_number') or r['record_no']
        for prog,items in (d.get('consultations') or {}).items():
            if prog not in LABEL:raise ValueError('Unreviewed program '+prog)
            for x in items or []:
                sid=x.get('actionId') or x.get('actionLinkId')
                if not sid:held.append([da,prog,'No action identifier']);continue
                # 401 shares parent actionLinkId across certifications; pair it with the notified authority.
                partner=x.get('agency') or x.get('certifyingAuthorityNotified') or x.get('agencyNotified') or ''
                k=(r['state'],da,prog,str(sid),str(partner))
                vals=(x.get('beginDate'),x.get('endDate'),x.get('closureMethod') or x.get('effectsDetermination'))
                if k in cases and cases[k][1]!=vals:raise ValueError('Conflicting consultation records: '+str(k))
                cases[k]=(r,vals,partner)
 for (st,da,prog,sid,_),(r,(start,end,outcome),partner) in sorted(cases.items()):
    if start and end and start>end:held.append([da,prog,'Start later than end']);continue
    for stage,date in [('start',start),('end',end)]:
        if not date or date>'2026-11-15' or (stage=='start' and date==end):continue
        if stage=='end' and not outcome:status='End date recorded; outcome not stated'
        else:status='Review began' if stage=='start' else outcome
        # Regional dashboard project has an explicitly cross-referenced DA number; overlapping
        # program/day milestones stay available in the dashboard instead of becoming duplicate events.
        can=[v['id'] for v in fast if v['date']==date and (v['details'].get('corps_file') or '').upper()==da.upper() and ((prog=='esa' and ('species' in (v['details'].get('program') or '').lower() or 'wildlife' in v['details']['federal_issuer'].lower())) or (prog=='s106Nhpa' and 'historic' in v['kind'].lower()) or (prog=='wqc401' and '401' in v['kind']))]
        if can:links.append([da,prog,date,can]);continue
        key=c.digest(json.dumps([st,da,prog,sid,partner,stage]).encode())[:18]
        det=dict(federal_issuer='US Army Corps of Engineers',reporting_agency='US Army Corps of Engineers',consulted_authority=partner or None,program=prog,case_number=da,source_action_identifier=sid,reported_start=start,reported_end=end,reported_outcome=outcome,parent_atlas_record=r['id'],scope='Review recorded in the district file. Check the partner authority for its own signed decision.')
        ret[st].append(dict(id='fed-consult-'+key,state=st,dataset=DS,record_no=da,jurisdiction=r['jurisdiction'],county=r.get('county') or r['details'].get('census_county') or '',project=r['project'],kind=LABEL[prog],status=status,date=date,date_role='Review start' if stage=='start' else 'Review end',url=r['url'],source_url=r.get('source_url') or r['url'],source_sha256=r.get('source_sha256') or r['details'].get('source_sha256'),locator=da+' · '+prog+' · consultation '+sid,details=det))
 for st,a in ret.items():c.dump(series_path('fcon_'+st.lower()),a)
 c.dump(D/'federal_consultations.json',dict(identified_reviews=len(cases),dated_events=sum(map(len,ret.values())),per_state={st:len(a) for st,a in ret.items()},held=held,dashboard_overlaps=links,unit='Agency-reported review starts/ends. Same-day start and close count once, and no additional permits are inferred.'))
 print(len(cases),'consultation records;',sum(map(len,ret.values())),'dated actions;',len(links),'overlaps.')
if __name__=='__main__':run()
