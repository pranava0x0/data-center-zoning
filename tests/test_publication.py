"""Independent contract checks for downloadable tables and the deployed Pages artifact."""
import csv
import hashlib
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path
from urllib.parse import urlsplit, unquote

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'scripts'))
from pipeline.publish_site import feature_rows, build, BASE
from collectors.virginia.statewide.telecom_right_of_way import parse_vdot


class Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.site = R / '_site'
        cls.d = cls.site / 'downloads'
        cls.t = json.loads((cls.d / 'telecom-release.json').read_text())

    def csv(self, name):
        with (self.d / name).open(newline='') as f:
            return list(csv.DictReader(f))

    def test_manifest_and_zip_roundtrip(self):
        manifest = json.loads((self.d / 'manifest.json').read_text())
        archive=next(self.d.glob('*.zip'))
        self.assertEqual((self.d/'archive.sha256').read_text().split()[0],hashlib.sha256(archive.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive) as z:
            for item in manifest['files']:
                b = (self.d / item['name']).read_bytes()
                self.assertEqual(item['sha256'], hashlib.sha256(b).hexdigest(), item['name'])
                self.assertEqual(item['bytes'], len(b))
                self.assertEqual(z.read(item['name']), b)
                if 'rows' in item:
                    self.assertEqual(len(self.csv(item['name'])), item['rows'])

    def test_feature_keys_units_and_technology_isolation(self):
        rows = json.loads((self.d / 'features.json').read_text())
        self.assertEqual(len(rows), len({r['feature_id'] for r in rows}))
        rules = {r['id']: r for r in json.loads((self.d / 'data-center-research.json').read_text())}
        tc = {r['id']: r for r in self.t['provisions']}
        for r in rows:
            source = (rules if r['technology'] == 'data_center' else tc)[r['rule_id']]
            self.assertEqual(source.get('document_status', source.get('record_type')), 'adopted' if r['technology'] == 'data_center' else 'regulation')
            self.assertIsInstance(r['geoid'], (str, type(None)))
            self.assertRegex(r['source_sha256'], r'^[a-f0-9]{64}$')
            self.assertTrue(r['source_url'].startswith('https://'))
            if r['value'] is not None:
                self.assertTrue(r['units'])
                self.assertTrue(r['comparator'])
        setbacks = [r for r in rows if r['rule_id'] == 'va-fx-setback']
        self.assertEqual([(r['value'], r['units'], r['comparator']) for r in setbacks], [(200, 'ft', '>='), (300, 'ft', '>=')])
        self.assertIn('principal building', setbacks[1]['summary'])
        self.assertEqual(len(rows), len(self.csv('features.csv')))
        self.assertTrue(any((r['geoid'] or '').startswith('0') and len(r['geoid']) >= 5 for r in rows))

    def test_telecom_instrument_event_and_location_joins(self):
        instruments = {i['id']: i for i in self.t['instruments']}
        self.assertEqual(len(instruments), len(self.t['instruments']))
        self.assertEqual(len({e['id'] for e in self.t['events']}), len(self.t['events']))
        for row in self.t['events'] + self.t['locations']:
            self.assertIn(row['instrument_id'], instruments)
        for i in instruments.values():
            self.assertEqual(i['data_center_relationship'], 'not established')
            self.assertIsNone(i['project_id'])
            if i['instrument_type'] == 'land_use_permit':
                self.assertEqual(i['status'], 'APPROVED')
                self.assertEqual(i['validity'], 'unconfirmed')
        fixture = instruments['va-vdot-98688']
        self.assertEqual(fixture['identifier'], '949:61269')
        self.assertEqual(fixture['identifier_type'], 'application_number')
        self.assertEqual(fixture['completion_date'], '2026-10-19')
        self.assertEqual(fixture['original_target'], '2025-10-16')
        self.assertNotEqual(fixture['revised_target'], fixture['completion_date'])
        self.assertTrue(fixture['source_inconsistency'])
        dates = [e['date'] for e in self.t['events'] if e['instrument_id'] == fixture['id']]
        self.assertIn('2025-08-21', dates)
        easement = instruments['va-fairfax-newington-easement']
        self.assertEqual(easement['instrument_type'], 'easement_authorization')
        self.assertEqual(len([e for e in self.t['events'] if e['instrument_id'] == easement['id']]), 2)
        for l in self.t['locations']:
            self.assertIsNone(l['geometry'])

    def test_unavailable_sources_are_not_zero_findings(self):
        row = next(r for r in self.t['coverage'] if r['id'] == 'leesburg')
        self.assertEqual(row['source_review'], 'blocked')
        self.assertNotIn('result_count', row)
        coverage = json.loads((self.d / 'coverage.json').read_text())
        for c in coverage.values():
            self.assertIsNone(c['national_completeness'])
            self.assertEqual(c['percent'], round(100 * c['numerator'] / c['denominator'], 1))

    def test_csv_cells_do_not_execute_formulas(self):
        for p in self.d.glob('*.csv'):
            with p.open(newline='') as f:
                for row in csv.reader(f):
                    for cell in row:
                        self.assertFalse(cell.startswith(('=', '+', '-', '@', '\t', '\r')), (p.name, cell[:80]))

    def test_published_rules_export_matches_reviewed_records(self):
        rows = self.csv('data-center-rules.csv')
        approved = {r['id'] for r in json.loads((self.d / 'data-center-research.json').read_text()) if r['check'] in ('snapshot_match', 'visual_source_check')}
        self.assertEqual(approved, {r['id'] for r in rows})
        self.assertEqual(len(rows), len(approved))
        histories = self.csv('data-center-history.csv')
        self.assertEqual(len(histories), len({r['id'] for r in histories}))
        self.assertFalse(any('va-vdot-' in r['id'] for r in histories))
        self.assertTrue(all(r['issuer_evidence'].strip() for r in histories))
        for r in histories:
            if r['issuer_verification']=='inferred':self.assertEqual(r['issuer_role'],'publisher')

    def test_seo_and_static_answer_pages(self):
        for name in ['index.html', 'about.html', 'downloads.html', 'records.html','telecom.html']:
            s = (self.site / name).read_text()
            self.assertIn('name="description"', s)
            self.assertIn('rel="canonical"', s)
            self.assertIn('<h1>', s)
        self.assertIn('application/ld+json', (self.site / 'index.html').read_text())
        self.assertIn('national completeness', (self.site / 'llms.txt').read_text().lower())
        self.assertIn(BASE + 'sitemap.xml', (self.site / 'robots.txt').read_text())
        self.assertNotIn('cache', {p.name for p in self.site.iterdir()})
        self.assertTrue((self.site / '.nojekyll').exists())

    def test_all_local_public_links_resolve(self):
        for p in self.site.glob('*.html'):
            for link in re.findall(r'(?:href|src)="([^"]+)"', p.read_text()):
                url = urlsplit(link)
                if url.scheme or url.netloc or not url.path or url.path.startswith('blob:'):
                    continue
                self.assertTrue((p.parent / unquote(url.path)).resolve().is_file(), (p.name, link))


if __name__ == '__main__':
    unittest.main()
