"""Test joins, duplicate issuances and distinctions between New York decisions and permits."""
import json, sys, unittest
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path
import collectors.new_york.status as status_ny
class NewYork(unittest.TestCase):
    records=json.loads((series_path('ny')).read_text())
    def by(self,n):return [r for r in self.records if r['record_no']==n]
    def cls(self,r):
        return status_ny.classify(r,date(2026,11,15),lambda ns,b,why,d:(ns,b),lambda w,k:(None,k),None,None)
    def test_number_is_not_an_issue_or_subtype(self):
        group=self.by('Q00600921-I1-GC-CX');self.assertEqual(len(group),2)
        self.assertEqual({r['details']['sequence'] for r in group},{'1','2'});self.assertEqual({self.cls(r) for r in group},{('NY:nyc-dob-now','historical')})
        self.assertEqual({self.cls(r) for r in self.by('104751065-02-EW')},{('NY:nyc-bis','unconfirmed')})
        self.assertTrue(all('doc__' in r['details']['linked_job_url'] for r in self.by('104751065-02-EW')))
    def test_modification_shared_number_and_planning_separate(self):
        rows=self.by('3-3924-00493/00001');self.assertEqual(len(rows),3)
        self.assertEqual({self.cls(r) for r in rows},{('NY:dec-air','unconfirmed')})
        self.assertEqual(self.cls(next(r for r in self.records if r['id']=='ny-somerset-sup')),(None,'decision'))
        self.assertEqual(self.cls(self.by('M01278410-I1-GC')[0]),('NY:nyc-dob-now','unconfirmed'))
    def test_every_source_has_interpretation(self):
        for r in self.records:self.assertIsNotNone(self.cls(r),r['id'])
