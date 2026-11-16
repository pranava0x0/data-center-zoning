"""Snapshot permit identities and status. Deliberately separate from historical event stages.

permit_metrics(rows, as_of) returns an annotation for every input event ID. Compute
before geographic filtering; count distinct non-null keys (or representative rows).
Consult docs/permit-status.md before extending a registry.
"""
from lib.status import iso, details
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
from collections import defaultdict
from functools import lru_cache
from importlib import import_module
from importlib.util import find_spec
from datetime import date
import json
import re

ACTIVE='active'; HIST='historical'; UNC='unconfirmed'; OTHER='non_permit'
REFERENCES={
    'Ohio EPA NPDES register':'https://epa.ohio.gov/divisions-and-offices/surface-water/permitting/stormwater-program',
    'VA DEQ — Virginia Water Protection (VWP) General Permits':'https://gisdata.deq.virginia.gov/mapper_ext/DataFactSheets/Water_Permitting/General%20Permits_VWP_DEQFactSheet.pdf',
    'VA DEQ — Virginia Water Protection (VWP) Individual Permits (IP)':'https://gisdata.deq.virginia.gov/mapper_ext/DataFactSheets/Water_Permitting/Individual%20Permits_VWP_DEQFactSheet.pdf',
    'VA DEQ — Stormwater Permits Daily':'https://gisdata.deq.virginia.gov/mapper_ext/DataFactSheets/Water_Permitting/StormwaterPermitsDEQFactSheet.pdf',
    'Loudoun issued permits':'https://logis.loudoun.gov/gis/rest/services/LMARC/LandMARC_Permits/MapServer/1',
    'Indiana DHS Project Activity':'https://www.in.gov/dhs/building-plan-review/building-plan-review-process/',
    'TDLR architectural barriers registrations':'https://www.tdlr.texas.gov/ab/abfaq.htm',
    'Virginia DEQ issued data-center air permits':'https://www.deq.virginia.gov/news-info/shortcuts/permits/air/issued-air-permits-for-data-centers',
}
def norm(x):return ' '.join((str(x or '')).strip().casefold().split())
def no(why,event='other'):
    return dict(permit_bucket=OTHER,permit_key=None,permit_representative=False,permit_reason=why,permit_event_type=event)
STATUS_MODULES={"ak": "collectors.alaska.status", "al": "collectors.alabama.status", "ar": "collectors.arkansas.status", "ca": "collectors.california.status", "co": "collectors.colorado.status", "ct": "collectors.connecticut.status", "dc": "collectors.district_of_columbia.status", "fl": "collectors.florida.status", "ga": "collectors.georgia.status", "hi": "collectors.hawaii.status", "ia": "collectors.iowa.status", "id": "collectors.idaho.status", "ks": "collectors.kansas.status", "ky": "collectors.kentucky.status", "la": "collectors.louisiana.status", "ma": "collectors.massachusetts.status", "md": "collectors.maryland.status", "mi": "collectors.michigan.status", "mn": "collectors.minnesota.status", "ms": "collectors.mississippi.status", "mt": "collectors.montana.status", "nc": "collectors.north_carolina.status", "nd": "collectors.north_dakota.status", "ne": "collectors.nebraska.status", "nj": "collectors.new_jersey.status", "nm": "collectors.new_mexico.status", "nv": "collectors.nevada.status", "ny": "collectors.new_york.status", "ok": "collectors.oklahoma.status", "or": "collectors.oregon.status", "pa": "collectors.pennsylvania.status", "pr": "collectors.puerto_rico.status", "sc": "collectors.south_carolina.status", "sd": "collectors.south_dakota.status", "tn": "collectors.tennessee.status", "ut": "collectors.utah.status", "vt": "collectors.vermont.status", "wa": "collectors.washington.status", "wi": "collectors.wisconsin.status", "wv": "collectors.west_virginia.status", "wy": "collectors.wyoming.status"}
@lru_cache(maxsize=64)
def state_classifier(state):
    if not re.fullmatch(r'[A-Z]{2}',state or ''):return None
    mod=STATUS_MODULES.get(state.lower(),'')
    return import_module(mod).classify if mod and find_spec(mod) is not None else None

