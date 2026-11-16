import sys, json, unittest
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path
import collectors.minnesota.status as status_mn
class Minnesota(unittest.TestCase):
 def test_source_semantics(self):
    r=json.loads((series_path('mn')).read_text())
    fn=lambda x:status_mn.classify(x,date(2026,11,15),lambda ns,b,w,t:b,lambda w,k:k,None,None)
    self.assertEqual([fn(x) for x in r if x['record_no']=='BLDG1181293'],['unconfirmed'])
    self.assertEqual([fn(x) for x in r if x['record_no']=='BLDG631787'],['historical'])
    self.assertFalse(any('pickleball' in x['project'].lower() for x in r))
    self.assertFalse(any(x['record_no']=='255536-PROJ0000000001' for x in r))
    self.assertEqual([fn(x) for x in r if x['id']=='mn-chaska-2023-10-16'],['decision']);self.assertTrue(all(fn(x) for x in r))
