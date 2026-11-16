import json, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import collectors.virginia.manassas.development_actions as m
class Manassas(unittest.TestCase):
 def test_city_records_preserve_precision_and_instrument_gaps(self):
    rows=json.loads(m.OUT.read_text());by={r['id'].split('va-manassas-city-')[1]:r for r in rows}
    self.assertEqual((by['grading']['date'],by['grading']['month']),(None,'2022-07'))
    self.assertEqual((by['airport-review']['date'],by['airport-review']['month'],by['airport-review']['status']),(None,'2025-10','Site Plan under review'))
    self.assertEqual(by['occupancy']['date'],'2024-05-16')
    self.assertEqual((by['d2']['details']['address_as_reported'],by['d2']['date']),('9482 Technology Drive','2024-09-09'))
    self.assertTrue(all(not r['record_no'] and r['jurisdiction']=='City of Manassas' for r in rows))
