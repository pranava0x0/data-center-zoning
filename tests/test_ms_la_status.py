"""Source-pinned business checks for Louisiana/Mississippi two-register joins and planning events."""
import unittest, json, sys
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path
import collectors.mississippi.status as status_ms, collectors.louisiana.status as status_la
def annotate(mod,r):
    def make(ns,b,why,when):return ns,b
    def no(why,kind):return None,kind
    return mod.classify(r,date(2026,11,15),make,no,lambda:(None,'application'),None)
class Sources(unittest.TestCase):
    def test_mississippi_active_table_and_conflicting_termination(self):
        a=json.loads((series_path('ms')).read_text());by=lambda n:[r for r in a if r['record_no']==n and 'enSearch' in r['dataset']]
        self.assertEqual(annotate(status_ms,by('1460-00133')[0]),('MS:deq-air','active'))
        r=next(r for r in by('MSR109658') if r['status']=='Coverage Terminated')
        self.assertEqual(r['details']['epa_crosscheck']['status'],'EFF');self.assertEqual(annotate(status_ms,r),('MS:npdes','unconfirmed'))
        self.assertEqual(annotate(status_ms,next(r for r in a if r['id'].endswith('20260901-2'))),(None,'decision'))
    def test_louisiana_notice_appeal_and_shared_version(self):
        a=json.loads((series_path('la')).read_text())
        self.assertEqual(annotate(status_la,next(r for r in a if r['record_no']=='2460-00035-01')),(None,'notice'))
        rec=[r for r in a if r['record_no']=='25-127-C'];self.assertEqual([r['status'] for r in rec],['DENIED','Motion approved']);self.assertTrue(all(annotate(status_la,r)==(None,'decision') for r in rec))
        same=[r for r in a if r['record_no']=='LAR10Q310'];self.assertEqual(len(same),2);self.assertTrue(all(r['details']['epa_crosscheck'] for r in same));self.assertTrue(all(annotate(status_la,r)==('LA:npdes','unconfirmed') for r in same))
        for r in a:self.assertTrue(r['details']['county'].endswith(' Parish'))
