"""The per-jurisdiction registry must cover every collector and series the build publishes."""
import csv, json, sys, unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'scripts'))
import pipeline.jurisdiction as J


class RegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = json.loads((R / 'data/jurisdiction_registry.json').read_text())
        with (R / 'data/history/series.csv').open() as f:
            cls.series = {r['series']: r['state'] for r in csv.DictReader(f)}

    def test_every_make_history_collector_is_registered(self):
        self.assertEqual(sorted(J.makefile_collectors()), sorted(self.reg['collectors']))

    def test_every_published_series_has_an_owner(self):
        owned = {s for j in self.reg['jurisdictions'].values() for s in j['series']}
        self.assertEqual(set(self.series) - owned, set())

    def test_series_are_filed_under_their_own_jurisdiction(self):
        for st, j in self.reg['jurisdictions'].items():
            for s in j['series']:
                self.assertEqual(self.series[s], st, s)

    def test_collector_order_follows_make_history(self):
        order = J.makefile_collectors()
        for st, j in self.reg['jurisdictions'].items():
            self.assertEqual(j['collectors'], sorted(j['collectors'], key=order.index), st)

    def test_live_flags_match_collector_source(self):
        for script, c in self.reg['collectors'].items():
            if script in self.reg['overrides']:
                continue
            self.assertEqual(c['live'], J.live_flags(script), script)

    def test_prerequisites_name_real_scripts(self):
        for name, p in self.reg['prerequisites'].items():
            for cmd in p['commands']:
                self.assertTrue((R / 'scripts' / cmd[0]).exists(), name)


if __name__ == '__main__':
    unittest.main()
