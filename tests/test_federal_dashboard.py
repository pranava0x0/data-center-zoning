"""Protect the decision-vs-target distinction and the actual closed date on ESA consultations."""
import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path, series_paths
from collectors.federal.fast41_dashboard import actual,classify
class DashboardTest(unittest.TestCase):
 def test_target_dates_and_flags(self):
  present=dict(action_milestone_complete=True,action_milestone_completion_target='2026-09-01T00:00:00')
  self.assertIsNone(actual(present)[0])
  self.assertIsNone(actual(dict(present,action_milestone_completion_actual='2026-11-16T00:00:00'))[0])
  self.assertIsNone(actual(dict(present,action_milestone_complete=False,action_milestone_completion_actual='2026-11-14'))[0])
  self.assertIsNone(actual(dict(present,action_milestone_na=True,action_milestone_completion_actual='2026-11-14'))[0])
 def test_agency_outcomes(self):
  rows=[r for st in ['oh','va'] for r in json.loads((series_path(f'fast_{st}')).read_text())]
  completed_esa={(r['state'],r['date'],r['status']) for r in rows if r['details'].get('milestone_final') and r['details'].get('action_type','').startswith('Endangered')}
  self.assertEqual(completed_esa,{('OH','2026-09-11','Biological opinion issued'),('VA','2026-07-02','Letter of concurrence issued')})
  for row in rows:
   result=classify(row,None,lambda *args:self.fail('Dashboard milestone counted as issued permit'),lambda why,bucket:bucket,None,None)
   self.assertIn(result,{'decision','determination','application','notice'})
  self.assertFalse(any('Final Verification/Permit Decision' in r['kind'] for r in rows))
