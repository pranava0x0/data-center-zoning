"""Phase 4: move published series and collector data/by-product files to their collector-mirroring paths.

  python3 docs/refactor-tools/phase4_move.py            # dry run: print the plan
  python3 docs/refactor-tools/phase4_move.py --apply    # move files, add the `path` column to data/history_series.csv,
                                                        # write docs/refactor-tools/phase4_moves.tsv (old -> new)
"""
import csv, json, os, sys
from phase4_map import P, series_rows, series_new_paths, data_new_path, OUTPUT_EXTRA

apply = '--apply' in sys.argv
reg = json.loads((P / 'data/jurisdiction_registry.json').read_text())
sp = series_new_paths(reg)
moves = []  # (area, old, new) relative to project root
for r in series_rows():
    moves.append(('output series', f"output/history_{r['series']}.json", f"output/{sp[r['series']]}"))
for old, new in OUTPUT_EXTRA.items():
    moves.append(('output by-product', f'output/{old}', f'output/{new}'))
for n in sorted(os.listdir(P / 'data')):
    if n.startswith('history_') and n != 'history_series.csv':
        new = data_new_path(n)
        if new:
            moves.append(('data', f'data/{n}', f'data/{new}'))
olds, news = [m[1] for m in moves], [m[2] for m in moves]
assert len(set(news)) == len(news), 'destination collision'
for o in olds:
    assert (P / o).exists(), o
for n in news:
    assert not (P / n).exists(), n
print(len(moves), 'moves')
if not apply:
    for m in moves[:5] + moves[-5:]:
        print(*m, sep='\t')
    sys.exit()
for _, o, n in moves:
    (P / n).parent.mkdir(parents=True, exist_ok=True)
    os.rename(P / o, P / n)
rows = series_rows()
with (P / 'data/history_series.csv').open('w', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['series', 'state', 'path'])
    for r in rows:
        w.writerow([r['series'], r['state'], sp[r['series']]])
with (P / 'docs/refactor-tools/phase4_moves.tsv').open('w') as f:
    f.write('area\told\tnew\n')
    for m in moves:
        f.write('\t'.join(m) + '\n')
print('moved; wrote data/history_series.csv path column and docs/refactor-tools/phase4_moves.tsv')
