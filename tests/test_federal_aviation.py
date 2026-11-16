import csv, io, json, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from lib.paths import series_path, series_paths
import collectors.federal.faa_obstruction_evaluations as f
class FAA(unittest.TestCase):
 def test_csv_escaped_nested_data(self):
    out=io.StringIO();w=csv.writer(out,escapechar='\\',doublequote=False);w.writerow(['STUDY (ASN)','frequency','description']);w.writerow(['2026-AWP-1-OE','{"MHz":"900, 901"}','Building, data center']);w.writerow(['2026-AWP-2-OE','short']);w.writerow(['report generated','now'])
    good,bad=list(f.records(out.getvalue().encode()));self.assertIsNone(bad);self.assertEqual(good['description'],'Building, data center');self.assertEqual(good['frequency'],'{"MHz":"900, 901"}')
 def test_release_reconciles_and_signed_letter_matches(self):
    audit=json.loads((f.D/'federal_aviation_search.json').read_text());roster=audit['files'];self.assertEqual(len(roster),len({(r['region'],r['year']) for r in roster}));self.assertTrue(all(len(r['sha256'])==64 for r in roster));self.assertEqual(len(audit['held']),audit['summary']['held'])
    cases=[r for p in series_paths('faa_') for r in json.loads(p.read_text())];self.assertEqual(len({r['record_no'] for r in cases}),sum(r.get('included',0) for r in roster));self.assertEqual(len(cases),audit['summary']['included'])
    supplemental=json.loads((series_path('faaletters_ca')).read_text());cases+=supplemental;self.assertEqual(len(cases),len({(r['record_no'],r['status'],r['date']) for r in cases}))
    q=next(r for r in cases if r['record_no']=='2019-AWP-15211-OE');self.assertEqual((q['date'],q['status'],q['state'],q['source_url']),('2020-02-03','No Hazard','CA',f.LETTER))
    with (R/'output/federal_history.csv').open() as fp:
        public=[r for r in csv.DictReader(fp) if r['dataset']==f.REG]
    self.assertEqual(len(public),len(cases));self.assertTrue(all(not r['permit_key'] and r['permit_bucket']=='non_permit' for r in public))
