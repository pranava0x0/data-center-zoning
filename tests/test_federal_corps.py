"""Exercise real distinctions that change federal counts, including calendar and duplicate-case traps."""
import collections, datetime as dt, hashlib, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from lib.paths import series_path, series_paths, collector_data
import collectors.federal.usace_regulatory as fc
from collectors.federal.status_usace import classify
class CorpsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows,cls.coverage=fc.build()
    def test_source_identity_distinct_from_events(self):
        eligible=[]
        for r in self.rows:
            self.assertEqual(r['details']['federal_issuer'],'US Army Corps of Engineers')
            def permit(reg,bucket,why,when):return (reg,r['record_no'])
            v=classify(r,dt.date(2026,11,16),permit,lambda why,event:event,lambda:'application',None)
            self.assertIsNotNone(v)
            if isinstance(v,tuple):eligible.append(v)
        self.assertEqual((len(eligible),len(set(eligible))),(31,27))
        ga=[x for x in self.rows if x['record_no']=='SAS-2023-00094']
        self.assertEqual(len({x['date'] for x in ga if x['details'].get('orm_view')=='issued'}),2)
    def test_held_company_and_geography(self):
        held=fc.j(collector_data('federal/usace_regulatory','held.json'))
        self.assertIn('NWP-2015-00206',held) # Public record is a sawmill on Amazon Creek.
        x=next(x for x in self.rows if x['record_no']=='SAS-2023-00094')
        self.assertEqual(x['state'],'GA');self.assertEqual(x['details']['census_county'],'Douglas County')
        self.assertNotIn('county',x['details'])
    def test_codenames_and_district_notices(self):
        z=[x for x in self.rows if x['dataset']==fc.PN and x['state']=='OH']
        self.assertEqual({x['details']['county'] for x in z},{'Pike County'})
        self.assertEqual({x['record_no'] for x in z},{'LRH-2026-00959-SCR','LRH-2026-00976-SCR'})
        self.assertTrue(all(x['details']['notice_documents'] for x in z))
    def test_reproducible_and_complete(self):
        def outputs(): return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in series_paths('corps_')}
        b=outputs();fc.build();self.assertEqual(outputs(),b)
        self.assertEqual(sum(self.coverage['by_state'].values()),len(self.rows))
        self.assertFalse(self.coverage['skipped'])
if __name__=='__main__':unittest.main()
