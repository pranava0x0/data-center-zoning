"""Layout rules (docs/plan-collector-layout.md).

scripts/
  lib/          shared code, named for its format; imports only lib/
  collectors/   <state>/..., federal/, multistate/, territories/; a collector imports lib/ and its own folder only
  pipeline/     build, export, validate, release; may import anything
  ordinances/   ordinance discovery and rules research
"""
import ast, unittest
from pathlib import Path

S = Path(__file__).resolve().parents[1] / 'scripts'
AREAS = ('lib', 'collectors', 'pipeline', 'ordinances')
# Deliberate cross-folder dependencies, each with its reason. Keep this list short.
ALLOWED = {
    ('collectors/federal/epa_npdes.py', 'pipeline.national_gate'): 'federal water results must pass the national geography gate',
    ('collectors/federal/epa_npdes_discovery.py', 'pipeline.national_gate'): 'same gate after discovery',
    ('collectors/federal/faa_obstruction_evaluations.py', 'pipeline.national_gate'): 'FAA points must pass the same gate',
    ('collectors/multistate/water_fire_authorizations.py', 'collectors.virginia.loudoun_county.monthly_reports'):
        'Loudoun fire-marshal records are screened against the parcels in the archived Loudoun layer',
}


def local_imports(p):
    for n in ast.walk(ast.parse(p.read_text())):
        mods = [n.module] if isinstance(n, ast.ImportFrom) and n.module and not n.level else \
               [a.name for a in n.names] if isinstance(n, ast.Import) else []
        for m in mods:
            if m.split('.')[0] in AREAS:
                yield m
    src = p.read_text()
    for m in __import__('re').findall(r"import_module\('([\w.]+)'\)", src):
        yield m


class Layout(unittest.TestCase):
    def test_nothing_loose_at_top_of_scripts(self):
        self.assertEqual(sorted(p.name for p in S.iterdir() if p.is_file()), [])

    def test_lib_imports_only_lib(self):
        bad = [f'{p.relative_to(S)} -> {m}' for p in S.glob('lib/*.py') for m in local_imports(p)
               if not m.startswith('lib')]
        self.assertEqual(bad, [])

    def test_collectors_import_only_lib_and_their_own_folder(self):
        bad = []
        for p in sorted(S.glob('collectors/**/*.py')):
            area = p.relative_to(S).parts[1]  # e.g. virginia, federal, multistate
            for m in local_imports(p):
                parts = m.split('.')
                if parts[0] == 'lib' or (parts[0] == 'collectors' and len(parts) > 1 and parts[1] == area):
                    continue
                if (str(p.relative_to(S)), m) in ALLOWED:
                    continue
                bad.append(f'{p.relative_to(S)} -> {m}')
        self.assertEqual(bad, [], 'move shared code to lib/ instead')


if __name__ == '__main__':
    unittest.main()
