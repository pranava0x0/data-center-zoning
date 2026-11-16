import csv, json, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class VirginiaCrosswalk(unittest.TestCase):
 def test_old_permit_and_later_action_share_one_count_without_dating_expiry(self):
    with (R/'output/federal_history.csv').open() as f:rows=[r for r in csv.DictReader(f) if r['series']=='corpsprior_va']
    timber=[r for r in rows if r['record_no']=='NAO-2021-01135-mmw'];self.assertEqual(len(timber),5)
    old=next(r for r in timber if r['date']=='2021-10-01');self.assertEqual(json.loads(old['details'])['orm_action_date'],'2021-10-04')
    rep=[r for r in timber if r['permit_representative']=='True'];self.assertEqual([(r['date'],r['permit_bucket']) for r in rep],[('2026-03-10','unconfirmed')]);self.assertEqual({x['case_group'] for x in timber},{old['case_group']});self.assertTrue(old['case_group'])
    for r in rows:
        if 'notice' in r['dataset'].lower() or 'amendment' in r['dataset'].lower() or 'assessment' in r['kind'].lower():
            self.assertFalse(r['permit_key'],r)
