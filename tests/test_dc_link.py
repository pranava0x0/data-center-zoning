"""Every permit record says how it connects to a data center; discretionary land-use case records form their own class,
whatever their status."""
import csv, json, sys, unittest
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'scripts'))
from pipeline.dc_link import link, review_class


class Classify(unittest.TestCase):
    def test_record_text_quotes_the_words(self):
        b, t = link({'title': 'Building permit', 'project': 'NTT PH6 data center shell', 'kind': 'Building', 'details': {}})
        self.assertEqual(b, 'record_text')
        self.assertIn('data center', t)

    def test_collector_statement_wins(self):
        b, t = link({'project': 'x', 'details': {'facility_match': 'Exact parcel of a county-coded data-center structure.'}})
        self.assertEqual((b, t), ('stated', 'Exact parcel of a county-coded data-center structure'))

    def test_ministerial_zoning_permit_is_standard(self):
        row = {'category': 'Land use & zoning', 'kind': 'Zoning (Commercial)', 'title': 'Data hall fit-out', 'details': {}}
        self.assertEqual(review_class(row, link(row)[0]), 'other')

    def test_special_exception_is_a_land_use_case(self):
        row = {'category': 'Land use & zoning', 'kind': 'Special Exception', 'project': 'Data center campus', 'details': {}}
        self.assertEqual(review_class(row, link(row)[0]), 'land_use')

    def test_denied_and_withdrawn_cases_keep_their_class(self):
        for status in ('Denied', 'Withdrawn', 'In Review', 'On agenda'):
            row = {'category': 'Land use & zoning', 'kind': 'Conditional use permit', 'status': status, 'project': 'Data center', 'details': {}}
            self.assertEqual(review_class(row, link(row)[0]), 'land_use', status)

    def test_air_permit_is_standard(self):
        row = {'category': 'Air construction & operation', 'kind': 'Special exception', 'project': 'Data center', 'details': {}}
        self.assertEqual(review_class(row, link(row)[0]), 'other')


class Published(unittest.TestCase):
    def test_every_record_has_a_link(self):
        csv.field_size_limit(sys.maxsize)
        with (R / 'output/permit_history.csv').open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r['id'] for r in rows if not r['dc_link']], [])
        self.assertEqual(Counter(r['review_class'] for r in rows).keys(), {'land_use', 'other'})


if __name__ == '__main__':
    unittest.main()
