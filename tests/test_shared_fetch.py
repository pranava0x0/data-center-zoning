"""Shared fetch/ArcGIS modules: paging proof, stable query order, robots handling. No network."""
import sys, unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.robotparser import RobotFileParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import lib.arcgis as arcgis, lib.net as fetch


class FakeLayer:
    """An in-memory ArcGIS layer; records each URL the way the collectors build them."""
    def __init__(self, oids, drop=None, truncate=False):
        self.oids, self.drop, self.truncate, self.urls = oids, drop, truncate, []

    def get(self, url, **q):
        self.urls.append(url + ('?' + urlencode(dict(f='json', **q)) if q else ''))
        if 'returnIdsOnly' in q:
            return {'objectIds': list(reversed(self.oids))}
        want = [int(x) for x in q['objectIds'].split(',')]
        rows = [{'attributes': {'OBJECTID': i}} for i in want if i != self.drop]
        return {'features': rows, **({'exceededTransferLimit': True} if self.truncate else {})}

    @staticmethod
    def read(ref):
        return ref


class ArcgisTest(unittest.TestCase):
    def test_pull_pages_in_sorted_slices_and_records_round_trip(self):
        layer = FakeLayer(list(range(1, 8)))
        p = arcgis.pull(layer.get, layer.read, 'https://x/FeatureServer/0', "A='1'", 'OBJECTID', batch=3)
        self.assertEqual(len(p['batches']), 3)
        self.assertEqual([r['OBJECTID'] for r in arcgis.records(layer.read, p)], list(range(1, 8)))

    def test_query_parameter_order_is_stable(self):
        layer = FakeLayer([1, 2])
        arcgis.pull(layer.get, layer.read, 'https://x/0', "A='1'", 'OBJECTID,NAME')
        self.assertEqual(layer.urls, [
            "https://x/0/query?f=json&where=A%3D%271%27&returnIdsOnly=true",
            "https://x/0/query?f=json&objectIds=1%2C2&outFields=OBJECTID%2CNAME&returnGeometry=false"])

    def test_missing_feature_is_rejected(self):
        layer = FakeLayer([1, 2, 3], drop=2)
        with self.assertRaises(arcgis.Incomplete):
            arcgis.pull(layer.get, layer.read, 'https://x/0', '1=1', 'OBJECTID')

    def test_transfer_limit_is_rejected(self):
        layer = FakeLayer([1], truncate=True)
        with self.assertRaises(arcgis.Incomplete):
            arcgis.pull(layer.get, layer.read, 'https://x/0', '1=1', 'OBJECTID')

    def test_records_detect_a_lost_page(self):
        layer = FakeLayer(list(range(1, 5)))
        p = arcgis.pull(layer.get, layer.read, 'https://x/0', '1=1', 'OBJECTID', batch=2)
        p['batches'] = p['batches'][:1]
        with self.assertRaises(arcgis.Incomplete):
            arcgis.records(layer.read, p)


class FetchPolicyTest(unittest.TestCase):
    def setUp(self):
        fetch._robots.clear(); fetch._last.clear()

    def rules(self, origin, lines):
        rp = RobotFileParser(); rp.parse(lines); fetch._robots[(origin, False)] = rp

    def test_disallowed_path_is_refused(self):
        self.rules('https://gov.example', ['User-agent: *', 'Disallow: /private'])
        with self.assertRaises(fetch.Refused):
            fetch.polite('https://gov.example/private/x')
        fetch.polite('https://gov.example/public/x')

    def test_long_crawl_delay_stops_instead_of_waiting(self):
        self.rules('https://slow.example', ['User-agent: *', 'Crawl-delay: 120'])
        with self.assertRaises(fetch.Refused):
            fetch.polite('https://slow.example/a')

    def test_exempt_host_needs_a_reason(self):
        for host, why in fetch.ROBOTS_EXEMPT.items():
            self.assertGreater(len(why), 20, host)

    def test_params_keep_caller_order(self):
        self.assertEqual(fetch.with_params('https://a/b', {'z': 1, 'a': 2}), 'https://a/b?z=1&a=2')

    def test_wire_escapes_spaces_but_keeps_existing_escapes(self):
        self.assertEqual(fetch.wire('https://a/PubDocs/1R0372-10 Permit.pdf?x=1%2C2'),
                         'https://a/PubDocs/1R0372-10%20Permit.pdf?x=1%2C2')

    def test_rejects_non_http(self):
        with self.assertRaises(ValueError):
            fetch.polite('file:///etc/passwd')


if __name__ == '__main__':
    unittest.main()
