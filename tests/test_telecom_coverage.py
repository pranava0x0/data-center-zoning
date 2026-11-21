import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('telecom_coverage', ROOT/'scripts/lib/telecom_coverage.py')
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


class TelecomCoverageTests(unittest.TestCase):
    def setUp(self):
        self.frame = [dict(authority_id=k, authority=n) for k,n in [
            ('vdot','Virginia Department of Transportation'), ('fairfax','County Of Fairfax'),
            ('loudoun','County Of Loudoun'), ('leesburg','Town Of Leesburg'),
            ('fairfax-city','City Of Fairfax'), ('henrico','County Of Henrico')]]
        self.meta = dict(measure='Fixture source checks', roster_vintage=2022, roster_sha256='f'*64, government_types={}, limitations=[])
        self.sources = {'s':dict(status='retrieved', sha256='a'*64, path='primary.html')}

    def check(self, identity, authority, state='VA', status='verified'):
        return dict(id=identity, state=state, authority=authority, source_review=status, source_id='s', history_review='bounded sample')

    def test_original_pilot_and_statewide_denominators_are_distinct(self):
        checks=[self.check('v-loudoun','VDOT'), self.check('v-fairfax','VDOT'), self.check('fairfax','Fairfax County')]
        result, rows=coverage.assess(checks, self.sources, self.frame, self.meta)
        self.assertEqual((result['pilot']['numerator'],result['pilot']['denominator'],result['pilot']['percent']),(2,4,50.0))
        self.assertEqual((result['virginia']['numerator'],result['virginia']['denominator']),(2,6))
        self.assertEqual(len(rows),6)
        self.assertEqual(next(r for r in rows if r['authority_id']=='loudoun')['source_review'],'not reviewed')
        self.assertIsNone(result['virginia']['history_completeness'])

    def test_out_of_state_reviews_cannot_inflate_virginia_coverage(self):
        checks=[self.check('oh','VDOT','OH'),self.check('tx','County of Loudoun','TX'),self.check('town','Town of Leesburg')]
        result,_=coverage.assess(checks,self.sources,self.frame,self.meta)
        self.assertEqual(result['virginia']['numerator'],1)
        self.assertEqual(result['pilot']['numerator'],1)

    def test_a_source_review_is_not_a_history_census(self):
        checks=[self.check('a','Loudoun County'),self.check('b','Loudoun County',status='blocked')]
        result,rows=coverage.assess(checks,self.sources,self.frame,self.meta)
        county=next(r for r in rows if r['authority_id']=='loudoun')
        self.assertEqual(county['source_review'],'verified')
        self.assertEqual(county['history_review'],['bounded sample','bounded sample'])
        self.assertIsNone(result['pilot']['history_completeness'])

    def test_ambiguous_place_names_do_not_merge_city_and_county(self):
        result,_=coverage.assess([self.check('ambiguous','Fairfax'),self.check('city','City of Fairfax')],self.sources,self.frame,self.meta)
        self.assertEqual(result['unmatched_checks'],['ambiguous'])
        self.assertEqual(result['virginia']['numerator'],1)
        self.assertEqual(result['pilot']['numerator'],0)

    def test_blocked_and_missing_reviews_are_not_zero_findings(self):
        result,rows=coverage.assess([self.check('blocked','Town of Leesburg',status='blocked')],self.sources,self.frame,self.meta)
        self.assertEqual(result['virginia']['numerator'],0)
        self.assertEqual(next(r for r in rows if r['authority_id']=='leesburg')['source_review'],'blocked')
        self.assertEqual(next(r for r in rows if r['authority_id']=='henrico')['history_review'],['not searched'])

    def test_verified_status_requires_an_archived_primary_source(self):
        check=self.check('bad','Loudoun County')
        with self.assertRaisesRegex(ValueError,'lacks archived'):
            coverage.assess([check],{},self.frame,self.meta)
        self.sources['s']['capture_method']='Search Snippet'
        with self.assertRaisesRegex(ValueError,'Discovery text'):
            coverage.assess([check],self.sources,self.frame,self.meta)

    def test_partial_charter_review_does_not_complete_blocked_permit_process(self):
        checks=[self.check('town-permit','Town of Leesburg',status='blocked'),self.check('town-charter','Town of Leesburg',status='partial')]
        result,rows=coverage.assess(checks,self.sources,self.frame,self.meta)
        row=next(r for r in rows if r['authority_id']=='leesburg')
        self.assertEqual(row['source_review'],'partial')
        self.assertEqual(row['blocked_check_ids'],['town-permit'])
        self.assertEqual(result['pilot']['numerator'],0)
        self.assertEqual(sum(result['virginia']['status_counts'].values()),len(self.frame))

    def test_pinned_frame_keeps_cities_once_and_preserves_government_ids(self):
        frame=coverage.authority_frame()
        self.assertEqual(len(frame),323)
        self.assertEqual(len({r['authority_id'] for r in frame}),323)
        kinds={k:sum(r['jurisdiction_type']==k for r in frame) for k in ['county','city','town','state agency']}
        self.assertEqual(kinds,dict(county=95,city=38,town=189,**{'state agency':1}))
        self.assertTrue(all(isinstance(r['government_id'],str) for r in frame if r['jurisdiction_type']!='state agency'))
        self.assertTrue(all(r['row_control']=='Not established by government roster' for r in frame if r['jurisdiction_type']!='state agency'))
        meta=json.loads(coverage.FRAME.read_text());meta['roster_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'roster changed'):
            coverage.authority_frame(meta)


if __name__=='__main__':
    unittest.main()
