"""Which approval, who issues or decides it, and when: identity fields for every atlas card.

Rules: titles, issuers and roles come from reviewed files (data/card_identity_rules.tsv, data/fairfax_card_evidence.json).
History records: derived deterministically from the record itself (details, federal issuer, dataset, kind, record number),
with data/card_identity_datasets.tsv supplying the issuer a register names only in its title.
Issuing and deciding offices come from three reviewed tables, each row with its citation:
data/card_identity_datasets.tsv (agency named by a register's title), data/card_identity_offices.tsv (office by record type for
registers that name none) and data/card_identity_state_agencies.tsv (state agency for EPA-reported state permits).
A record none of these resolves gets role 'publisher' and is listed in output/card_identity_review.csv.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, json, re
from collections import Counter, defaultdict
import lib.discovery as c

RULE_ROLES = {'issues', 'decides', 'reviews', 'sets_standard', 'adopted_by', 'unreported'}
BODY = re.compile(r'Council|Commission|Board|Committee|Police Jury|Aldermen|Authority\b', re.I)
SKIP_ISSUER = {'', 'none', 'state', 'sta', 'unknown', 'n/a'}
ABBR = {('VA', 'DEQ'): 'Virginia Department of Environmental Quality', ('VA', 'VDH'): 'Virginia Department of Health',
        ('MS', 'MDEQ'): 'Mississippi Department of Environmental Quality', ('AL', 'ADEM'): 'Alabama Department of Environmental Management',
        ('PR', 'OGPE (pemasFreedom)'): 'Oficina de Gerencia de Permisos (OGPe)'}
ISSUER_KEYS = ['issuer', 'local_issuer', 'reported_issuer', 'decision_body', 'authority', 'agency', 'reporting_agency', 'state_authority', 'responsible_government']
TITLE_KEYS = ['filing_title', 'document_label', 'document_title']  # the issuer's own document title, when supplied
STATE_NAMES = {}


def _tsv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def rule_table():
    rows = {r['id']: r for r in _tsv(c.R / 'data/card_identity_rules.tsv')}
    fixture = json.loads((c.R / 'data/fairfax_card_evidence.json').read_text())
    for rid, f in fixture.items():
        rows[rid] = dict(id=rid, title=f['title'], role=f['role'], issuer=f['office'], decision_process=f.get('process', ''),
                         sentence=f['description'], sentence_basis='county sources checked ' + f['verified_on'],
                         role_quote=f['checks'][1]['source'] if len(f['checks']) > 1 else '',
                         citation='; '.join(s['label'] + ' | ' + s['url'] for s in f['sources']))
    return rows


def first_sentence(text):
    t = ' '.join(str(text or '').split())
    m = re.match(r'(.+?[.!?])(?:\s|$)', t)
    return m.group(1) if m else t


def apply_rules(rules):
    """Attach card_title, card_issuer, card_role, card_process, card_sentence, card_sentence_basis to every rule."""
    table = rule_table()
    missing = set(table) - {r['id'] for r in rules}
    if missing:
        raise ValueError('Card identity refers to missing ordinance: ' + str(sorted(missing)))
    for r in rules:
        t = table.get(r['id'])
        brief = r.get('reader_brief') or ''
        if t:
            if t['role'] not in RULE_ROLES or not t['title'].strip() or not t['issuer'].strip():
                raise ValueError('Incomplete card identity row: ' + r['id'])
            r['card_role_evidence'] = t['citation']
            r['card_role_quote'] = t['role_quote']
            r.update(card_title=t['title'], card_issuer=t['issuer'], card_role=t['role'], card_process=t['decision_process'],
                     card_identity='reviewed')
            sentence, basis = (t['sentence'], t['sentence_basis'] or 'reviewed') if t['sentence'] else (first_sentence(brief), 'first sentence of the reviewed brief')
            if r['id'].startswith('va-fx-'):
                sentence, basis = t['sentence'], t['sentence_basis']
        else:  # held records are not shown by default; give them an honest fallback, never a guess
            r.update(card_title=r.get('reader_title') or r['topic'].replace('_', ' ').capitalize(), card_issuer=r['authority'],
                     card_role='unreported', card_process='', card_identity='fallback')
            sentence, basis = first_sentence(brief), 'first sentence of the reviewed brief'
        if not sentence:
            sentence, basis = first_sentence(r['summary']), 'first sentence of the rule summary'
        r['card_sentence'], r['card_sentence_basis'] = sentence, basis
        r['reader_title'], r['reader_brief'] = r['card_title'], sentence
    return rules


def dataset_table():
    return {r['dataset']: r for r in _tsv(c.R / 'data/card_identity_datasets.tsv')}


def office_table():
    """Office by record type for registers that name no issuing or deciding office (data/card_identity_offices.tsv)."""
    rows = _tsv(c.R / 'data/card_identity_offices.tsv')
    for r in rows:
        r['_kind'], r['_record'], r['_place'] = (re.compile(r[k], re.I) if r[k] else None for k in ('kind_match', 'record_match', 'locality_match'))
    return rows


def agency_table():
    """State agency by state, and the spellings ICIS uses for it (data/card_identity_state_agencies.tsv)."""
    by_state, alias = {}, {}
    for r in _tsv(c.R / 'data/card_identity_state_agencies.tsv'):
        if r['alias']:
            alias[(r['state'], r['alias'].lower())] = r['agency']
        else:
            by_state[r['state']] = r['agency']
    return by_state, alias


def find_office(rows, r):
    for o in rows:
        if o['dataset'] != r['dataset']:
            continue
        if (o['_kind'] and not o['_kind'].search(r.get('kind') or '')) or (o['_record'] and not o['_record'].search(str(r.get('record_no') or ''))):
            continue
        if o['_place'] and not o['_place'].search(r.get('locality') or r.get('county') or ''):
            continue
        return o
    return None


def tidy_issuer(v):
    """'Faribault city of' (EQB) becomes 'City of Faribault'."""
    m = re.match(r'(.+?) (city|town|village|township) of$', v.strip(), re.I)
    return m.group(2).capitalize() + ' of ' + m.group(1) if m else v.strip()


def clean_title(v):
    s = ' '.join(str(v).split())
    return re.sub(r'\.(pdf|docx?)$', '', s, flags=re.I)


def history_identity(r, d, table, state_name, offices=(), agencies=({}, {})):
    """Return title, title_basis, issuer, issuer_role, issuer_basis for one history record."""
    title, tb = '', 'type_only'
    for k in TITLE_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip() and v != 'None' and not v.startswith('cache/'):
            title, tb = clean_title(v), 'official'
            break
    rec = str(r.get('record_no') or '').strip()
    if not title:
        kind = str(r.get('kind') or '').strip()
        usable = rec and len(rec) <= 40 and ' / ' not in rec
        title, tb = (kind + ' ' + rec if usable and rec not in kind else kind), ('type_id' if usable else 'type_only')
    permit = r.get('permit_bucket') in ('active', 'historical', 'unconfirmed')
    by_state, alias = agencies
    office = find_office(offices, r)
    issuer, basis, role = '', '', 'publisher'
    ds = table.get(r['dataset'])
    if office and office['override'] == 'yes':
        issuer, basis, role = office['office'], 'office_table', office['role']
    elif ds and ds['prefer'] == 'table' and ds['issuer']:
        issuer, basis, role = ds['issuer'], 'dataset_table', ds['role']
    else:
        fed = r.get('federal_issuer')
        cand = [fed] + [d.get(k) for k in ISSUER_KEYS]
        for v in cand:
            if isinstance(v, str) and v.strip().lower() not in SKIP_ISSUER:
                v = tidy_issuer(v)
                issuer = alias.get((r['state'], v.lower())) or ABBR.get((r['state'], v), v)
                basis = 'register_field'
                role = 'issues' if permit else ('acts' if BODY.search(issuer) else 'agency')
                break
        if not issuer and office:
            issuer, basis, role = office['office'], 'office_table', office['role']
        if not issuer and (d.get('agency_type') == 'ST6' or r['dataset'].startswith('EPA ICIS-NPDES')) and r['state'] in by_state:  # EPA lists the issuer as 'State' or leaves it blank
            issuer, basis, role = by_state[r['state']], 'state_agency_table', 'issues'
        if not issuer and ds and ds['issuer']:
            issuer, basis, role = ds['issuer'], 'dataset_table', ds['role']
    if basis in ('dataset_table', 'office_table'):
        role = {'decides': 'acts', 'acts': 'acts', 'reviews': 'reviews', 'publisher': 'publisher', 'issues': 'issues' if permit else 'agency'}[role]
    if not issuer:  # only the publisher is known: say so, do not promote it to issuer
        issuer, basis, role = r.get('jurisdiction') or r.get('locality') or state_name.get(r['state'], r['state']), 'jurisdiction', 'publisher'
    if basis == 'office_table' and office and office.get('evidence') == 'inferred':
        role = 'publisher'
    return title, tb, issuer, role, basis


def audit(rows, rules):
    """Counts by source series for the audit page."""
    by = defaultdict(Counter)
    for r in rows:
        s = by[r['series']]
        s['records'] += 1
        s['official_title'] += r['title_basis'] == 'official'
        s['type_plus_identifier'] += r['title_basis'] == 'type_id'
        s['type_only'] += r['title_basis'] == 'type_only'
        s['named_issuer'] += r['issuer_basis'] in ('register_field', 'dataset_table', 'office_table', 'state_agency_table')
        s['role_stated'] += r['issuer_role'] in ('issues', 'acts', 'agency', 'reviews')
        s['unresolved_role'] += r['issuer_role'] == 'publisher'
    rc = Counter(r['card_role'] for r in rules if r['check'] in ('snapshot_match', 'visual_source_check'))
    return by, rc


if __name__ == '__main__':
    print(len(rule_table()), 'rule identity rows;', len(dataset_table()), 'dataset rows;', len(office_table()), 'office rows')