def observation(r, cutoff):
    ds=r.get('dataset',''); st=r.get('state',''); s=norm(r.get('status')); k=norm(r.get('kind')); d=details(r); day=iso(r.get('date'))
    if isinstance(r.get('details'),str):r=dict(r,details=d)  # Consolidated CSV serializes regulator fields as JSON.
    num=str(r.get('record_no') or '').strip().upper()
    if r.get('date') and not day:return no('Invalid date; record held for review.','unknown')
    if day and day>cutoff:return no('Event postdates reporting cutoff.','out_of_period')
    def perm(reg,bucket,why,when=None,version=None,stable_no=None):
        if st!=reg.split(':')[0]:return no('Register/state mismatch; verify issuer.','unknown')
        if not num or num in {'N/A','UNKNOWN','NONE'}:return no('Reported permit has no stable source number.','unnumbered')
        if when and when>cutoff:
            bucket,why,when=UNC,'Source status date is later than cutoff.',None
        return dict(permit_bucket=bucket,permit_key=reg+'|'+(stable_no or num),permit_representative=False,permit_reason=why,permit_event_type='permit',_day=when,_version=version)
    def app():return no('Application, draft or pre-issuance workflow.','application')
    def stale():return no('Pending or withdrawn without confirmation of an issued instrument.','application')
    def obs(reg,historical=(),active=(),issued=(),when=None,held=()):
        if s in historical:return perm(reg,HIST,'Register reports '+str(r['status'])+'.',when)
        if s in active:return perm(reg,ACTIVE,'Register explicitly reports '+str(r['status'])+'.',when)
        if s in issued:return perm(reg,UNC,'Issuance documented; continued validity not established.',when)
        if s in held:return perm(reg,UNC,'Permit record present; status does not establish validity.',when)
        return stale() if s in {'pending','submitted','approved','planned','in review','void','withdrawn','draft','denied','incomplete submittal','plan review','awaiting client reply'} else no('Unmapped source status: '+str(r.get('status') or ''),'unknown')
    if ds in ('PortlandMaps all permits','Municipal land-use case records','Oregon land-use ordinance and review records'):return import_module('collectors.oregon.status_portland_west_metro').classify(r,cutoff,perm,no,app,obs)
    if ds=='Fairfax County site plan and land development decisions':return no('The county approved the named site submission. It does not establish issuance of a construction permit.','decision')
    if ds in {'Loudoun fire marshal — data-center property authorizations','Phoenix Fire Department — data-center project and address match','San Francisco Fire Department storage and use permits','US site-specific water permit records','Santa Clara Fire Marshal permit documents','Washington Ecology — industrial-user state discharge permits'}:return import_module('collectors.multistate.water_fire_authorizations').classify(r,cutoff,perm,no,app,obs)
    if ds=='Henrico County monthly issued permits':return import_module('collectors.virginia.henrico_county.permits').classify(r,cutoff,perm,no,app,obs)
    if ds in ('New Albany verified campus zoning actions','Hilliard campus board decisions'):return import_module('collectors.ohio.central_ohio_entitlements').classify(r,cutoff,perm,no,app,obs)
    if ds in ('Cook County assessor municipal permit register','Elk Grove Village redevelopment resolutions'):return import_module('collectors.illinois.elk_grove_village_cook_assessor').classify(r,cutoff,perm,no,app,obs)
    if ds=='City of Manassas development and construction updates':return import_module('collectors.virginia.manassas.development_actions').classify(r,cutoff,perm,no,app,obs)
    if ds=='FAA airspace determinations':return no('Air navigation determination for this structure, not permission to build or operate a data center.','decision')
    if ds=='Municipal project planning dockets':return no('Planning docket action; no independently issued permit established.','decision')
    if ds=='US EPA Region 8 tribal minor NSR final actions':return import_module('collectors.federal.epa_air_cases').classify(r,cutoff,perm,no,app,obs)
    if ds=='Army Corps Digital Library project actions':return import_module('collectors.federal.usace_digital_library').classify(r,cutoff,perm,no,app,obs)
    if ds=='Army Corps prior permit amendments':return no('A modification to the previously issued permit; no additional permit instrument established.','permit_action')
    if ds=='Army Corps consultation history':return import_module('collectors.federal.usace_consultations').classify(r,cutoff,perm,no,app,obs)
    if ds=='Guam interagency land-use referrals':return import_module('collectors.guam.status').classify(r,cutoff,perm,no,app,obs)
    if ds=='EPA water permit timeline':return no('Dated action for the original numbered EPA permit; see its register record for current status.','permit_action')
    for registers,module in [
        (('US Army Corps of Engineers regulatory public actions','US Army Corps of Engineers district public notices'),'collectors.federal.status_usace'),
        (('FAST-41 federal permitting milestones','FAST-41 timetable decisions'),'collectors.federal.fast41_dashboard'),
        (('FERC interconnection decisions',),'collectors.federal.ferc_orders'),
        (('Interior insular data-center financial assistance',),'collectors.territories.status_grants'),
        (('Department of Energy land and developer milestones',),'collectors.federal.doe_nepa'),
        (('Interior Department land decisions','Department of Energy NEPA determinations'),'collectors.federal.decisions')]:
        if ds in registers:return import_module(module).classify(r,cutoff,perm,no,app,obs)
    if ds=='U.S. EPA water discharge permits':
        from collectors.federal.epa_named_water_permits import classify
        return classify(r,cutoff,perm,no,app,obs,federal=True)
    if ds=='State-issued water permits reported to EPA':
        from collectors.federal.epa_named_water_permits import classify
        return classify(r,cutoff,perm,no,app,obs)
    if d.get('feed_id'):
        from collectors.multistate.open_data_release import classify
        answer=classify(r,cutoff,perm,no,app,obs)
        if answer:return answer
    if r.get('dataset') in ('Guam Hybrid Land Use Commission minutes','Palm Beach County Project Tango decisions','Delaware Coastal Zone Act decisions','Lewiston City Council development agreements','Rhode Island DEM emergency generator permits','Susquehanna River Basin Commission consumptive use approvals'):
        from collectors.multistate.status_meeting_votes import classify
        answer=classify(r,cutoff,perm,no,app,obs)
        if answer:return answer
    classifier=state_classifier(st)
    if classifier:
        answer=classifier(r,cutoff,perm,no,app,obs)
        if answer is not None:return answer
    if ds in {'Loudoun submitted permits','Virginia Permit Transparency — environmental applications','Virginia Permit Transparency — DEQ air applications'}:return app()
    if ds in {'Loudoun land-use applications','New Albany zoning entitlements','Municipal planning decisions','Abilene city site-plan register','Columbus engineering filings','City of Hobart Plan Commission minutes'}:return no('Planning application, site-plan or decision event.','decision')
    if ds=='TDLR architectural barriers registrations':return no('Texas architectural-barriers registration, not a permit.','registration')
    if ds in {'VA DEQ — VWP SSWD','VA DEQ — Virginia Water Protection (VWP) Non-Permit (NP)'}:return no('DEQ determination or non-permit activity.','determination')
    if ds=='Virginia DEQ issued data-center air permits':
        if s=='approved':return no('Corroborated application approval, not a permit issuance.','application')
        return no('DEQ site registration + application/action number: no unique instrument key.','permit_action')
    if ds in {'Loudoun issued permits','Loudoun monthly building reports'}:
        reg='VA:loudoun-building'; finals=[iso(x) for x in d.get('final_dates',[])];finals=[x for x in finals if x and x<=cutoff]
        if finals and s=='issued':return perm(reg,HIST,'LandMARC records a finalization date.',max(finals))
        return obs(reg,('finaled',),issued=('issued',),when=day if s=='issued' and 'issue date' in norm(r.get('date_role')) else None)
    if ds=='Prince William data-center building permits':return obs('VA:prince-william-building',('finaled',),issued=('issued',))
    if ds=='County case files':
        if k=='land disturbance' and s=='issued' and not num:return no('County reports issuance, without a deduplicable number.','unnumbered')
        if k in ('commercial electrical','sprinkler system or standpipe system') and 'fairfax county' in norm(r.get('jurisdiction')):return obs('VA:fairfax-building',('closed',),issued=('issued',))
        if s=='received':return app()
        return no('Case-file planning, certification or review decision.','decision')
    if ds=='VA DEQ — Stormwater Permits Daily':
        reg='VA:deq-construction-gp'
        if s in {'md_in_prog','rs_in_prog','t_in_prog','md_submit','rs_submit'}:return app()
        dates=d.get('dates') or {};term=iso(dates.get('SWC_TERM_DATE'));signed=iso(dates.get('SWC_APP_SIGNED_DT'))
        # A signed date can precede the actual agency action; order only on
        # dated affirmative actions relative to a documented termination.
        if s=='per_term':return perm(reg,HIST if term and term<=cutoff else UNC,'CGP termination.' if term and term<=cutoff else 'Termination date not verified.',term if term and term<=cutoff else None)
        if s in {'per_issued','per_reiss','modified','transfer'}:return perm(reg,UNC,'CGP coverage action, not an explicit present active classification.',signed if signed and signed<=cutoff else None)
        return no('Unmapped CGP status.','unknown')
    if ds.startswith('VA DEQ — Virginia Water Protection (VWP) ') and ds.split(') ')[-1] in {'Individual Permits (IP)','General Permits'}:
        reg='VA:deq-vwp-'+('individual' if 'Individual' in ds else 'general')
        if s=='application':return app()
        return obs(reg,('history',),('active',))
    if ds=='Ohio EPA NPDES register':
        reg='OH:epa-construction-npdes'
        if s in {'draft','withdrawn','denied','pending'}:return app()
        match=re.fullmatch(r'([0-4]GC(?:D|O)?[0-9]+)\*([A-Z])G',num)
        if not match:return no('Unexpected Ohio general-coverage identity; inspect numbering.','unknown')
        num,letter=match.groups();variant=ord(letter);eff=iso(d.get('effective_date'));exp=iso(d.get('expiration_date'))
        if s=='active' and ((eff and eff>cutoff) or (exp and exp<cutoff)):return perm(reg,UNC,'Explicit active label conflicts with reported term; verify continuation.',eff,variant)
        if s=='active':return perm(reg,ACTIVE,'Ohio EPA reports ACTIVE coverage.',eff,variant)
        if s in {'expired','revoked','terminated'}:return perm(reg,HIST,'Ohio EPA reports '+s+' coverage.',eff,variant)
        return no('Unmapped Ohio NPDES status.','unknown')
    if ds=='Ohio EPA selected air and water permits':
        if k in ('initial title v air permit','surface water permit to install') and s in ('approval','final title v permit'):return perm('OH:epa-'+('air' if 'air' in k else 'sewer-installation'),UNC,'Issued instrument; current status not confirmed.',day)
        return no('Unrecognized Ohio EPA instrument.','unknown')
    if ds=='Columbus building and trade permits':return obs('OH:columbus-building',('closed','expired permit'),issued=('issued',),when=iso(d.get('last_status_date')))
    if ds=='Austin issued construction permits':return obs('TX:austin-development',('expired','void','withdrawn','final'),('active',),('issued',))
    if ds=='Dallas building permits':return obs('TX:dallas-development',issued=('issued',))
    if ds=='San Antonio issued building and trade permits':return obs('TX:san-antonio-development',issued=('issued',))
    if ds=='Fort Worth development permits':
        return obs('TX:fort-worth-development',('finaled','expired'),issued=('issued',),when=iso(d.get('source_status_date')))
    return extension(r,ds,s,k,d,num,cutoff,perm,obs,app)

