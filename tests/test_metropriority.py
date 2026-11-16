import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path
import collectors.ohio.central_ohio_entitlements as m
class MetroCases(unittest.TestCase):
 def setUp(self):self.rows=m.c.read(m.OUT,[])
 def test_competing_votes_and_count(self):
    p=[r for r in self.rows if r['record_no']=='PZ-22-42'];self.assertEqual(len(p),3)
    split=next(r for r in p if r['kind']=='Lot split');self.assertIn('Approved',split['status'])
    plans=sorted((r['date'],r['status']) for r in p if r['kind']=='Level B site plan');self.assertIn('denied',plans[0][1]);self.assertIn('Approved',plans[1][1]);self.assertGreater(plans[1][0],plans[0][0])
    cups=[r for r in self.rows if r['kind']=='Conditional use permit'];self.assertEqual(len({r['details']['permit_family'] for r in cups}),1)
 def test_true_council_date(self):
    council=next(r for r in self.rows if r['kind']=='Rezoning')
    self.assertEqual(council['date'],'2025-07-15');self.assertEqual(council['details']['gis_raw_case_date'],'2025-05-19')
 def test_exclusions_and_missing_day(self):
    ix=m.c.read(m.C/'manifest.json',{});g={f['attributes']['OBJECTID']:f['attributes'] for f in m.load(ix,'na')['features']}
    nums={r['record_no'] for r in self.rows};self.assertIn('Fulfillment',g[130651]['Name'])
    for oid in (130651,130866,130427,130597):self.assertNotIn(g[oid]['CaseNumber'],nums)
    self.assertIsNone(m.day(g[130597]['AdoptionDate']))
    prev={r['record_no'] for r in m.c.read(series_path('oh'),[]) if r['jurisdiction'] in ['Hilliard','New Albany']};self.assertTrue(nums.isdisjoint(prev))
if __name__=='__main__':unittest.main()
