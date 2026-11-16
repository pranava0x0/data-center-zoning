import csv, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path
from pipeline.build_history import locality
from collectors.multistate.ckan_catalog_csv import clean
class HistoryTests(unittest.TestCase):
    def test_published_exports(self):
        with (ROOT/'output/permit_history.csv').open() as f:rows=list(csv.DictReader(f))
        s=json.loads((ROOT/'output/permit_history_summary.json').read_text())
        self.assertEqual(s['rows'],len(rows));self.assertEqual(len(rows),len({x['id'] for x in rows}))
        self.assertEqual(s['loudoun_rows'],sum(x['locality']=='Loudoun County' for x in rows))
        self.assertTrue(all(x['date_role'] and x['url'].startswith('https://') for x in rows))
    def test_monthly_files_and_structures_stay_distinct(self):
        supplement=json.loads((series_path('building')).read_text())
        issued={r['record_no'] for r in json.loads((series_path('loudoun')).read_text()) if r['dataset']=='Loudoun issued permits'}
        monthly=[r for r in supplement if r['dataset']=='Loudoun monthly building reports']
        self.assertTrue(monthly);self.assertFalse(issued.intersection(r['record_no'] for r in monthly))
        with (ROOT/'output/permit_history.csv').open() as f:report={r['id'] for r in csv.DictReader(f)}
        self.assertTrue(all(r['id'] in report for r in monthly))
        structures=[r for r in supplement if r['kind']=='Data-center structure observation']
        self.assertTrue(structures);self.assertFalse(report.intersection(r['id'] for r in structures))
    def test_no_false_issue_dates(self):
        r=json.loads((series_path('cases')).read_text())
        bo=[x for x in r if x['jurisdiction']=='Botetourt County'];self.assertEqual({x['month'] for x in bo},{'2026-02','2026-08'});self.assertTrue(all(x['date'] is None for x in bo))
        self.assertEqual(sorted(x['date'] for x in r if x['record_no']=='LEGI-2023-0048'),['2024-03-13','2024-03-19','2024-04-10'])
        p=json.loads((series_path('pwc')).read_text())
        self.assertTrue(all(clean(v['record_no']) and v['date_role']=='occupancy date' for v in p))
    def test_locality_aliases(self):
        self.assertEqual(locality('Loudoun Co.'),locality('Loudoun County, VA'));self.assertNotEqual(locality('Fairfax Co.'),locality('Fairfax City'))
if __name__=='__main__':unittest.main()
