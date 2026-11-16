"""Map numbers count distinct documented permits, independently of action/register counts."""
import csv, json, re, unittest
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'data/history/series.csv').open() as f:
    STATE_SET={r['state'] for r in csv.DictReader(f)}
class MapCounts(unittest.TestCase):
    def test_map_matches_permit_keys(self):
        text=(ROOT/'viewer/history-index.js').read_text()
        index=json.loads(text.split('=',1)[1].split(';window.PERMIT_CHUNKS')[0])
        with (ROOT/'output/permit_history.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(set(index['metrics']),STATE_SET)
        grouped=defaultdict(lambda:defaultdict(set))
        for r in rows:
            if r['permit_key']:grouped[r['state']][r['permit_bucket']].add(r['permit_key'])
        for state,classes in grouped.items():
            self.assertEqual({k:len(v) for k,v in classes.items()},index['metrics'][state]['*'])
        self.assertEqual(sum(index['totals'].values()),len(rows))
        self.assertGreater(len(rows),sum(len(v) for cls in grouped.values() for v in cls.values()))
    def test_default_file_has_no_script_dependencies(self):
        page=(ROOT/'viewer/index.html').read_text()
        self.assertNotRegex(page,r'<script[^>]+\bsrc=')
        for code in STATE_SET:
            for tail in ('','-details'):self.assertIn('id="pack-'+code+tail+'"',page)
