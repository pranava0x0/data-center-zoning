"""Audit card identity: official title, type plus identifier, named issuer, unresolved role. Writes the review queue."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, json, re
from collections import Counter, defaultdict
import lib.discovery as c
from pipeline.card_identity import audit, office_table, agency_table
csv.field_size_limit(10**9)
OK = ('snapshot_match', 'visual_source_check')
def main():
    rows = list(csv.DictReader((c.OUT / 'permit_history.csv').open()))
    rules = [r for r in json.loads((c.OUT / 'rules.json').read_text()) if r['check'] in OK]
    by, rc = audit(rows, rules)
    tot = Counter()
    for s in by.values(): tot.update(s)
    queue = []
    for r in rows:
        if r['issuer_role'] == 'publisher':
            queue.append(dict(kind='history record', id=r['id'], series=r['series'], dataset=r['dataset'], title=r['title'], publisher_shown=r['issuer'],
                              reason='No issuing or deciding office found; only the publisher is known', url=r['url']))
    for r in rules:
        if r['card_role'] == 'unreported':
            queue.append(dict(kind='ordinance rule', id=r['id'], series=r['state'], dataset=r['jurisdiction'], title=r['card_title'], publisher_shown=r['card_issuer'],
                              reason='No office found that issues or decides this approval', url=r['url']))
    with (c.OUT / 'card_identity_review.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, 'kind id series dataset title publisher_shown reason url'.split()); w.writeheader(); w.writerows(queue)
    n = len(rows)
    def pct(a, b): return f'{100*a/b:.1f}%' if b else '0%'
    basis = Counter((r['dataset'], r['issuer_basis']) for r in rows)
    BASIS = {'register_field': 'The register names the issuer', 'dataset_table': 'The register title names the agency', 'office_table': 'Office derived from record type (data/card_identity_offices.tsv)',
             'state_agency_table': 'State agency from EPA\'s authorized program (data/card_identity_state_agencies.tsv)', 'jurisdiction': 'Only the publisher is known'}
    by_basis = Counter(r['issuer_basis'] for r in rows)
    L = ['# Card identity audit', '',
         'Every card shows the title of the approval or record, then the jurisdiction and the issuing or deciding office, then one short sentence. This page counts how many cards can say that from the recorded data, by source series. [Review queue](../output/card_identity_review.csv) lists each card whose issuing or deciding office is still unknown.', '',
         '## How titles and offices are chosen', '',
         '- **Official title**: the issuer\'s own document title when the register supplies one (`filing_title`, `document_label`, `document_title`); a file extension is dropped. File names such as Iowa DNR `19-A-481.pdf` and permittee names are not titles.',
         '- **Type plus identifier**: the agency\'s record type and record number, for example "Building permit B2011476". Identifiers over 40 characters or containing " / " are agency file locators, not permit numbers, so those cards show the record type alone.',
         '- **Office from the register**: the register\'s own issuer or authority field, the federal issuer, or an agency the register title names (`data/card_identity_datasets.tsv`). Abbreviations such as ADEM, NDEQ or KY DEP are expanded from `data/card_identity_state_agencies.tsv`.',
         '- **Office from the record type**: when a register names no office, `data/card_identity_offices.tsv` maps the record type to the office the jurisdiction\'s own ordinance or agency page assigns it to, with the citation on the row. The `evidence` column says whether the cited page states the assignment or the row is inferred from the register\'s own publisher.',
         '- **State agency for EPA-reported permits**: ICIS lists the issuing agency of state-issued NPDES records as blank, "State" or "STA" for many states. Those records take the state agency that runs the EPA-authorized NPDES program, per EPA\'s state program page.',
         '- **Unresolved**: only the publisher is known. The card would show the publisher and the record is queued.', '',
         f'## Permit-history records ({n:,})', '',
         '| Source series | Records | Official title | Type + identifier | Type only | Named office | Unresolved |', '|---|---:|---:|---:|---:|---:|---:|']
    for s_, v in sorted(by.items(), key=lambda x: -x[1]['records']):
        L.append(f"| {s_} | {v['records']:,} | {v['official_title']:,} | {v['type_plus_identifier']:,} | {v['type_only']:,} | {v['named_issuer']:,} | {v['unresolved_role']:,} |")
    L.append(f"| **All** | **{n:,}** | **{tot['official_title']:,}** ({pct(tot['official_title'], n)}) | **{tot['type_plus_identifier']:,}** ({pct(tot['type_plus_identifier'], n)}) | **{tot['type_only']:,}** | **{tot['named_issuer']:,}** ({pct(tot['named_issuer'], n)}) | **{tot['unresolved_role']:,}** |")
    L += ['', 'Official titles are rare because most registers publish a record type and number, not a document title. Type plus identifier is the intended fallback, not a defect.', '',
          '### How each office was found', '', '| Basis | Records |', '|---|---:|']
    for k, v in by_basis.most_common(): L.append(f'| {BASIS.get(k, k)} | {v:,} |')
    L += ['', 'Registers whose office comes from the record type or the state program table (one row per register; each mapping and its citation is in the TSV):', '', '| Register | Basis | Records |', '|---|---|---:|']
    for (d, b_), k in sorted(basis.items(), key=lambda x: -x[1]):
        if b_ in ('office_table', 'state_agency_table'): L.append(f'| {d} | {BASIS[b_]} | {k:,} |')
    L += ['', f'Another {by_basis["dataset_table"]:,} records come from registers whose title names the agency (`data/card_identity_datasets.tsv`).']
    L += ['', f'## Ordinance rules ({sum(rc.values())})', '',
          'Titles, offices and one-sentence summaries are in [data/card_identity_rules.tsv](../data/card_identity_rules.tsv). Each row carries the verbatim quote and the page that names the office (`role_quote`, `citation`). The four Fairfax cards come from [data/fairfax_card_evidence.json](../data/fairfax_card_evidence.json).', '',
          '| What the office does | Rules |', '|---|---:|']
    for role, label in [('issues', 'Issues the permit'), ('decides', 'Decides the approval'), ('reviews', 'Reviews'), ('sets_standard', 'Adopted the standard'), ('adopted_by', 'Adopted the provision'), ('unreported', 'Not known')]:
        L.append(f'| {label} | {rc[role]} |')
    L += ['', f'Rules with no office: {rc["unreported"]}.', '',
          f'## Review queue', '', f'{len(queue):,} rows: {sum(1 for q in queue if q["kind"]=="history record"):,} history records and {sum(1 for q in queue if q["kind"]=="ordinance rule")} rules.', '']
    if queue:
        L += ['| Register (dataset) | Records | Publisher shown |', '|---|---:|---|']
        ds = Counter((q['dataset'], q['publisher_shown']) for q in queue if q['kind'] == 'history record')
        for (d, p), k in ds.most_common(25): L.append(f'| {d} | {k:,} | {p} |')
        L.append('')
    L += ['## Fairfax fixtures', '', 'Claims on the four Fairfax cards were checked against the adopted text, the county process and acceptance pages, the noise instructions and the October 27, 2026 amendment. Corrections: the size-limit and setback clauses are on page 2 of the adopted PDF, not page 3; the noise instructions cite the clause as 4102.7.A(6), the later codified number; the 2026 amendment states no effective date, so its 100 MW noise-profile requirement is shown as separate detail and not applied to earlier approvals. See each `checks` entry in the fixture file.', '']
    (c.R / 'docs/card-identity-audit.md').write_text('\n'.join(L))
    print(f'Card identity: {n:,} records, {tot["named_issuer"]:,} named issuer, {tot["unresolved_role"]:,} unresolved; {rc["unreported"]} rules unresolved.')
if __name__ == '__main__': main()
