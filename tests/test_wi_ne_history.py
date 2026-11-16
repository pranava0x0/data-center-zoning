import unittest, json, sys
from pathlib import Path
from datetime import date
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from lib.paths import series_path, series_paths
from collectors.nebraska.status import classify as ne
from collectors.wisconsin.status import classify as wi
def report(state,fn):
 out=[]
 for r in json.loads((series_path(state)).read_text()):
    result=fn(r,date(2026,11,15),lambda reg,bucket,reason,dt,**k:(bucket,k.get('stable_no',r['record_no'])),lambda why,ty:(ty,None),lambda:('application',None),None)
    if not result:raise AssertionError(r['id'])
    out.append((r,result))
 return out
class Checks(unittest.TestCase):
 def test_wi(self):
    a=report('wi',wi);self.assertIn(('active','25-MIN-094'),[v for _,v in a]);self.assertIn(('unnumbered',None),[v for r,v in a if r['status']=='conveyed']);self.assertTrue(all(v[0]=='application' for r,v in a if r['record_no']=='26-MIN-096'))
 def test_ne(self):
    a=report('ne',ne);self.assertIn(('historical','CP19-021'),[v for _,v in a]);self.assertIn(('unconfirmed','CP25-001'),[v for _,v in a]);self.assertTrue(all(v[0]=='application' for r,v in a if 'Applicant submittal' in r['status']));self.assertIn(('unnumbered',None),[v for r,v in a if r['id']=='ne-papp-foundation']);self.assertEqual(4,len([v for r,v in a if r['dataset']=='Lincoln nonresidential building permits']))
