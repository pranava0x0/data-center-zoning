import unittest, json, sys
from pathlib import Path
from datetime import date
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from lib.paths import series_path
from collectors.iowa.status import classify as ia
from collectors.utah.status import classify as ut
def check(fn,r):return fn(r,date(2026,11,15),lambda reg,bucket,reason,dt,**k:(reg,bucket,k.get('stable_no',r['record_no'])),lambda why,ty:ty,lambda:'application',None)
class Snap(unittest.TestCase):
 def test_iowa(self):
    rows=json.loads((series_path('ia')).read_text());perm=[(r,check(ia,r)) for r in rows];self.assertTrue(all(v for _,v in perm));self.assertEqual(len({v for r,v in perm if r['record_no']=='2400752'}),1);self.assertIn('decision',[v for r,v in perm if r['record_no']=='26-024']);self.assertTrue(any(v[1]=='historical' for r,v in perm if r['status']=='Rescinded'));self.assertEqual(len({v[-1] for r,v in perm if r['record_no'].startswith('12-A-215')}),1)
 def test_utah(self):
    rows=json.loads((series_path('ut')).read_text());self.assertTrue(all(check(ut,r) for r in rows));self.assertTrue(all(check(ut,r)=='application' for r in rows if r['status']=='Notice of Intent received'));self.assertFalse(any('164894' in r['id'] for r in rows))
