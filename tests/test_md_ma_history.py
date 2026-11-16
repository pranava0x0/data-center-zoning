import sys, json, unittest
from datetime import date
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from lib.paths import series_path, series_paths
from collectors.maryland.status import classify as md
from collectors.massachusetts.status import classify as ma
def data(st,fn):
 rr=json.loads((series_path(st)).read_text());out={}
 for r in rr:
    v=fn(r,date(2026,11,15),lambda reg,bkt,why,t,**k:(bkt,k.get('stable_no',r['record_no'])),lambda why,stage:(stage,None),lambda:('application',None),None)
    if not v:raise AssertionError(r['id'])
    out[r['id']]=v
 return out
class T(unittest.TestCase):
 def test_md(self):
    o=data('md',md);self.assertEqual(o['md-balt-COM2019-73587'],o['md-balt-COM2019-01000']);self.assertEqual(o['md-mde-storm-1'][0],'notice');self.assertEqual(o['md-mde-FR2023G001(03)'][1],'FR2023G001')
 def test_ma(self):
    o=data('ma',ma);self.assertEqual(o['ma-markley-affirm'][0],'decision');self.assertEqual(o['ma-markley-issue'],('unconfirmed','NE-25-002'));self.assertEqual(o['ma-mepa-401'][0],'unnumbered')
