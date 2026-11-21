"""Replay reviewed telecom evidence (Virginia permits and rules, Ohio and Texas rules, data center fiber records). Network retrieval never publishes new claims.

Snapshots and their SHA-256 receipts live in data/telecom so a fresh checkout works offline.
This collector writes only output/telecom/ and viewer/telecom.js.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import csv
import hashlib
import html
import json
import re
import io
from datetime import datetime
from lib.discovery import HTML, dump
from lib.telecom_coverage import assess

R = Path(__file__).resolve().parents[4]
D = R / 'data/telecom'
O = R / 'output/telecom'


def text(raw):
    parser = HTML()
    parser.feed(raw)
    return ' '.join(' '.join(parser.parts).split())


def iso(value):
    return datetime.strptime(value, '%m/%d/%Y').date().isoformat() if value else None


def parse_vdot(raw):
    fields = {text(k): text(v) for k, v in re.findall(r'<h6[^>]*>(.*?)</h6>\s*<p[^>]*>(.*?)</p>', raw, re.S)}
    applicant = re.search(r'Applicant Name</(?:h\d|label)>\s*<p[^>]*>(.*?)</p>', raw, re.S)
    if not applicant:
        # The header uses a div rather than p in some portal editions.
        lines = text(raw).split('Applicant Name', 1)[1].split('On this page', 1)[0].strip()
        fields['Applicant Name'] = lines
    else:
        fields['Applicant Name'] = text(applicant[1])
    rows = []
    for block in re.findall(r'<tr[^>]*>(.*?)</tr>', raw, re.S):
        cells = [text(v) for v in re.findall(r'<td[^>]*>(.*?)</td>', block, re.S)]
        if len(cells) == 11:
            rows.append(dict(zip(['step', 'substep', 'description', 'target_start', 'target_end', 'actual_start', 'actual_end', 'assignee', 'target_duration', 'actual_duration', 'status'], cells)))
    return fields, rows


DC_WORDS = re.compile(r'data[\s_-]*cent(?:er|re)|datacent|hyperscale|colocation', re.I)
LOCALITIES = {'Loudoun County': ('VA', '51107'), 'Fairfax County': ('VA', '51059'), 'Prince William County': ('VA', '51153')}
STATES = {'VA': 'Virginia', 'OH': 'Ohio', 'TX': 'Texas'}
NO_DC_LINK = 'The archived sources do not establish that this work serves a data center.'


def source_text(source, page=None):
    path = R / source['path']
    if path.suffix == '.pdf':
        from pypdf import PdfReader
        pages = PdfReader(str(path)).pages
        return ' '.join(' '.join(p.extract_text().split()) for p in ([pages[page - 1]] if page else pages))
    return text(path.read_text())


def say_date(value):
    d = datetime.strptime(value, '%m/%d/%Y')
    return d.strftime('%B ') + str(d.day) + d.strftime(', %Y')


def csv_write(path, rows, keys=None):
    keys = keys if keys is not None else list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for row in rows:
            out = {}
            for k in keys:
                v = row.get(k)
                s = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else '' if v is None else str(v)
                out[k] = "'" + s if s.startswith(('=', '+', '-', '@', '\t', '\r')) else s
            w.writerow(out)


def build():
    sources = json.loads((D / 'sources.json').read_text())
    for key, s in sources.items():
        if s['status'] != 'retrieved':
            continue
        if hashlib.sha256((R / s['path']).read_bytes()).hexdigest() != s['sha256']:
            raise ValueError('Source bytes changed: ' + key)
    # Validate the two-stage easement fixture against whole primary PDF pages, not a search snippet.
    from pypdf import PdfReader
    for key,page,anchor in [('fairfax-april',30,'Authorized the advertisement'),('fairfax-may',36,'prepare and execute')]:
        body=' '.join(PdfReader(R/sources[key]['path']).pages[page-1].extract_text().split())
        if anchor not in body or '6900' not in body or 'MetroDuct' not in body:raise ValueError('Easement source changed: '+key)
    provisions = json.loads((D / 'provisions.json').read_text())
    for p in provisions:
        s = sources[p['source_id']]
        if s['status'] != 'retrieved' or p.get('publication_status') not in ('published', 'held'):
            raise ValueError('Unreviewed source or publication status: ' + p['id'])
        if p['record_type']=='rezoning_proffer' and p['publication_status']!='held':
            raise ValueError('Proffer adoption requires separate reviewed evidence: ' + p['id'])
        if p['evidence'] not in source_text(s, p.get('page')):
            raise ValueError('Evidence no longer matches: ' + p['id'])
        if len(p['evidence'].split()) > 25 or p['scope_class'] not in ('data_center_specific', 'general') or not p.get('scope_basis'):
            raise ValueError('Quote too long or scope missing: ' + p['id'])
        p.update(technology='fiber_telecom', url=s['url'], source_title=s['title'], source_sha256=s['sha256'], retrieved_at=s['retrieved_at'], source_capture_method=s.get('capture_method','HTTP response'))
    instruments, events, locations = [], [], []
    for key, source in sources.items():
        if not re.fullmatch(r'vdot-\d+', key) or source['status'] != 'retrieved':
            continue
        fields, timeline = parse_vdot((R / source['path']).read_text())
        if fields.get('Application Type') != 'Utility - Fiber Optic' or fields.get('Agency Name') != 'VDOT':
            raise ValueError('Not a VDOT wireline record: ' + key)
        locality = fields['Locality']
        if locality not in LOCALITIES:
            raise ValueError('Unreviewed locality: ' + locality)
        if DC_WORDS.search(text((R / source['path']).read_text())):
            raise ValueError('Record mentions a data center; classify by hand: ' + key)
        received = next((t['actual_end'] for t in timeline if t['step'] == 'Application Received' and t['actual_end']), None)
        iid = 'va-' + key
        approved = fields['Application Status'] == 'APPROVED' and any(t['step']=='Permit Determination' and t['status']=='Complete' and t['actual_end'] for t in timeline)
        instrument = dict(id=iid, project_id=None, technology='fiber_telecom', title=fields['Application Type'] + ' — ' + fields['Application Number'], title_basis='agency type and application number', identifier=fields['Application Number'], identifier_type='application_number', instrument_type='land_use_permit' if approved else 'application', issuer='Virginia Department of Transportation', issuer_role='permitting agency', authority_geoid='51', state='VA', row_controller='VDOT (permit authority); fee ownership not established', row_control_basis='VDOT land-use register; 24VAC30-151-20', row_control_source_url=sources['va-authority']['url'], applicant=fields['Applicant Name'], status=fields['Application Status'], validity='unconfirmed', description=fields['Application Description'], original_target=iso(fields.get('Target Completion Date')), revised_target=iso(fields.get('Revised Target Date')), completion_date=iso(fields.get('Completion Date')), data_center_relationship='not established', scope_class='general', scope_basis=NO_DC_LINK, brief=f"{fields['Applicant Name']}: VDOT fiber optic permit application {fields['Application Number']}" + (f', received {say_date(received)}' if received else '') + f"; the register shows {fields['Application Status'].lower()}.", source_title=source['title'], source_id=key, url=source['url'], locator='Application Details; Application Process Details', source_sha256=source['sha256'], retrieved_at=source['retrieved_at'], source_inconsistency=any(t['status'] == 'In Progress' for t in timeline) and approved)
        instruments.append(instrument)
        locations.append(dict(id=iid + '-location', instrument_id=iid, state=LOCALITIES[locality][0], locality=locality, geoid=LOCALITIES[locality][1], location_basis='agency-reported locality', geometry=None))
        # Preserve duplicated/repeated source steps as evidence; deduplicate identical event observations.
        seen = set()
        for t in timeline:
            if not t['actual_end'] or t['status'] != 'Complete':
                continue
            signature = (t['step'], t['substep'], t['actual_start'], t['actual_end'], t['assignee'])
            if signature in seen:
                continue
            seen.add(signature)
            event_id = iid + '-' + hashlib.sha256('|'.join(signature).encode()).hexdigest()[:12]
            events.append(dict(id=event_id, instrument_id=iid, action=t['step'] + ': ' + t['substep'], date=iso(t['actual_end']), date_role='actual step end', actual_start=iso(t['actual_start']), target_start=iso(t['target_start']), target_end=iso(t['target_end']), status=t['status'], assignee=t['assignee'], description=t['description'], scope_class='general', scope_basis=NO_DC_LINK, brief=f"{t['assignee']} completed this step on {say_date(t['actual_end'])}.", source_title=source['title'], url=source['url'], locator='Application Process Details: ' + t['step'] + ' / ' + t['substep'], source_sha256=source['sha256'], source_id=key))
    iid = 'va-fairfax-newington-easement'
    s = sources['fairfax-may']
    instruments.append(dict(id=iid, project_id=None, technology='fiber_telecom', title='Fiber optic easement — 6900 Newington Road', title_basis='synthesized from Board item', identifier=None, identifier_type='not published', instrument_type='easement_authorization', issuer='Fairfax County Board of Supervisors', issuer_role='authorizes conveyance', authority_geoid='51059', row_controller='Fairfax County Board of Supervisors (property reported County-owned in the May 21, 2024 source; current ownership not rechecked)', row_control_basis='May 21, 2024 Board Summary, item 51', row_control_source_url=s['url'], applicant='MetroDuct Systems VA LLC', state='VA', scope_class='general', scope_basis=NO_DC_LINK, brief='The Board authorized staff to prepare and execute a fiber optic easement; no deed or excavation permit appears in the record.', source_title=s['title'], status='Conveyance documentation authorized', validity='Conveyance and current rights unconfirmed', description='The Board authorized staff to prepare and execute easement documents. The record does not establish deed execution, recording, or an excavation permit.', data_center_relationship='not established', source_id='fairfax-may', url=s['url'], locator='Item 51, printed/PDF p. 36', source_sha256=s['sha256'], retrieved_at=s['retrieved_at']))
    locations.append(dict(id=iid + '-location', instrument_id=iid, state='VA', locality='Fairfax County', geoid='51059', location_basis='Board-owned property at 6900 Newington Road; parcels 0994 01 0015 and 0017', geometry=None))
    for source_id, day, action, locator in [('fairfax-april', '2024-04-16', 'Public hearing advertisement authorized', 'Admin 7, printed/PDF p. 30'), ('fairfax-may', '2024-05-21', 'Staff authorized to prepare and execute conveyance documents', 'Item 51, printed/PDF p. 36')]:
        s = sources[source_id]
        events.append(dict(id=iid + '-' + day, instrument_id=iid, action=action, date=day, date_role='Board action', status='Approved', assignee='Fairfax County Board of Supervisors', scope_class='general', scope_basis=NO_DC_LINK, brief=action + '.', source_title=s['title'], url=s['url'], locator=locator, source_id=source_id, source_sha256=s['sha256']))
    state_by_instrument = {l['instrument_id']: l['state'] for l in locations}
    for e in events:
        e['state'] = state_by_instrument[e['instrument_id']]
    coverage = json.loads((D / 'coverage.json').read_text())
    coverage_summary, authorities = assess(coverage, sources)
    result = dict(schema_version='1.1.0', as_of='2026-11-21', provisions=provisions, instruments=sorted(instruments, key=lambda x: x['id']), events=sorted(events, key=lambda x: x['id']), locations=locations, coverage=coverage, coverage_summary=coverage_summary, authority_coverage=authorities)
    O.mkdir(parents=True, exist_ok=True)
    dump(O / 'release.json', result)
    for name in ['provisions', 'instruments', 'events', 'locations', 'coverage', 'authority_coverage']:
        csv_write(O / (name + '.csv'), result[name])
    fields = list(dict.fromkeys(k for p in provisions for k in p))
    for name, status in [('published','published'),('held','held')]:
        rows = [p for p in provisions if p['publication_status']==status]
        csv_write(O/(name+'.csv'),rows,fields)
    # The 323-entry follow-up queue is downloadable. It is not startup map data.
    viewer_result = {k:v for k,v in result.items() if k not in ('authority_coverage','coverage')}
    viewer_result['coverage_summary'] = {name:{key:coverage_summary[name][key] for key in ('numerator','denominator','percent')} for name in ('pilot','virginia')}
    viewer_result['coverage_summary']['roster_vintage'] = coverage_summary['roster_vintage']
    (R / 'viewer/telecom.js').write_text('window.TELECOM=' + json.dumps(viewer_result, ensure_ascii=False, separators=(',', ':')) + ';\n')
    from collections import Counter
    print(f"Telecom: {len(provisions)} requirements, {len(instruments)} instruments/applications, {len(events)} events")
    print('requirements by state/scope:', dict(sorted(Counter((p['state'], p['scope_class']) for p in provisions).items())))
    state_of = {l['instrument_id']: l['state'] for l in locations}
    print('instruments by state/scope:', dict(sorted(Counter((state_of[i['id']], i['scope_class']) for i in instruments).items())))
    return result


if __name__ == '__main__':
    build()
