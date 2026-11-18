import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pipeline import card_identity as ci

OK = ('snapshot_match', 'visual_source_check')
TABLE = {'Austin issued construction permits': dict(issuer='City of Austin', role='issues', prefer=''),
         'Generic docket': dict(issuer='', role='publisher', prefer='')}


def rec(**k):
    r = dict(dataset='X register', state='TX', kind='Electrical Permit', record_no='2026-036762 EP', federal_issuer='', permit_bucket='active', jurisdiction='Austin', locality='Austin')
    r.update(k)
    return r


class RuleIdentity(unittest.TestCase):
    def test_every_published_rule_has_a_reviewed_identity(self):
        rules = [r for r in json.loads((ROOT / 'output/rules.json').read_text()) if r['check'] in OK]
        self.assertEqual(len(rules), 312)
        for r in rules:
            self.assertEqual(r['card_identity'], 'reviewed', r['id'])
            self.assertIn(r['card_role'], ci.RULE_ROLES - {'unreported'}, r['id'])  # every rule names the office that issues, decides or adopts it
            self.assertTrue(r['card_issuer'].strip() and r['card_sentence'].strip(), r['id'])
            self.assertFalse(r['card_title'].endswith('?'), r['id'])
            self.assertNotIn('…', r['card_title'] + r['card_sentence'], r['id'])
            self.assertLessEqual(len(r['card_sentence'].split()), 24, r['id'])  # one short sentence on the card face
            self.assertIsNone(__import__('re').search(r'[.!?]\s+[A-Z]', r['card_sentence'].strip()), r['id'])
            self.assertNotIn(' \u2014 ', r['card_title'], r['id'])  # "Title: detail", not an em dash

    def test_fairfax_fixture_matches_rule_data(self):
        fx = json.loads((ROOT / 'data/fairfax_card_evidence.json').read_text())
        rules = {r['id']: r for r in json.loads((ROOT / 'output/rules.json').read_text())}
        self.assertEqual(set(fx), {'va-fx-commercial-gfa', 'va-fx-industrial-gfa', 'va-fx-setback', 'va-fx-noise'})
        for rid, f in fx.items():
            self.assertEqual(rules[rid]['card_title'], f['title'])
            self.assertTrue(f['checks'] and all(c['url'].startswith('https://www.fairfaxcounty.gov/') for c in f['checks']))
            self.assertEqual(rules[rid]['effective'], f['effective'])
        self.assertEqual(rules['va-fx-commercial-gfa']['thresholds'][0]['value'], 40000)
        self.assertEqual(rules['va-fx-industrial-gfa']['thresholds'][0]['value'], 80000)
        self.assertEqual([t['value'] for t in rules['va-fx-setback']['thresholds']], [200, 300])
        self.assertEqual(fx['va-fx-setback']['role'], 'sets_standard')  # a standard, not a permit
        self.assertNotIn('permit', fx['va-fx-setback']['title'].lower())


OFFICES = [dict(dataset='Loudoun land-use applications', kind_match='^Special Exception$', record_match='', locality_match='', office='Loudoun County Board of Supervisors', role='decides', override='', _kind=__import__('re').compile('^Special Exception$'), _record=None, _place=None),
           dict(dataset='Loudoun land-use applications', kind_match='', record_match='', locality_match='', office='Loudoun County Department of Building and Development', role='decides', override='', _kind=None, _record=None, _place=None)]
AGENCIES = ({'TX': 'Texas Commission on Environmental Quality'}, {('TX', 'sta'): 'Texas Commission on Environmental Quality'})


class RuleOffices(unittest.TestCase):
    def test_no_rule_left_without_an_office(self):
        rules = [r for r in json.loads((ROOT / 'output/rules.json').read_text()) if r['check'] in OK]
        self.assertEqual([r['id'] for r in rules if r['card_role'] == 'unreported'], [])

    def test_resolved_rules_carry_a_quote_and_a_citation(self):
        import csv
        rows = {r['id']: r for r in csv.DictReader(open(ROOT / 'data/card_identity_rules.tsv'), delimiter='\t')}
        review = {r['id'] for r in csv.DictReader(open(ROOT / 'output/card_identity_review.csv'))}
        for rid, r in rows.items():
            self.assertTrue(r['issuer'].strip() and r['role'].strip(), rid)
            self.assertNotIn(rid, review)
            if r['role_quote'].strip():
                self.assertIn('http', r['citation'], rid)


class HistoryIdentity(unittest.TestCase):
    def test_office_comes_from_record_type_when_register_names_none(self):
        for kind, office in [('Special Exception', 'Loudoun County Board of Supervisors'), ('Plat', 'Loudoun County Department of Building and Development')]:
            *_, iss, role, basis = ci.history_identity(rec(dataset='Loudoun land-use applications', kind=kind, permit_bucket='non_permit'), {}, TABLE, {}, OFFICES)
            self.assertEqual((iss, role, basis), (office, 'acts', 'office_table'))

    def test_icis_state_permit_takes_the_states_npdes_agency(self):
        for d in ({'agency_type': 'ST6', 'reported_issuer': 'State'}, {'agency_type': 'ST6', 'reported_issuer': 'STA'}, {'agency_type': 'ST6'}):
            *_, iss, role, basis = ci.history_identity(rec(dataset='State-issued water permits reported to EPA'), d, TABLE, {}, (), AGENCIES)
            self.assertEqual((iss, role, basis), ('Texas Commission on Environmental Quality', 'issues', 'state_agency_table'))

    def test_type_plus_identifier_and_issuer_from_dataset(self):
        t, tb, iss, role, basis = ci.history_identity(rec(dataset='Austin issued construction permits'), {}, TABLE, {})
        self.assertEqual((t, tb, iss, role, basis), ('Electrical Permit 2026-036762 EP', 'type_id', 'City of Austin', 'issues', 'dataset_table'))

    def test_official_title_wins_and_register_issuer_is_used(self):
        t, tb, iss, role, basis = ci.history_identity(rec(), {'filing_title': 'Backup Generating Facility SPPE Application.pdf', 'issuer': 'California Energy Commission'}, TABLE, {})
        self.assertEqual((t, tb, iss, basis), ('Backup Generating Facility SPPE Application', 'official', 'California Energy Commission', 'register_field'))

    def test_locator_is_not_an_identifier(self):
        t, tb, *_ = ci.history_identity(rec(record_no='FID 122487 / 153 00215 / DEQ Notification / BEGIN CONSTRUCTION'), {}, TABLE, {})
        self.assertEqual((t, tb), ('Electrical Permit', 'type_only'))

    def test_publisher_only_is_unresolved_never_issuer(self):
        *_, iss, role, basis = ci.history_identity(rec(dataset='Generic docket', permit_bucket='non_permit'), {}, TABLE, {})
        self.assertEqual((iss, role, basis), ('Austin', 'publisher', 'jurisdiction'))

    def test_non_permit_event_is_not_issued_by(self):
        *_, role, _ = ci.history_identity(rec(permit_bucket='non_permit'), {'issuer': 'Planning Commission'}, TABLE, {})
        self.assertEqual(role, 'acts')
        *_, role, _ = ci.history_identity(rec(permit_bucket='non_permit'), {'issuer': 'City of Hartford'}, TABLE, {})
        self.assertEqual(role, 'agency')

    def test_generic_state_value_is_not_a_named_issuer(self):
        *_, role, basis = ci.history_identity(rec(), {'reported_issuer': 'State'}, TABLE, {})
        self.assertEqual((role, basis), ('publisher', 'jurisdiction'))


if __name__ == '__main__':
    unittest.main()
