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

    def test_display_fields_are_not_presented_as_verified_source_quotes(self):
        basis,text=link(dict(title='Atlas data center title',title_basis='type_id'))
        self.assertEqual(basis,'record_text')
        self.assertTrue(text.startswith('Atlas title field: '))
        self.assertNotIn('The record says',text)

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

    def test_recorded_zone_change_and_withdrawal_kinds_are_land_use(self):
        for kind,status in [('Zone change LU to PUD','Approved'),('Land use application withdrawal','Withdrawal posted')]:
            row=dict(category='Land use & zoning',kind=kind,status=status,project='Data center')
            self.assertEqual(review_class(row,link(row)[0]),'land_use',kind)
            self.assertEqual(row['status'],status)


class Published(unittest.TestCase):
    def test_existing_zone_change_and_withdrawals_keep_their_case_class(self):
        csv.field_size_limit(sys.maxsize)
        with (R/'output/permit_history.csv').open(newline='') as f:
            rows={r['id']:r for r in csv.DictReader(f)}
        for identity,status in [('wy-switchgrass-pud','Approved'),('ky-oldham-hwy','Withdrawal posted'),('ky-oldham-dw','Withdrawal posted')]:
            self.assertEqual(rows[identity]['review_class'],'land_use',identity)
            self.assertEqual(rows[identity]['status'],status,identity)

    def test_every_record_has_a_link(self):
        csv.field_size_limit(sys.maxsize)
        with (R / 'output/permit_history.csv').open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r['id'] for r in rows if not r['dc_link']], [])
        self.assertEqual(Counter(r['review_class'] for r in rows).keys(), {'land_use', 'other'})

    def test_link_text_uses_final_identity_fields(self):
        csv.field_size_limit(sys.maxsize)
        with (R/'output/permit_history.csv').open() as f:
            for row in csv.DictReader(f):
                row['details']=json.loads(row['details'])
                # CSV prefixes formula-like display cells; the viewer retains raw strings.
                for key in ('title','project','kind'):
                    value=row.get(key,'')
                    if len(value)>1 and value[0]=="'" and value[1] in '=+-@\t\r':
                        row[key]=value[1:]
                self.assertEqual(link(row),(row['dc_link_basis'],row['dc_link']),row['id'])


if __name__ == '__main__':
    unittest.main()
