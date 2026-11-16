"""Decision-table and grouping regressions; no live traffic."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pipeline.permit_status import permit_metrics

def row(id,ds,status='Issued',num='A-123',state='TX',day=None,kind='Building permit',details=None):
    return dict(id=id,state=state,dataset=ds,status=status,date=day,record_no=num,kind=kind,details=details or {},date_role='issue date')
def metrics(*rows):return permit_metrics(rows,as_of='2026-11-15')
class PermitBuckets(unittest.TestCase):
    def test_initial_and_renewed_oh_coverage_do_not_inflate_count(self):
        ds='Ohio EPA NPDES register'; args={'state':'OH','kind':'Construction Permits (NPDES)'}
        rows=[row('old',ds,'EXPIRED','4GC10001*AG',day='2019-02-02',**args),row('new',ds,'ACTIVE','4GC10001*BG',day='2025-04-01',details={'expiration_date':'2028-04-22'},**args),row('draft',ds,'DRAFT','4GC10001*CG',**args)]
        m=metrics(*rows);self.assertEqual(m['old']['permit_key'],m['new']['permit_key']);self.assertEqual(m['new']['permit_bucket'],'active');self.assertTrue(m['new']['permit_representative']);self.assertFalse(m['old']['permit_representative']);self.assertIsNone(m['draft']['permit_key'])
        self.assertEqual(m,metrics(*reversed(rows)))
    def test_conflicting_order_and_effective_dates_are_not_resolved_by_suffix_alone(self):
        ds='Ohio EPA NPDES register'
        m=metrics(row('a',ds,'EXPIRED','4GC10001*AG',state='OH',details={'effective_date':'2025-07-01'}),row('b',ds,'ACTIVE','4GC10001*BG',state='OH',details={'effective_date':'2024-01-01'}))
        self.assertEqual(m['b']['permit_bucket'],'unconfirmed')
    def test_explicit_active_with_past_expiration_is_unconfirmed(self):
        x=row('1','Ohio EPA NPDES register','ACTIVE','4GC10001*AG',state='OH',details=json.dumps({'expiration_date':'2020-04-22'}));self.assertEqual(metrics(x)['1']['permit_bucket'],'unconfirmed')
    def test_silent_issuance_is_not_active_or_explicitly_inactive(self):
        r=row('1','Dallas building permits',day='2001-01-01')
        self.assertEqual(metrics(r)['1']['permit_bucket'],'unconfirmed')
    def test_homonymous_issuers_do_not_merge(self):
        m=metrics(row('a','Dallas building permits'),row('b','San Antonio issued building and trade permits'));self.assertNotEqual(m['a']['permit_key'],m['b']['permit_key'])
    def test_contradictory_undated_states(self):
        m=metrics(row('a','Austin issued construction permits','Active'),row('b','Austin issued construction permits','Final'));self.assertEqual(m['a']['permit_bucket'],'unconfirmed');self.assertEqual(sum(x['permit_representative'] for x in m.values()),1)
    def test_issued_only_and_monthly_registers_share_proven_identity(self):
        m=metrics(row('a','Loudoun issued permits',state='VA',day='2020-10-03'),row('b','Loudoun monthly building reports',state='VA',day='2020-10-03'))
        self.assertEqual(m['a']['permit_key'],m['b']['permit_key']);self.assertEqual(sum(x['permit_representative'] for x in m.values()),1)
    def test_loudoun_real_final_date_not_issue_date(self):
        m=metrics(row('a','Loudoun issued permits',state='VA',details={'final_dates':['2022-12-09']}));self.assertEqual(m['a']['permit_bucket'],'historical')
    def test_state_approval_is_not_permit(self):
        m=metrics(row('a','TDLR architectural barriers registrations','Project Closed'),row('b','Indiana DHS Project Activity','Standard',state='IN',kind='Construction design release'),row('c','Virginia DEQ issued data-center air permits','Approved',state='VA'),row('d','Unknown city source','Active'))
        self.assertTrue(all(o['permit_bucket']=='non_permit' and o['permit_key'] is None for o in m.values()))
    def test_dated_cgp_final_termination_over_older_issue(self):
        ds='VA DEQ — Stormwater Permits Daily'
        m=metrics(row('a',ds,'PER_ISSUED',state='VA',details={'dates':{'SWC_APP_SIGNED_DT':'2020-04-01'}}),row('b',ds,'PER_TERM',state='VA',details={'dates':{'SWC_TERM_DATE':'2024-06-01'}}),row('c',ds,'MD_SUBMIT',state='VA'))
        self.assertEqual(m['a']['permit_bucket'],'historical');self.assertEqual(m['b']['permit_representative'],True);self.assertIsNone(m['c']['permit_key'])
    def test_arizona_open_plan_never_counts_and_open_issued_permit_needs_consistent_term(self):
        detail={'permit_type_code':'BLD','issue_date':'2026-02-01','expiration_date':'2028-02-01'}
        p=row('p','Phoenix permits','OPEN','BLD 100',state='AZ',details=detail)
        active=metrics(p);self.assertEqual(active['p']['permit_bucket'],'active')
        m=metrics(dict(p,id='review',dataset='Phoenix plan reviews'),dict(p,id='conflict',details=dict(detail,completion_date='2026-09-01')))
        self.assertFalse(m['review']['permit_representative']);self.assertEqual(m['conflict']['permit_bucket'],'unconfirmed')
    def test_arizona_air_codes_waivers_and_certificates_are_not_active_permits(self):
        air=row('a','Maricopa County air permit register','A','P0012345',state='AZ',kind='County air permit register / Minor',details={'operating_status':'Operating'})
        waiver=row('w','ADEQ myDEQ construction stormwater','Approval recorded','AZWV1',state='AZ',kind='Construction stormwater waiver register')
        cert=dict(row('c','Mesa building permit register','C of O Issued',state='AZ'),date_role='Opened date')
        m=metrics(air,waiver,cert);self.assertEqual(m['a']['permit_bucket'],'unconfirmed');self.assertEqual(m['w']['permit_event_type'],'waiver');self.assertEqual(m['c']['permit_event_type'],'certificate')
    def test_indiana_air_revision_requires_independently_linked_number_and_snapshot(self):
        ds='Indiana IDEM air decisions and notices';approved='Approval - Effective Immediately'
        original=row('one',ds,approved,'089-42502-00639',state='IN',kind='FESOP New Source Construction',day='2020-05-08')
        change=dict(row('two',ds,approved,'089-45165-00639',state='IN',kind='FESOP Significant Permit Revision',day='2023-03-31'),source_sha256='128beaed3864fa13b7b19dea1e1dfc30a0e70142452cacf33b0cbe1327ce5ad6')
        m=metrics(original,change,dict(change,id='unknown',source_sha256='changed'));self.assertEqual(m['one']['permit_key'],m['two']['permit_key']);self.assertTrue(m['two']['permit_representative']);self.assertIsNone(m['unknown']['permit_key'])
    def test_supplemental_site_trade_permits_and_planning_decisions(self):
        sc=row('s','Scottsdale permits at a verified data-center site','FINALLED',state='AZ',day='2022-10-19'); h=row('h','City of Hobart Plan Commission minutes','grant preliminary plat',state='IN')
        m=metrics(sc,h,dict(sc,id='missing',date=None));self.assertEqual(m['s']['permit_bucket'],'historical');self.assertEqual(m['h']['permit_event_type'],'decision');self.assertIsNone(m['missing']['permit_key'])
    def test_wrong_state_or_future_excluded(self):
        m=metrics(row('a','Dallas building permits',state='OH'),row('b','Dallas building permits',day='2027-01-01'));self.assertEqual(m['a']['permit_event_type'],'unknown');self.assertEqual(m['b']['permit_event_type'],'out_of_period')
if __name__=='__main__':unittest.main()
