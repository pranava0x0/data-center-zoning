"""Regressions for state isolation, stage separation and ambiguous permit classes."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pipeline.compass_taxonomy import classify_rule, classify_history, classify_stage, UNMAPPED
from pipeline.validate_compass import rule_errors, extraction_errors, history_state, history_event_errors

class CrossState(unittest.TestCase):
    def test_state_does_not_follow_ticket_or_source_into_wrong_state(self):
        row=dict(state='OH',topic='water-withdrawal',level='state',map_geoid='51',url='https://law.lis.virginia.gov/vacode/',check='held')
        self.assertIn('different state government source',rule_errors(row,{'51':'VA'}))
        self.assertIn('wrong state geometry',rule_errors(row,{'51':'VA'}))
        self.assertIsNone(history_state({'state':'TX','jurisdiction':'Columbus, OH','id':'item-1'}))
    def test_regional_utility_is_not_assigned_parent_county(self):
        row=dict(state='VA',topic='water supply',level='regional',map_geoid='51107',url='https://www.loudounwater.org/',check='held')
        self.assertIn('service authority imputed to ordinary geography',rule_errors(row,{'51107':'VA'}))
    def test_new_state_does_not_inherit_a_numeric_trigger(self):
        rule={'state':'OH','url':'https://codes.ohio.gov/','sha256':'abc'}
        r={'state':'VA','source_url':rule['url'],'sha256':'abc','status':'adopted','condition':'30-day period','metric':'consumptive use','unit':'gal/day'}
        errs=extraction_errors(r,rule)
        self.assertIn('candidate crossed state, source, or snapshot',errs)
        self.assertIn('unreviewed candidate presented as definitive',errs)
    def test_technology_independent_categories_keep_source_meaning(self):
        self.assertEqual(classify_rule('use_classification'),'Land use & zoning')
        self.assertNotEqual(classify_rule('permitting_pause'),classify_rule('moratorium'))
        self.assertEqual(classify_history('Virginia Water Protection non-permit record'),'Wetlands & state waters')
        self.assertEqual(classify_history('Zoning Correspondence'),'Administration & correspondence')
        self.assertEqual(classify_history('Plan Review',program='Stormwater Plan Review'),'Construction stormwater')
        self.assertEqual(classify_history('Pending',program='Habitat Management'),'Wetlands & state waters')
        self.assertEqual(classify_history('Final Site Compliance Plan'),'Engineering, subdivision & land')
        self.assertEqual(classify_history('Unknown local process'),UNMAPPED)
    def test_completion_and_registration_are_not_issuance(self):
        for kind,status in [('Site compliance plan','Completed'),('Air permit public notice','Issued'),('State accessibility project registration','Issued'),('Variance','Withdrawn'),('Virginia Water Protection non-permit record','Active')]:
            self.assertNotEqual(classify_stage(kind,status),'Issuance reported')
        self.assertEqual(classify_stage('Construction stormwater','PER_ISSUED'),'Issuance reported')
    def test_publisher_date_semantics_differ_by_register(self):
        self.assertTrue(history_event_errors(dict(dataset='Fort Worth development permits',date_role='Issue date')))
        self.assertFalse(history_event_errors(dict(dataset='Austin issued construction permits',date_role='Issue date')))
        self.assertTrue(history_event_errors(dict(dataset='New Albany planning',status='Withdrawn',date_role='Adoption date')))
        self.assertFalse(history_event_errors(dict(dataset='New Albany zoning entitlements',status='Withdrawn',date_role='recorded disposition date (GIS AdoptionDate)')))
        self.assertEqual(classify_history('Surface Water Permit to Install',dataset='Ohio EPA selected air and water permits'),'Water & sewer infrastructure')
        self.assertEqual(classify_history('Construction Permits - inactive (NPDES)',dataset='Ohio EPA NPDES register'),'Construction stormwater')
    def test_attachment_does_not_supply_state_if_conflicting(self):
        self.assertEqual(history_state({'id':'anonymous','series':'cases'}),'VA')
        self.assertIsNone(history_state({'id':'anonymous','series':'cases'},'OH'))
        self.assertIsNone(history_state({'id':'J-23','jurisdiction':'Washington County'}))
if __name__=='__main__':unittest.main()
