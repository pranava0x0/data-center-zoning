import json, sys, unittest
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lib.paths import series_path, series_paths
import collectors.multistate.water_fire_authorizations as w
class WaterFireAudit(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.rows={s:w.c.read(series_path(f'waterfire_{s}'),[]) for s in ['ca','az','va','pa','tx','wa']}
    cls.registry={r['id']:r for rs in cls.rows.values() for r in rs}
 def cl(self,r):
    from pipeline.permit_status import observation
    # Test this adapter directly, including controls before shared dispatch is updated.
    cutoff=date(2026,11,16)
    def perm(reg,bucket,reason,when=None,version=None,stable_no=None):return (bucket, reg+'|'+(stable_no or r['record_no']))
    def no(reason,event='other'):return ('non_permit',event)
    def app():return no('','application')
    def obs(reg,historical=(),active=(),issued=(),when=None,held=()):
       s=r['status'].casefold()
       return perm(reg,'historical' if s in historical else 'unconfirmed' if s in issued else 'active' if s in active else 'unknown','')
    return w.classify(r,cutoff,perm,no,app,obs)
 def test_numbered_term_vs_operator_status(self):
    rs=self.rows['wa'];lookup={r['record_no']:r for r in rs}
    self.assertEqual(self.cl(lookup['ST0501377'])[0],'active')
    self.assertEqual(lookup['ST0008113']['details']['facility_status'],'Active')
    self.assertEqual(self.cl(lookup['ST0008113'])[0],'historical')
    self.assertEqual({self.cl(r)[1] for r in rs if r['record_no']=='ST0008106'},{'WA:ecology-industrial-user|ST0008106'})
    self.assertNotIn('ST0005278',lookup)
 def test_applications_and_crosswalk(self):
    self.assertEqual(self.cl(self.rows['tx'][0]),('non_permit','application'))
    self.assertEqual({self.cl(r)[1] for r in self.rows['pa']},{'PA:srbc-consumptive|20240901'})
    self.assertEqual(self.cl(next(r for r in self.rows['wa'] if r['record_no']=='CQ-010'))[0],'non_permit')
    self.assertIsNone(next(r for r in self.rows['wa'] if not r['record_no'])['date'])
 def test_fire_join_integrity(self):
    l={r['record_no'] for r in w.c.read(w.HIST,[]) if r['dataset']=='Loudoun issued permits'}
    self.assertFalse(l.intersection(r['record_no'] for r in self.rows['va']))
    old={r['record_no'] for r in w.c.read(w.AZREG,[]) if r['dataset']=='Phoenix permits'}
    self.assertFalse(old.intersection(r['record_no'] for r in self.rows['az']))
    self.assertNotIn('F214 2503584',{r['record_no'] for r in self.rows['az']})
    self.assertNotIn('F214 2505533',{r['record_no'] for r in self.rows['az']})
    self.assertTrue(all(r['details']['seed_ids'] for r in self.rows['az']))
    self.assertLess(sum(r['details']['fuel_explicit'] for r in self.rows['va']),len(self.rows['va']))
 def test_provenance(self):
    ix=w.c.read(w.INDEX,{});shas={s['sha256'] for s in ix.values() if s.get('sha256')}
    for r in self.registry.values():self.assertIn(r['source_sha256'],shas)
    for review in w.c.read(w.D/'water_fire_visual_reviews.json',[]):self.assertEqual(ix[review['source']]['sha256'],review['sha256'])
if __name__=='__main__':unittest.main()
