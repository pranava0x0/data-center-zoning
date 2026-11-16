"""Phase 4: rewrite literal references to history_* files in code and docs.

  python3 phase4_rewrite.py code ROOT   # scripts/ and tests/: path expressions -> series_path()/collector_data(), plus text
  python3 phase4_rewrite.py text ROOT   # README, docs, uat.md, issues.md: old file names -> new paths (text only)

Dynamic names (f-strings, string concatenation) are not touched; they are reported by `leftover`.
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from phase4_map import P, series_new_paths, data_new_path, OUTPUT_EXTRA

reg = json.loads((P / 'data/jurisdiction_registry.json').read_text())
SERIES = series_new_paths(reg)                     # series -> history/....json (relative to output/)
DATA_OLD = sorted(l.split('\t')[1].removeprefix('data/') for l in (P / 'docs/refactor-tools/phase4_moves.tsv').read_text().splitlines()[1:] if l.split('\t')[0] == 'data')
DATA = {n: data_new_path(n) for n in DATA_OLD}      # old name -> history/... (relative to data/) or None


def data_call(old):
    new = DATA[old] if old in DATA else data_new_path(old)
    folder, _, name = new.removeprefix('history/').rpartition('/')
    return f"collector_data('{folder}','{name}')"


LEFT = r"(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*"


def rewrite_code(text):
    used = set()

    def out_sub(m):
        s = m['s']
        if s not in SERIES:
            return m[0]
        used.add('series_path')
        return f"series_path('{s}')"
    # R/'output/history_x.json'   ROOT/'output/history_x.json'   root/'output/history_x.json'
    text = re.sub(rf"(?<![\w.]){LEFT}\s*/\s*'output/history_(?P<s>[a-z0-9_]+)\.json'", out_sub, text)
    # c.OUT/'history_x.json'   OUT/'history_x.json'   f.OUT/...
    text = re.sub(rf"(?<![\w.])(?:[A-Za-z_]\w*\.)*OUT\s*/\s*'history_(?P<s>[a-z0-9_]+)\.json'", out_sub, text)

    def data_sub(m):
        old = 'history_' + m['n']
        try:
            if (DATA[old] if old in DATA else data_new_path(old)) is None:
                return m[0]
        except KeyError:
            return m[0]
        used.add('collector_data')
        return data_call(old)
    # R/'data/history_x_y.json'   c.R/'data/...'   ROOT/'data/...'
    text = re.sub(rf"(?<![\w.]){LEFT}\s*/\s*'data/history_(?P<n>[a-z0-9_]+\.(?:json|csv))'", data_sub, text)
    # D/'history_x_y.json'
    text = re.sub(r"(?<![\w.])(?:[A-Za-z_]\w*\.)*D\s*/\s*'history_(?P<n>[a-z0-9_]+\.(?:json|csv))'", data_sub, text)
    return replace_text(text), used


def replace_text(text):
    """Remaining literal mentions (docstrings, comments, strings embedded in records): old name -> new relative path."""
    for old in sorted(DATA_OLD, key=len, reverse=True):
        new = DATA[old]
        if new is None:
            continue
        if old == 'history_cases.json':
            text = text.replace('data/history_cases.json', 'data/' + new)
            continue
        text = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])", new, text)
    for s in sorted(SERIES, key=len, reverse=True):
        old = f'history_{s}.json'
        text = re.sub(rf"(?<![A-Za-z0-9_/]){re.escape(old)}(?![A-Za-z0-9_])", 'history/' + SERIES[s].removeprefix('history/'), text)
        text = re.sub(rf"output/{re.escape(old)}(?![A-Za-z0-9_])", 'output/' + SERIES[s], text)
    for old, new in OUTPUT_EXTRA.items():
        text = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])", new, text)
    return text


IMPORT = 'from lib.paths import {}\n'


def add_import(text, names):
    lines = text.split('\n')
    # insert after the bootstrap line if present, else before the first import
    for i, l in enumerate(lines[:12]):
        if 'sys.path.insert(0' in l:
            at = i + 1
            break
    else:
        at = next(i for i, l in enumerate(lines) if re.match(r'(import|from) ', l))
    lines.insert(at, IMPORT.format(', '.join(sorted(names))).rstrip('\n'))
    return '\n'.join(lines)


def main():
    mode, root = sys.argv[1], Path(sys.argv[2])
    changed = []
    if mode == 'code':
        files = [*root.joinpath('scripts').rglob('*.py'), *root.joinpath('tests').glob('*.py'), *root.joinpath('tests').glob('*.mjs')]
        for f in sorted(files):
            if '/lib/paths.py' in str(f):
                continue
            t = f.read_text()
            n, used = (rewrite_code(t) if f.suffix == '.py' else (replace_text(t), set()))
            if n != t:
                if used:
                    n = add_import(n, used)
                f.write_text(n)
                changed.append(str(f.relative_to(root)))
    else:
        files = [root / 'README.md', root / 'uat.md', root / 'issues.md', *root.joinpath('docs').glob('*.md')]
        for f in files:
            if not f.exists() or 'refactor-tools' in str(f) or f.name == 'plan-collector-layout.md':
                continue
            t = f.read_text(); n = replace_text(t)
            if n != t:
                f.write_text(n); changed.append(str(f.relative_to(root)))
    print(len(changed), 'files changed')
    print('\n'.join(changed))


if __name__ == '__main__':
    main()
