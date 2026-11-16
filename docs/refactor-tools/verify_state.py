"""Verify a state's split collector reproduces the published files byte-for-byte, twice, with the network blocked.

    python3 verify_state.py <state_folder> [entry]     e.g. verify_state.py texas  (entry defaults to history.py)

Targets = every file the old collectors/<state>/all_sources.py wrote, per data/jurisdiction_registry.json
(its series in output/ plus its other outputs in data/). Baseline = the files as they are now (the published
edition, which equals the old collector's offline output)."""
import hashlib, json, os, subprocess, sys
from pathlib import Path
P = Path('/Users/pranava/Projects/local ordinance zoning')
state = sys.argv[1]; entry = sys.argv[2] if len(sys.argv) > 2 else 'history.py'
reg = json.loads((P / 'data/jurisdiction_registry.json').read_text())
c = reg['collectors'].get(f'collectors/{state}/all_sources.py') or reg['collectors'].get(f'collectors/{state}/history.py')
sys.path.insert(0, str(P / 'scripts'))
from lib.paths import series_path
targets = [series_path(s) for s in c['series']] + [P / f for f in c['other_outputs']]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
base = {str(t.relative_to(P)): sha(t) for t in targets}
env = dict(os.environ, HTTP_PROXY='http://127.0.0.1:9', HTTPS_PROXY='http://127.0.0.1:9', http_proxy='http://127.0.0.1:9', https_proxy='http://127.0.0.1:9')
env.pop('ATLAS_REFETCH', None)
runs = []
for i in (1, 2):
    r = subprocess.run([sys.executable, f'scripts/collectors/{state}/{entry}'], cwd=P, env=env, capture_output=True, text=True, timeout=1800)
    if r.returncode:
        sys.exit(f'FAIL run {i}: ' + (r.stderr or r.stdout)[-2000:])
    runs.append({str(t.relative_to(P)): sha(t) for t in targets})
bad = [k for k in base if not (base[k] == runs[0][k] == runs[1][k])]
print(('PASS' if not bad else 'FAIL') + f' {state}: {len(targets)} files checked' + (f'; differ: {bad}' if bad else ''))
sys.exit(1 if bad else 0)
