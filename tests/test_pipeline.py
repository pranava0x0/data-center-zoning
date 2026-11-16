import csv, hashlib, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import lib.discovery as c, pipeline.build as build, ordinances.rules.extract_values as extract_values
class Pipeline(unittest.TestCase):
 def test_meaningful_extraction(self):
    r=next(x for x in extract_values.RECIPES if x[0]=='va-fx-setback')
    unrelated='The building must be located at least 200 feet from the lot line of an R district.'
    text=unrelated+' Power supply equipment, must be either: 1. located at least 300 feet from the lot line of an R district.'
    self.assertIsNone(extract_values.extract(unrelated,r[4]))
    self.assertEqual(extract_values.extract(text,r[4]),300)
    self.assertIsNone(extract_values.extract(text+text.replace('300','400'),r[4]))
 def test_pin_detects_document_or_claim_drift(self):
    with tempfile.TemporaryDirectory() as path,patch.object(c,'CACHE',Path(path)):
     data=b'alpha must apply before construction.';h=c.digest(data);(c.CACHE/(h+'.bin')).write_bytes(data);(c.CACHE/(h+'.txt')).write_bytes(data)
     url='https://example.org/statute';r=dict(id='x',url=url,evidence='must apply',summary='conditional');idx={url:dict(sha256=h,text_sha256=h,adapter='html')};pin={}
     self.assertEqual(build.audit(r,idx,pin,True)['check'],'snapshot_match')
     self.assertEqual(build.audit(dict(r,summary='unconditional'),idx,pin,True)['check'],'changed_since_review')
     self.assertEqual(build.audit(dict(r,evidence='may apply'),idx,pin,False)['check'],'passage_not_matched')
     (c.CACHE/(h+'.bin')).write_bytes(b'bad')
     self.assertEqual(build.audit(r,idx,pin,False)['check'],'snapshot_integrity_failure')
 def test_release(self):
    rows=c.read(c.OUT/'rules.json',[]);self.assertTrue(rows);live=[r for r in rows if r['check'] in ('snapshot_match','visual_source_check')]
    self.assertTrue(set(build.PILOT) <= {r['state'] for r in live} <= set(build.STATES))
    for r in live:
        self.assertIn(r['id'],c.read(c.R/'data/review_pins.json',{}))
        if r['check']=='visual_source_check':self.assertGreaterEqual(r['visual_review']['page'],1)
    grade=next(r for r in live if r['id']=='va-lou-grade');self.assertEqual(grade['thresholds'][0]['unit'],'ft2')
    legend=next(r for r in rows if r['id']=='va-lou-legacy-use')
    self.assertEqual({p['path'] for p in legend['pathways']},{'special exception','permitted use'})
    sw=c.read(c.OUT/'virginia_screen.json',{})
    for s in sw['results']:
        for d in s['documents']:
            p=c.R/'cache/va_sweep'/(d['sha256']+'.bin')
            self.assertEqual(c.digest(p.read_bytes()),d['sha256'])
 def test_geography_and_ranks(self):
    with (c.R/'data/jurisdictions.csv').open() as f:gs=list(csv.DictReader(f))
    self.assertEqual(len(gs),len({g['geoid'] for g in gs}))
    self.assertEqual(sum(g['state']=='VA' and g['layer']=='counties' for g in gs),133)
    with (c.R/'data/state_priority.csv').open() as f:rs=list(csv.DictReader(f))
    self.assertEqual([int(r['scenario_rank']) for r in rs],list(range(1,11)))
    for r in rs:self.assertEqual(int(r['total']),sum(int(r[k]) for k in ('operating','under_construction','planned')))
if __name__=='__main__':unittest.main()
