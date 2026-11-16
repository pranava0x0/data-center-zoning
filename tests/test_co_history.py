import sys, json, unittest
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path
import collectors.colorado.status as status_co
class Colorado(unittest.TestCase):
 def test_air_request_not_issue_and_aurora_occupancy_scope(self):
    r=json.loads((series_path('co')).read_text())
    fn=lambda x:status_co.classify(x,date(2026,11,15),lambda ns,b,w,t:b,lambda w,k:k,None,None)
    self.assertEqual([fn(x) for x in r if x['record_no']=='25DG0038'],['application','notice'])
    self.assertEqual([fn(x) for x in r if x['record_no']=='09DE0597'],['unconfirmed','application'])
    self.assertEqual([fn(x) for x in r if x['id']=='co-aurora-B1911702'],['unconfirmed'])
    row=next(x for x in r if x['id']=='co-aurora-B1973703');self.assertEqual((row['date'],row['details']['certificate_expiration']),('2024-06-04','2024-07-01'));self.assertEqual(fn(row),'decision')
    self.assertEqual([fn(x) for x in r if x['record_no']=='2016-COMMCON-0002700'],['historical']);self.assertTrue(all(fn(x) for x in r))