def extension(r,ds,s,k,d,num,cutoff,perm,obs,app):
    when=iso(r.get('date')); role=norm(r.get('date_role'))
    if ds in ('Chandler city council zoning decisions','Phoenix plan reviews'):return no('Zoning decision or plan review; not an issued construction permit.','decision')
    if ds in ('Maricopa County air public notices','Pima County dust enforcement'):return no('Public notice or enforcement event, not a permit.','notice')
    if ds=='Maricopa County air permit register':
        if not re.fullmatch(r'P[0-9]+',num) or k not in ('county air permit register / minor','county air permit register / synthetic minor'):return no('Unrecognized county air permit identity or class.','unknown')
        return perm('AZ:maricopa-air',UNC,'County permit-register number. Raw status code is not expanded; facility operating status is separate.')
    if ds in ('ADEQ legacy construction stormwater','ADEQ myDEQ construction stormwater','ADEQ myDEQ industrial stormwater'):
        if 'waiver' in k or norm(d.get('waiver_field'))=='true':return no('Stormwater waiver, not permit coverage.','waiver')
        reg='AZ:adeq-'+('industrial' if 'industrial' in ds else 'construction')+'-stormwater'
        if s=='approval recorded' and role=='approval date':return perm(reg,UNC,'Dated stormwater approval, without current active status.',when)
        if s=='termination/cancellation recorded' and role=='termination/cancellation date' and when:return perm(reg,HIST,'Dated termination or cancellation on the agency register.',when)
    if ds=='Phoenix permits':
        reg='AZ:phoenix-permits';issue=iso(d.get('issue_date'));final=iso(d.get('completion_date'));exp=iso(d.get('expiration_date'))
        if 'service request' in k or 'flow test' in k:return no('Service request or test entered on permit layer.','service')
        if not d.get('permit_type_code') or not num.startswith(str(d['permit_type_code']).strip().upper()+' '):return no('Phoenix compound permit identity not verified.','unknown')
        if not issue or issue>cutoff:return app()
        if s=='open' and exp and exp>=cutoff and not final:return perm(reg,ACTIVE,'Phoenix explicitly reports OPEN: issued, within reported term, no completion date.',issue)
        if s=='open':return perm(reg,UNC,'OPEN is not confirmed: expiration is absent/past or completion exists.')
        return obs(reg,('done','expr'),issued=('issued',),when=final)
    if ds=='Scottsdale permits at a verified data-center site':
        if not iso(r.get('date')) or norm(r.get('date_role'))!='issue date':return no('Holds site-linked row without a verified issue date.','unknown')
        return obs('AZ:scottsdale-development',('finalled','expired'))
    if ds=='Mesa building permit register':
        reg='AZ:mesa-building';final=iso(d.get('finaled_date'));issued='issue date'==role
        if s=='finaled':return perm(reg,HIST,'Mesa reports finaled building permit.',final)
        if s in ('c of c issued','c of o issued','temporary c of o') and not issued:return no('Certificate alone does not identify an issued construction permit.','certificate')
        if issued and s in ('issued','c of c issued','c of o issued','temporary c of o'):
            if final and when and when<=final<=cutoff:return perm(reg,HIST,'Mesa records a completed final inspection after issuance.',final)
            return perm(reg,UNC,'Mesa issued the permit; certificate does not independently establish finality.',when)
        if s in ('fees paid','fees due','in review','approved','revisions required','revisions received'):return app()
    if ds=='Tempe building safety permits':
        if 'revision' in k:return no('Revision without independently linked base instrument.','permit_action')
        final=iso(d.get('completion_date'))
        if s=='issued' and when and final and when<=final<=cutoff:return perm('AZ:tempe-building',HIST,'Tempe records completion after issuance.',final)
        return obs('AZ:tempe-building',('finaled','final','closed'),issued=('issued',),when=iso(d.get('status_date')))
    if ds=='Tucson commercial building permits':
        if s=='fees due':return app()
        if s=='inspections' and role=='issue date':return perm('AZ:tucson-building',UNC,'Issued; inspection status alone does not establish present validity.',when)
        return obs('AZ:tucson-building',('closed','final'),issued=('issued',))
    if ds=='Goodyear Citizen Access':return obs('AZ:goodyear-building',('completed',),issued=('permit issued',),held=('co or final inspection','tco'))
    if ds=='Chandler Citizen Access':return obs('AZ:chandler-development',issued=('issued',))
    if ds=='Indiana DHS Project Activity':
        if k=='construction design release application' or s=='filed':return app()
        if k=='construction design release':return no('State design review release; not a local construction permit.','design_release')
    if ds=='Indiana IDEM Waterways decisions and notices':return no('Nonfinal application deficiency or hearing notice.','notice' if 'notice' in s else 'application')
    if ds=='Indiana IDEM air decisions and notices':
        if s=='draft air permit':return no('Draft document inviting comment; not an issued permit.','notice')
        if s=='approval - effective immediately':
            if k in ('tv new source construction','title v new source construction','fesop new source construction'):
                return perm('IN:idem-air',UNC,'Initial agency permit decision; continued validity not established.',iso(r.get('date')))
            if k=='fesop significant permit revision':
                if num=='089-45165-00639' and r.get('source_sha256')=='128beaed3864fa13b7b19dea1e1dfc30a0e70142452cacf33b0cbe1327ce5ad6':
                    return perm('IN:idem-air',UNC,'Revision expressly identifies underlying F089-42502-00639; not another permit.',iso(r.get('date')),stable_no='089-42502-00639')
                return no('Revision without independently linked underlying permit.','permit_action')
    return no('No vetted issuer/register mapping.','unknown')

