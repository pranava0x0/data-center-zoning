import json, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from lib.paths import series_path
import collectors.federal.faa_letters_california_energy as f
class Letters(unittest.TestCase):
    def test_cover_signature_and_supplemental_events(self):
        rows=json.loads(f.OUT.read_text())
        a=next(r for r in rows if r['record_no']=='2019-AWP-15211-OE')
        self.assertEqual((a['date'],a['details']['docketed_date'],a['status'],a['details']['original_structure_type']),('2020-02-03','2020-02-12','No Hazard','Building Data Center'))
        for r in rows:
            self.assertEqual(r['details']['federal_issuer'],'Federal Aviation Administration')
            self.assertRegex(r['details']['signature_control_number'],r'^\d+-\d+$')
        ex=[r for r in rows if r['details']['transaction_number']=='264840']
        self.assertEqual(len(ex),8)
        self.assertEqual({(r['status'],r['date'],r['details']['conditional_expiry_as_stated']) for r in ex},{('Extension','2025-04-07','2026-10-07')})
    def test_duplicates_only_when_event_matches(self):
        rows=json.loads(f.OUT.read_text());bulk=json.loads((series_path('faa_ca')).read_text())
        self.assertTrue({r['record_no'] for r in rows}&{r['record_no'] for r in bulk})
        self.assertFalse({f.key(r) for r in rows}&{f.key(r) for r in bulk})
    def test_no_map_or_cover_promoted(self):
        manifest=json.loads(f.IDX.read_text());tn='232020';m=manifest[tn];pages=json.loads((f.C/(m['sha256']+'.json')).read_text());cfg=json.loads(f.CFG.read_text())[tn]
        rows,nonletter=f.parse(tn,cfg,m,pages)
        self.assertEqual((len(rows),nonletter),(1,[1]))
        rows,nonletter=f.parse(tn,cfg,m,[pages[0],pages[-1]])
        self.assertFalse(rows)
        with self.assertRaises(ValueError):f.parse(tn,cfg,m,[s.replace('Signature Control No:', 'Inventory No:') for s in pages])
