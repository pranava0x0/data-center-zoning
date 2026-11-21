"""Virginia source-review coverage with an explicit, pinned government baseline.

A locality where VDOT worked is not a second permitting authority. One reviewed
source does not establish a complete code review, permit census, or ROW ownership.
"""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRAME = ROOT / 'data/telecom/codex-research/authority-frame.json'


def canonical(value):
    value = ' '.join(re.sub(r'[^a-z0-9]+', ' ', value.lower()).split())
    for kind in ('county', 'city', 'town'):
        if value.startswith(kind + ' of '):
            return value[len(kind) + 4:] + ' ' + kind
    if value in ('vdot', 'virginia department of transportation'):
        return 'va-vdot'
    return value


def authority_frame(metadata=None, root=ROOT):
    metadata = metadata or json.loads(FRAME.read_text())
    source = root / metadata['roster_path']
    if hashlib.sha256(source.read_bytes()).hexdigest() != metadata['roster_sha256']:
        raise ValueError('Virginia authority roster changed; review and reseal its baseline')
    rows = []
    with source.open(newline='') as handle:
        for row in csv.DictReader(handle):
            if row['state'] != 'VA' or row['class_name'] != 'General Purpose':
                continue
            kind = 'county' if row['classification'] == '1 - COUNTY' else 'city' if row['name'].startswith('CITY OF ') else 'town'
            if row['classification'] not in ('1 - COUNTY', '2 - MUNICIPAL'):
                raise ValueError('Unreviewed government class: ' + row['classification'])
            rows.append(dict(authority_id='va-gov-' + row['government_id'], government_id=row['government_id'], state='VA', authority=row['name'].title(), jurisdiction_type=kind, source_url=row['source'], roster_vintage=metadata['roster_vintage'], row_control='Not established by government roster'))
    for row in metadata['additional_agencies']:
        rows.append(dict(**row, government_id=None, state='VA', source_url=None, roster_vintage=metadata['roster_vintage'], row_control='State highway permit authority; individual ROW ownership unconfirmed'))
    if len(rows) != metadata['denominator'] or len({r['authority_id'] for r in rows}) != len(rows):
        raise ValueError('Virginia authority baseline count or identity mismatch')
    return sorted(rows, key=lambda r: r['authority_id'])


def assess(checks, sources, frame=None, metadata=None):
    """Return a small viewer summary and a full exportable authority follow-up table.

    Callers verify source hashes before using source status. A check marked
    verified without an archived source is an error, not a completed authority.
    """
    metadata = metadata or json.loads(FRAME.read_text())
    frame = frame if frame is not None else authority_frame(metadata)
    names = {canonical(r['authority']): r['authority_id'] for r in frame}
    # A bare town name is accepted only when it cannot also mean a city/county.
    bases = {}
    for name, identity in names.items():
        base = re.sub(r' (?:county|city|town)$', '', name)
        bases.setdefault(base, set()).add(identity)
    names.update({base: next(iter(ids)) for base, ids in bases.items() if len(ids) == 1})
    groups = {r['authority_id']: [] for r in frame}
    unmatched = []
    for check in checks:
        if check.get('state') != 'VA':
            continue
        identity = names.get(canonical(check.get('authority', '')))
        if identity is None:
            unmatched.append(check['id'])
            continue
        if check.get('source_review') == 'verified':
            source = sources.get(check.get('source_id'))
            if not source or source.get('status') != 'retrieved' or not source.get('sha256') or not source.get('path'):
                raise ValueError('Verified coverage lacks archived primary source: ' + check['id'])
            if str(source.get('capture_method','')).strip().lower() in ('search snippet', 'search index'):
                raise ValueError('Discovery text cannot verify coverage: ' + check['id'])
        groups[identity].append(check)
    done = set()
    output = []
    for row in frame:
        reviews = groups[row['authority_id']]
        verified = any(r.get('source_review') == 'verified' for r in reviews)
        if verified:
            done.add(row['authority_id'])
        status = 'verified' if verified else 'partial' if any(r.get('source_review') == 'partial' for r in reviews) else 'blocked' if any(r.get('source_review') == 'blocked' for r in reviews) else 'not reviewed'
        output.append(dict(**row, source_review=status, check_ids=[r['id'] for r in reviews], blocked_check_ids=[r['id'] for r in reviews if r.get('source_review')=='blocked'], source_ids=sorted({r['source_id'] for r in reviews if r.get('source_id')}), history_review=[r.get('history_review', 'unknown') for r in reviews] or ['not searched']))
    pilot_names = ['va-vdot', 'fairfax county', 'loudoun county', 'leesburg town']
    pilot = {names[n] for n in pilot_names if n in names}
    if len(pilot) != 4:
        raise ValueError('Original Virginia pilot authorities are missing from the frame')
    def fraction(n, d, measure):
        return dict(numerator=n, denominator=d, percent=round(100*n/d, 1), measure=measure, national_completeness=None, history_completeness=None)
    summary = dict(
        pilot=fraction(len(done & pilot), len(pilot), 'Original Virginia pilot authorities with an archived primary-source review; not full histories or ordinance completeness'),
        virginia=fraction(len(done), len(frame), metadata['measure']),
        roster_vintage=metadata['roster_vintage'], roster_sha256=metadata['roster_sha256'],
        government_types=metadata['government_types'], limitations=metadata['limitations'],
        unmatched_checks=unmatched,
    )
    summary['virginia']['status_counts'] = {status:sum(r['source_review']==status for r in output) for status in ('verified','partial','blocked','not reviewed')}
    return summary, output
