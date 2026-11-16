import json, sys, unittest
from pathlib import Path
from datetime import date
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from lib.paths import series_path
from collectors.arkansas.status import classify
class ArkansasTests(unittest.TestCase):
 def test_state_and_city_semantics(self):
    grouped={}
    for r in json.loads((series_path('ar')).read_text()):
      v=classify(r,date(2026,11,15),lambda reg,s,*a,**kw:s,lambda why,ty:ty,lambda:'application',None)
      self.assertIsNotNone(v,r['id']);grouped.setdefault(r['record_no'],set()).add(v)
    self.assertIn('active',grouped['2507-AOP-R0'])
    self.assertEqual({'application'},grouped['2507-AOP-R1'])
    self.assertIn('decision',grouped['HQR-RV9M-ZB672'])
    self.assertEqual({'historical'},grouped['202219031'])
    self.assertNotIn('202317461',grouped)
