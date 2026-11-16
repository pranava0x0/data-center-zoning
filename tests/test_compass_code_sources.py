import csv, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import ordinances.compass.code_sources as tool
class SourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.gs,cls.states=tool.initgeo()
 def match(self,*args):return tool.geo(*args,self.gs,self.states)
 def test_state_and_county_width(self):
    self.assertEqual(self.match('Alabama','','','','1000')[1]['geoid'],'01')
    self.assertEqual(self.match('Alabama','Baldwin','','County','1003')[1]['geoid'],'01003')
    self.assertEqual(self.match('Virginia','James City','','County','51095')[1]['geoid'],'51095')
    self.assertEqual(self.match('Virginia','','Roanoke','City','51770')[1]['geoid'],'51770')
 def test_geography_is_not_authority(self):
    st,j,why=self.match('New Jersey','Somerset','Franklin','Township','3401524840');self.assertIsNone(j)
    st,j,why=self.match('New Jersey','Gloucester','Franklin','Township','3401524840');self.assertEqual(j['geoid'],'3401524840')
    st,j,why=self.match('Ohio','Franklin','Franklin','Township','3401524840');self.assertIsNone(j)
 def test_released_rows_accounted(self):
    with tool.CSV.open() as f: rows=list(csv.DictReader(f))
    arr=json.loads((ROOT/'data/compass_sources.json').read_text())['releases']
    for a in arr:
        if not a.get('workbook_audit'):continue
        subset=[r for r in rows if r['technology']==a['technology']]
        positions=set()
        for r in subset:
            rowids=[]
            for v in r['excel_rows'].split(';'):
                bounds=list(map(int,v.split('-')));rowids.extend(range(bounds[0],bounds[-1]+1))
            self.assertEqual(len(rowids),int(r['feature_rows']));self.assertTrue(positions.isdisjoint(rowids));positions.update(rowids)
        self.assertEqual(len(positions),a['workbook_audit']['data_rows_with_state_and_feature'])
        self.assertTrue(all(r['workbook_sha256']==a['workbook_audit']['sha256'] for r in subset))
    self.assertEqual(50,len([r for r in rows if not r['original_url']]))
