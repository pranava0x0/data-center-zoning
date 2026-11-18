"""Replay reviewed Virginia telecom evidence. Network retrieval never publishes new claims.

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
from datetime import datetime
from lib.discovery import HTML, dump

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


def csv_write(path, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
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
        if p['evidence'] not in text((R / s['path']).read_text()):
            raise ValueError('Evidence no longer matches: ' + p['id'])
        p.update(technology='fiber_telecom', url=s['url'], source_sha256=s['sha256'], retrieved_at=s['retrieved_at'])
    instruments, events, locations = [], [], []
    for key, source in sources.items():
        if not re.fullmatch(r'vdot-\d+', key) or source['status'] != 'retrieved':
            continue
        fields, timeline = parse_vdot((R / source['path']).read_text())
        if fields.get('Application Type') != 'Utility - Fiber Optic' or fields.get('Agency Name') != 'VDOT':
            raise ValueError('Not a VDOT wireline record: ' + key)
        locality = fields['Locality']
        if locality not in ('Loudoun County', 'Fairfax County'):
            raise ValueError('Unreviewed locality: ' + locality)
        iid = 'va-' + key
        approved = fields['Application Status'] == 'APPROVED' and any(t['step']=='Permit Determination' and t['status']=='Complete' and t['actual_end'] for t in timeline)
        instrument = dict(id=iid, project_id=None, technology='fiber_telecom', title=fields['Application Type'] + ' — ' + fields['Application Number'], title_basis='agency type and application number', identifier=fields['Application Number'], identifier_type='application_number', instrument_type='land_use_permit' if approved else 'application', issuer='Virginia Department of Transportation', issuer_role='permitting agency', authority_geoid='51', row_controller='VDOT (permit authority); fee ownership not established', row_control_basis='VDOT land-use register; 24VAC30-151-20', row_control_source_url=sources['va-authority']['url'], applicant=fields['Applicant Name'], status=fields['Application Status'], validity='unconfirmed' if approved else 'not_issued', description=fields['Application Description'], original_target=iso(fields.get('Target Completion Date')), revised_target=iso(fields.get('Revised Target Date')), completion_date=iso(fields.get('Completion Date')), data_center_relationship='not established', source_id=key, url=source['url'], locator='Application Details; Application Process Details', source_sha256=source['sha256'], retrieved_at=source['retrieved_at'], source_inconsistency=any(t['status'] == 'In Progress' for t in timeline) and approved)
        instruments.append(instrument)
        locations.append(dict(id=iid + '-location', instrument_id=iid, state='VA', locality=locality, geoid='51107' if locality == 'Loudoun County' else '51059', location_basis='agency-reported locality', geometry=None))
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
            events.append(dict(id=event_id, instrument_id=iid, action=t['step'] + ': ' + t['substep'], date=iso(t['actual_end']), date_role='actual step end', actual_start=iso(t['actual_start']), target_start=iso(t['target_start']), target_end=iso(t['target_end']), status=t['status'], assignee=t['assignee'], description=t['description'], url=source['url'], locator='Application Process Details: ' + t['step'] + ' / ' + t['substep'], source_sha256=source['sha256'], source_id=key))
    iid = 'va-fairfax-newington-easement'
    s = sources['fairfax-may']
    instruments.append(dict(id=iid, project_id=None, technology='fiber_telecom', title='Fiber optic easement — 6900 Newington Road', title_basis='synthesized from Board item', identifier=None, identifier_type='not published', instrument_type='easement_authorization', issuer='Fairfax County Board of Supervisors', issuer_role='authorizes conveyance', authority_geoid='51059', row_controller='Fairfax County Board of Supervisors (Board-owned property)', row_control_basis='May 21, 2024 Board Summary, item 51', row_control_source_url=s['url'], applicant='MetroDuct Systems VA LLC', status='Conveyance documentation authorized', validity='not a street-opening permit', description='The Board authorized staff to prepare and execute easement documents. The record does not establish deed execution, recording, or an excavation permit.', data_center_relationship='not established', source_id='fairfax-may', url=s['url'], locator='Item 51, printed/PDF p. 36', source_sha256=s['sha256'], retrieved_at=s['retrieved_at']))
    locations.append(dict(id=iid + '-location', instrument_id=iid, state='VA', locality='Fairfax County', geoid='51059', location_basis='Board-owned property at 6900 Newington Road; parcels 0994 01 0015 and 0017', geometry=None))
    for source_id, day, action, locator in [('fairfax-april', '2024-04-16', 'Public hearing advertisement authorized', 'Admin 7, printed/PDF p. 30'), ('fairfax-may', '2024-05-21', 'Staff authorized to prepare and execute conveyance documents', 'Item 51, printed/PDF p. 36')]:
        s = sources[source_id]
        events.append(dict(id=iid + '-' + day, instrument_id=iid, action=action, date=day, date_role='Board action', status='Approved', assignee='Fairfax County Board of Supervisors', url=s['url'], locator=locator, source_id=source_id, source_sha256=s['sha256']))
    result = dict(schema_version='1.0.0', as_of='2026-11-18', provisions=provisions, instruments=sorted(instruments, key=lambda x: x['id']), events=sorted(events, key=lambda x: x['id']), locations=locations, coverage=json.loads((D / 'coverage.json').read_text()))
    O.mkdir(parents=True, exist_ok=True)
    dump(O / 'release.json', result)
    for name in ['provisions', 'instruments', 'events', 'locations', 'coverage']:
        csv_write(O / (name + '.csv'), result[name])
    (R / 'viewer/telecom.js').write_text('window.TELECOM=' + json.dumps(result, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f"Telecom: {len(provisions)} requirements, {len(instruments)} instruments/applications, {len(events)} events")
    return result


if __name__ == '__main__':
    build()
