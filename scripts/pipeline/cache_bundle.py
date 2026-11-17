"""Pack, restore and inventory the evidence cache, which git does not hold (about 10 GB).

    python3 scripts/pipeline/cache_bundle.py inventory          # writes cache/INVENTORY.tsv: path, bytes, sha256
    python3 scripts/pipeline/cache_bundle.py pack DEST_DIR      # cache-<date>.tar + its inventory, for any storage
    python3 scripts/pipeline/cache_bundle.py restore BUNDLE.tar # unpacks into cache/ and re-verifies every file

A fresh clone can rebuild offline once the cache is restored; `make check-all` then proves every series replays
byte-for-byte. Files are already gzip-compressed, so the bundle is an uncompressed tar.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, hashlib, tarfile
from datetime import date
from pathlib import Path
from lib.paths import ROOT

CACHE = ROOT / 'cache'
INV = CACHE / 'INVENTORY.tsv'
SKIP = ('chrome-test-',)


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def files():
    for p in sorted(CACHE.rglob('*')):
        rel = p.relative_to(CACHE)
        if p.is_file() and p != INV and not any(part.startswith(SKIP) for part in rel.parts) and not p.name.endswith('.part'):
            yield p, rel


def inventory():
    rows = [f'{rel}\t{p.stat().st_size}\t{sha(p)}' for p, rel in files()]
    INV.write_text('path\tbytes\tsha256\n' + '\n'.join(rows) + '\n')
    print(len(rows), 'files,', sum(int(r.split('\t')[1]) for r in rows) // 2**20, 'MiB ->', INV.relative_to(ROOT))


def pack(dest):
    inventory()
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True)
    out = dest / f'cache-{date.today().isoformat()}.tar'
    with tarfile.open(out, 'w') as t:
        t.add(INV, arcname='INVENTORY.tsv')
        for p, rel in files():
            t.add(p, arcname=str(rel))
    (dest / (out.stem + '.INVENTORY.tsv')).write_text(INV.read_text())
    print('wrote', out, out.stat().st_size // 2**20, 'MiB')


def restore(bundle):
    with tarfile.open(bundle) as t:
        for m in t.getmembers():
            target = (CACHE / m.name).resolve()
            if CACHE.resolve() not in target.parents or not (m.isfile() or m.isdir()):
                sys.exit('Refusing unsafe member: ' + m.name)
        t.extractall(CACHE)
    bad = []
    for line in INV.read_text().splitlines()[1:]:
        rel, n, h = line.split('\t')
        p = CACHE / rel
        if not p.exists() or p.stat().st_size != int(n) or sha(p) != h:
            bad.append(rel)
    print('restored;', 'all files verified' if not bad else f'{len(bad)} files differ: {bad[:5]}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['inventory', 'pack', 'restore'])
    ap.add_argument('path', nargs='?')
    a = ap.parse_args()
    if a.cmd in ('pack', 'restore') and not a.path:
        ap.error(a.cmd + ' needs a path')
    {'inventory': lambda: inventory(), 'pack': lambda: pack(a.path), 'restore': lambda: restore(a.path)}[a.cmd]()
