"""Two labels for every permit-history record.

link(row)     -> (basis, text): how the record is tied to a data center, in words a reader can check against the source.
review_class(row) -> 'land_use' when the record is a step in a discretionary land-use case about a data center
                 (rezoning, special exception, conditional use, board or commission action, regional siting review);
                 'other' for everything else (building, trade, air, water, fire and other permit history).
                 This is a workflow class, not an outcome: pending, on-agenda, denied and withdrawn cases are 'land_use' too.
                 The record's own status field says where the case stands; nothing here infers a grant.

Matching atlas display/detail fields come first, followed by collector statements, register membership and named facility/project fields.
Field excerpts describe atlas fields; they are not certified verbatim quotations from an agency document.
"""
import re

DC = re.compile(r'data[\s_-]*(?:cent(?:er|re)s?|ctr\b|halls?\b|processing cent(?:er|re)|backup cent(?:er|re))|datacent(?:er|re)'
                r'|hyperscale|server[\s-]*farm|colocation|co-location|high[\s-]performance[\s-]comput', re.I)
TEXT_FIELDS = ('title', 'project', 'kind')
DETAIL_TEXT = ('description', 'work_description', 'scope_excerpt', 'scope', 'evidence_excerpt', 'document_description',
               'match_value', 'evidence', 'decision_evidence', 'matched_text', 'source_facility_use')
STATED = ('facility_match', 'identity_basis')
# Collector notes in plain words. Notes not listed here are shown as written.
PLAIN = (
    ('Exact parcel and complete street address of county-coded data-center structure',
     'Same parcel and street address as a building Loudoun County records as a data center'),
    ('City permit at the existing state-verified data-center address', 'Issued at the address of a data center with a state air permit'),
    ('same permit file', "Filed in the same state permit file as the facility's data center records"),
    ('Exact municipal project number and normalized street address',
     'Same project number and address as a City of Phoenix record that names a data center'),
    ('Reviewed named project or supporting work', 'Named data center project, confirmed by a second source'),
    ('Named Colossus water-recycling works', 'Water-recycling plant serving the Colossus data center site'),
    ('CTC Property LLC and named Colossus facility', 'Names CTC Property LLC and the Colossus data center'),
    ('State air application includes explicit data-center identifier', 'The state air application names a data center'),
    ('Same permit number and campus confirmed by state draft notice', "Same permit number and campus as the state's draft notice"),
    ('DEC issued permit identifies data center explicitly', 'The issued state permit names a data center'),
    ('Eddy Lane named site plan', 'Same address and applicant as the Eddy Lane data center site plan'),
)
# Registers that list only data centers, so membership is the link. Each sentence names who made the list.
DATASETS = {
    'Prince William data-center building permits': "Listed in Prince William County's data center buildings layer",
    'Iowa DNR air construction equipment permit history': "Iowa DNR's plant roster names the plant a data center, or the city or operator does",
    'Iowa DNR signed Title V operating permits': "Iowa DNR's plant roster names the plant a data center",
    'Virginia DEQ issued data-center air permits': "Virginia DEQ's register of air permits issued to data centers",
    'Oklahoma DEQ final data-center instruments': "Oklahoma DEQ instrument for a project the agency files as a data center",
    'Loudoun fire marshal — data-center property authorizations': "Parcel and address of a structure Loudoun County codes as a data center",
}
LAND_USE = {'Land use & zoning', 'Regional development review', 'Planning consultation', 'Engineering, subdivision & land'}
# Discretionary decisions only. Ministerial zoning permits, plats and site plans are steps every large building takes.
DECISION_KIND = re.compile(r'rezon|zone change|land[ -]use application withdrawal|zoning (?:map|concept|ordinance|text)|special (?:exception|use)|conditional use|legislative|'
                           r'planning (?:motion|proceeding)|agenda|proceeding|development agreement|ordinance amendment|'
                           r'land[ -]use (?:decision|compatibility)|compatibility finding|regional impact|commission|council|'
                           r'board|variance|annexation|recomendaci|consulta|location consultation|siting|plan amendment|zoning amendment|'
                           r'zoning modification|appeal|act 250', re.I)


def snippet(text, m, width=70):
    s = ' '.join(str(text).split())
    m = DC.search(s)
    a = max(0, m.start() - width // 2)
    b = min(len(s), m.end() + width // 2)
    a = s.rfind(' ', 0, a) + 1 if a else 0
    b = s.find(' ', b) if b < len(s) and s.find(' ', b) > 0 else len(s)
    return ('…' if a else '') + s[a:b].strip(' ,;') + ('…' if b < len(s) else '')


def _str(v):
    return v if isinstance(v, str) else ''


def link(row):
    d = row.get('details') if isinstance(row.get('details'), dict) else {}
    for k in TEXT_FIELDS:
        v = _str(row.get(k))
        if DC.search(v):
            return 'record_text', 'Atlas ' + k.replace('_',' ') + ' field: ' + snippet(v, None)
    for k in DETAIL_TEXT:
        v = _str(d.get(k))
        if v and DC.search(v):
            return 'record_text', 'Atlas ' + k.replace('_',' ') + ' field: ' + snippet(v, None)
    for k in STATED:
        v = _str(d.get(k)).strip()
        if v:
            return 'stated', next((b for a, b in PLAIN if v.startswith(a)), v.rstrip('.'))
    if str(d.get('structure_type_match')) in ('True', 'true') or d.get('structure_type_match') is True:
        return 'register', 'Loudoun County lists the structure type as data center'
    if row.get('dataset') in DATASETS:
        return 'register', DATASETS[row['dataset']]
    for k, label in (('parcel_pins', 'Parcel'), ('parcel', 'Parcel'), ('tax_parcel', 'Parcel')):
        v = d.get(k)
        v = v[0] if isinstance(v, list) and v else v
        if v:
            return 'site', f'{label} {v}, at {row.get("project") or "a data center site"}'.rstrip()
    for k, label in (('plant_number', 'plant'), ('facility_id', 'facility'), ('facility_key', 'facility'), ('site_id', 'site'),
                     ('source_id', 'source')):
        v = d.get(k)
        if v and row.get('project'):
            return 'facility', f'Facility named in the record: {row["project"]} ({label} {v})'
    if row.get('project'):
        return 'project', 'Project named in the record: ' + ' '.join(str(row['project']).split())[:120]
    return 'none', ''


def review_class(row, basis):
    if row.get('category') not in LAND_USE:
        return 'other'
    if basis == 'none':
        return 'other'
    return 'land_use' if DECISION_KIND.search(str(row.get('kind') or '')) else 'other'


def encode(row, basis, text):
    """Short form for the viewer; viewer/app.js linkText() expands it. None means the default, worked out in this order: a
    quote from the title, project or kind when one names a data center; the register-wide sentence for the dataset
    (DATASETS, shipped once in the history index); the project named in the record."""
    d = row.get('details') if isinstance(row.get('details'), dict) else {}
    if basis == 'project' or (basis == 'register' and DATASETS.get(row.get('dataset')) == text):
        return None
    if basis == 'record_text':  # name the field; the viewer quotes it with the same pattern
        if any(DC.search(_str(row.get(k))) for k in TEXT_FIELDS):
            return None  # default: the viewer quotes the first of title, project, kind that names a data center
        for k in DETAIL_TEXT:
            if DC.search(_str(d.get(k))):
                return 'd' + k
        return 'x' + text
    if basis == 'facility':
        return 'f' + text[text.rindex('(') + 1:-1]
    return 'x' + text