def permit_metrics(rows,as_of):
    cutoff=as_of if type(as_of) is date else iso(as_of)
    if not cutoff:raise ValueError('as_of must be an ISO date')
    result={};groups=defaultdict(list)
    for r in rows:
        rid=r.get('id')
        if not rid or rid in result:raise ValueError('Missing or duplicate event identity: '+str(rid))
        ob=observation(r,cutoff);ob['permit_semantics_url']=REFERENCES.get(r.get('dataset')) or r.get('source_url') or r.get('url');result[rid]=ob
        if ob['permit_key']:groups[ob['permit_key']].append((rid,ob))
    for members in groups.values():
        pool=members; reason=None; chronology_conflict=False
        if any(o['_version'] is not None for _,o in pool):
            v=max(o['_version'] for _,o in pool)
            most_recent=[m for m in pool if m[1]['_version']==v]
            latest_known=[o['_day'] for _,o in most_recent if o['_day']]
            prior_known=[o['_day'] for _,o in pool if o['_version']<v and o['_day']]
            chronology_conflict=bool(latest_known and prior_known and min(latest_known)<max(prior_known))
            pool=most_recent
        tags={o['permit_bucket'] for _,o in pool}
        if len(tags)>1 and all(o['_day'] is not None for _,o in pool):
            latest=max(o['_day'] for _,o in pool);pool=[m for m in pool if m[1]['_day']==latest];tags={o['permit_bucket'] for _,o in pool}
        if chronology_conflict:bucket=UNC;reason='Agency renewal sequence conflicts with source effective dates.'
        elif len(tags)>1: bucket=UNC;reason='Conflicting statuses cannot be ordered by a reliable date.'
        else:bucket=next(iter(tags))
        best=max(pool,key=lambda m:(m[1].get('_day') or date.min,m[0]));best[1]['permit_representative']=True
        for _,o in members:
            o['permit_bucket']=bucket;o['permit_reason']=reason or best[1]['permit_reason'];o.pop('_day');o.pop('_version')
    return result
