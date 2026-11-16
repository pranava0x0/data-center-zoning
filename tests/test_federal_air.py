import sys, unittest, json
from pathlib import Path
from datetime import date
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'));import collectors.federal.epa_air_cases as fa
from lib.paths import series_path
class FederalAirTest(unittest.TestCase):
    def test_versions_and_late_effective_date(self):
        rows={r['id']:r for r in json.loads((series_path('federalair_nd')).read_text())}
        self.assertEqual({r['details']['source_facility_id'] for r in rows.values()},{'TAT-008149','TAT-008173'})
        perm=lambda reg,bucket,why,when=None,version=None,stable_no=None:(reg,bucket,stable_no)
        call=lambda row,dt:fa.classify(rows[row],date.fromisoformat(dt),perm,None,None,None)
        self.assertEqual(call('federal-air-crosby-2022','2024-03-10')[1],'unconfirmed')
        self.assertEqual(call('federal-air-crosby-2022','2024-03-11')[1],'historical')
        self.assertEqual(call('federal-air-crosby-2021','2026-11-15')[2],call('federal-air-crosby-2024','2026-11-15')[2])
        self.assertEqual(rows['federal-air-crosby-2024']['details']['effective_date'],'2024-03-11')
        self.assertEqual(rows['federal-air-crosby-2024']['date'],'2024-02-09')
    def test_no_pending_or_office_software(self):
        audit=json.loads((R/'data/national/federal_air_decisions.json').read_text())['hit_dispositions']
        self.assertIn('held_application_on_hold_project_use_unconfirmed',audit.values())
        self.assertIn('excluded_office_software',audit.values())
        self.assertTrue(all('008161' not in x['record_no'] for x in json.loads((series_path('federalair_nd')).read_text())))
