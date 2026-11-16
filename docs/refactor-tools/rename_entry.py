"""Replace collectors/<state>/all_sources.py with history.py everywhere it is referenced."""
import json, sys
from pathlib import Path
P = Path('/Users/pranava/Projects/local ordinance zoning')
for state in sys.argv[1:]:
    old, new = f'collectors/{state}/all_sources.py', f'collectors/{state}/history.py'
    assert (P / 'scripts' / new).exists(), new
    if (P / 'scripts' / old).exists():
        (P / 'scripts' / old).unlink()
    for f in [P / 'Makefile', P / 'README.md', *sorted((P / 'docs').glob('*.md')), P / 'uat.md']:
        t = f.read_text(); n = t.replace(old, new)
        if n != t: f.write_text(n)
    for f in [*P.joinpath('scripts').rglob('*.py'), *P.joinpath('tests').glob('*.py')]:
        t = f.read_text(); n = t.replace(f'collectors.{state}.all_sources', f'collectors.{state}.history').replace(old, new)
        if n != t: f.write_text(n)
    r = json.loads((P / 'data/jurisdiction_registry.json').read_text())
    r['collectors'] = {(new if k == old else k): v for k, v in r['collectors'].items()}
    r['overrides'] = {(new if k == old else k): v for k, v in r['overrides'].items()}
    for j in r['jurisdictions'].values():
        j['collectors'] = [new if c == old else c for c in j['collectors']]
    (P / 'data/jurisdiction_registry.json').write_text(json.dumps(r, indent=2) + '\n')
    print('renamed', state)
