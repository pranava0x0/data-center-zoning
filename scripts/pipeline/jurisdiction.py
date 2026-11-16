"""One entrypoint to check or refresh any jurisdiction's permit history.

  python3 scripts/pipeline/jurisdiction.py list                 # every jurisdiction, its collectors, series and live flags
  python3 scripts/pipeline/jurisdiction.py check TX             # offline replay x2, byte-compare, schema + archive checks
  python3 scripts/pipeline/jurisdiction.py check --all
  python3 scripts/pipeline/jurisdiction.py refresh TX           # live pull with each collector's own flag, then `check`, then a row diff
  python3 scripts/pipeline/jurisdiction.py trace                # regenerate data/jurisdiction_registry.json from what collectors write

`check` blocks the network (proxy to a closed port), so a pass proves the edition rebuilds from cached bytes alone,
twice, to identical bytes, matching what is already published. `refresh` is the only mode that contacts publishers.
The registry is a reviewed config file: collectors, the series they write, their live flags and shared prerequisites.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from lib.paths import series_path

R = Path(__file__).resolve().parents[2]
REG = R / 'data/jurisdiction_registry.json'
OUT = R / 'output'
REQUIRED = ['id', 'dataset', 'jurisdiction', 'record_no', 'project', 'kind', 'status', 'date', 'date_role', 'url', 'locator']
OFFLINE_ENV = {k: 'http://127.0.0.1:9' for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy')}
OFFLINE_ENV.update(NO_PROXY='', no_proxy='')
NAMES = {}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def series_file(series):
    """Published path of a series, relative to the project root (e.g. output/history/texas/history.json)."""
    return str(series_path(series).relative_to(R))


def series_states():
    with (R / 'data/history/series.csv').open() as f:
        return {r['series']: r['state'] for r in csv.DictReader(f)}


def jurisdiction_names():
    if not NAMES:
        with (R / 'data/national/jurisdictions.csv').open() as f:
            for r in csv.DictReader(f):
                if r.get('layer') in ('states', 'state'):
                    NAMES[r['state']] = r['name']
    return NAMES


def makefile_collectors():
    """Collectors in `make history` order (the order matters: some read others' outputs)."""
    mk = (R / 'Makefile').read_text()
    body = mk.split('\nhistory:\n', 1)[1].split('\n\t$(MAKE) build', 1)[0]
    return re.findall(r'scripts/(\S+\.py)', body)


def live_flags(script):
    """Detect how a collector is told to contact publishers. Overrides in the registry win."""
    src = (R / 'scripts' / script).read_text()
    m = re.search(r"run_module\('([\w.]+)'", src)
    if m:  # a one-line entry that runs an issuer module: read that module's flags
        src = (R / 'scripts' / (m[1].replace('.', '/') + '.py')).read_text()
    if re.search(r"""['"]--refresh['"]""", src):
        return ['--refresh']
    if re.search(r"""['"]--fetch['"]""", src) or re.search(r'from (history_ky|lib\.config_collector) import .*\bcli\b', src):
        return ['--fetch']
    return []


def load():
    return json.loads(REG.read_text())


def run(script, args=(), offline=True, timeout=1800, refetch=False):
    env = dict(os.environ, **(OFFLINE_ENV if offline else {}))
    env.pop('ATLAS_REFETCH', None)
    if refetch:
        env['ATLAS_REFETCH'] = '1'
    t = time.time()
    p = subprocess.run([sys.executable, 'scripts/' + script, *args], cwd=R, env=env, capture_output=True, text=True, timeout=timeout)
    return p.returncode, round(time.time() - t, 1), (p.stderr or p.stdout)[-1500:]


def snapshot(watch=('output', 'data')):
    return {str(p.relative_to(R)): p.stat().st_mtime_ns for w in watch for p in (R / w).rglob('*') if p.is_file()}


# ---------------------------------------------------------------- registry

def build_registry(written):
    """written: {script: [relative paths it wrote]} -> registry dict (deterministic ordering)."""
    ss = series_states()
    old = load() if REG.exists() else {}
    overrides = old.get('overrides', {})
    collectors = {}
    for script in makefile_collectors():
        files = sorted(written.get(script, []))
        series = sorted(s for s in ss if series_file(s) in files)
        states = sorted({ss[s] for s in series})
        o = overrides.get(script, {})
        collectors[script] = dict(
            series=series,
            jurisdictions=states,
            scope='national' if len(states) > 3 else 'multi' if len(states) > 1 else 'single' if states else 'support',
            live=o.get('live', live_flags(script)),
            other_outputs=[f for f in files if f not in {series_file(s) for s in ss}],
        )
    by = defaultdict(lambda: dict(collectors=[], series=[]))
    for script, c in collectors.items():
        for st in c['jurisdictions']:
            by[st]['collectors'].append(script)
            by[st]['series'] += [s for s in c['series'] if ss[s] == st]
    for st in sorted(set(ss.values()) - {'state'}):
        by[st]['series'] = sorted(set(by[st]['series']))
        unowned = sorted(s for s, x in ss.items() if x == st and s not in by[st]['series'])
        if unowned:
            by[st]['series_without_collector'] = unowned
    return dict(
        note='Generated by scripts/pipeline/jurisdiction.py trace; edit `overrides`, `prerequisites` and `gaps` by hand.',
        overrides=overrides,
        prerequisites=old.get('prerequisites', {}),
        gaps=old.get('gaps', {}),
        collectors=collectors,
        jurisdictions={k: by[k] for k in sorted(by)},
    )


def cmd_trace(a):
    written = {}
    for script in makefile_collectors():
        before = snapshot()
        rc, secs, err = run(script)
        after = snapshot()
        written[script] = [k for k, v in after.items() if before.get(k) != v]
        print(f'{script:38} rc={rc} {secs:>6}s wrote {len(written[script])}', flush=True)
        if rc:
            print(err, file=sys.stderr)
    reg = build_registry(written)
    REG.write_text(json.dumps(reg, indent=2) + '\n')
    print('wrote', REG.relative_to(R))


# ---------------------------------------------------------------- list

def cmd_list(a):
    reg = load()
    names = jurisdiction_names()
    rows = []
    for st, j in reg['jurisdictions'].items():
        n = sum(len(json.loads(series_path(s).read_text())) for s in j['series'] if series_path(s).exists())
        own = [c for c in j['collectors'] if reg['collectors'][c]['scope'] in ('single', 'multi')]
        shared = [c for c in j['collectors'] if c not in own]
        live = sorted({f for c in j['collectors'] for f in reg['collectors'][c]['live']} or {'(none)'})
        own_s = ', '.join(c.removeprefix('collectors/').removesuffix('.py') for c in own) or '-'
        rows.append((st, names.get(st, st), n, len(j['series']), own_s if len(own_s) < 48 else own_s[:45] + '...', len(shared), ' '.join(live)))
    w = [max(len(str(r[i])) for r in rows) for i in range(7)]
    hdr = ('JUR', 'name', 'rows', 'series', 'own collectors', 'shared', 'live flag(s)')
    print('  '.join(h.ljust(w[i]) for i, h in enumerate(hdr)))
    for r in rows:
        print('  '.join(str(v).ljust(w[i]) for i, v in enumerate(r)))


# ---------------------------------------------------------------- check

def validate_series(series, state):
    """Schema and identity checks on one published series (mirrors build_history's gate, scoped)."""
    p = series_path(series)
    if not p.exists():
        return [f'{series}: missing output']
    rows = json.loads(p.read_text())
    errs = []
    if not isinstance(rows, list) or not rows:
        return [f'{series}: empty or not a list']
    ids = Counter(r.get('id') for r in rows)
    errs += [f'{series}: duplicate id {i}' for i, n in ids.items() if n > 1][:5]
    for r in rows:
        miss = [k for k in REQUIRED if k not in r]
        if miss:
            errs.append(f"{series}: {r.get('id')} missing {miss}")
            break
    for r in rows:
        d = r.get('date')
        if d and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(d)):
            errs.append(f"{series}: {r['id']} bad date {d!r}")
            break
        if d and d > '2026-11-15' and not r.get('details', {}).get('future_dated_ok'):
            pass  # cut-off is enforced inside each collector; refresh moves it deliberately
    st = {r.get('state') for r in rows if r.get('state')}
    if st and st - {state}:
        errs.append(f'{series}: rows tagged {sorted(st - {state})}, registry says {state}')
    return errs


def check_many(states, reg, verbose=True):
    """Replay the union of the jurisdictions' collectors (in `make history` order) twice, offline; judge each one."""
    ss = series_states()
    order = makefile_collectors()
    scripts = [c for c in order if any(c in reg['jurisdictions'][st]['collectors'] for st in states)]
    series = sorted({s for st in states for s in reg['jurisdictions'][st]['series']})
    targets = {s: series_path(s) for s in series}
    published = {s: sha(p) for s, p in targets.items()}
    failed, timing, hashes = {}, {}, []
    for attempt in (1, 2):
        for script in scripts:
            rc, secs, err = run(script)
            timing.setdefault(script, secs)
            if rc:
                tail = err.strip().splitlines()[-1] if err.strip() else str(rc)
                failed[script] = f'{script} failed offline (run {attempt}): {tail}'
        hashes.append({s: sha(p) for s, p in targets.items()})
        if failed:
            break
    results = []
    for st in states:
        j = reg['jurisdictions'][st]
        errs = [failed[c] for c in j['collectors'] if c in failed]
        drift = []
        if not errs and len(hashes) == 2:
            errs += [f'non-deterministic: {series_file(s)}' for s in j['series'] if hashes[0][s] != hashes[1][s]]
            drift = [series_file(s) for s in j['series'] if published[s] != hashes[-1][s]]
            for s in j['series']:
                errs += validate_series(s, ss[s])
        rows = sum(len(json.loads(targets[s].read_text())) for s in j['series'] if targets[s].exists())
        r = dict(jurisdiction=st, ok=not errs, rows=rows, errors=errs, drift_from_published=drift,
                 collectors=[dict(script=c, seconds=timing.get(c), ok=c not in failed) for c in j['collectors']],
                 series_sha256={series_file(s): hashes[-1][s] for s in j['series']})
        results.append(r)
        if verbose:
            print(f"{'PASS' if r['ok'] else 'FAIL'} {st}: {len(j['collectors'])} collectors, {len(j['series'])} series, {rows} rows"
                  + (f"; changed vs. published: {', '.join(drift)}" if drift else '; identical to published'))
            for e in errs:
                print('   ', e)
    return results


def check(st, reg, verbose=True):
    return check_many([st], reg, verbose)[0]


def cmd_check(a):
    reg = load()
    todo = sorted(reg['jurisdictions']) if a.all else [s.upper() for s in a.jurisdictions]
    bad = [s for s in todo if s not in reg['jurisdictions']]
    if bad:
        sys.exit(f'Unknown jurisdiction(s): {bad}. See `jurisdiction.py list`.')
    results = check_many(todo, reg)
    rc, _, err = run('pipeline/history_materialization.py', ['--strict'])
    if rc:
        print('FAIL archive receipts:', err.strip().splitlines()[-1])
    report = OUT / 'jurisdiction_checks.json'
    if a.all:
        json.dump(dict(results=results, archive_receipts_ok=rc == 0), report.open('w'), indent=2)
        report.write_text(report.read_text() + '\n')
    if rc or not all(r['ok'] for r in results):
        sys.exit(1)


# ---------------------------------------------------------------- refresh

def rows_by_id(series):
    out = {}
    for s in series:
        p = series_path(s)
        if p.exists():
            for r in json.loads(p.read_text()):
                out[r['id']] = r
    return out


def cmd_refresh(a):
    reg = load()
    st = a.jurisdiction.upper()
    j = reg['jurisdictions'][st]
    before = rows_by_id(j['series'])
    mine = {series_file(x) for x in j['series']}
    siblings_before = {series_file(s): sha(series_path(s)) for s in series_states() if series_file(s) not in mine}
    # Collectors also rewrite manifests under data/, so the whole published edition is stashed (~120 MB).
    stash = Path(tempfile.mkdtemp(prefix='refresh-' + st))
    for d in ('data', 'output'):
        shutil.copytree(R / d, stash / d)
    # Shared prerequisites rewrite cache files other jurisdictions replay from (e.g. EPA slices); stash those too.
    cached = sorted({q for pre in reg.get('prerequisites', {}).values() if st in pre['jurisdictions']
                     for g in pre.get('cache_globs', []) for q in R.glob(g)})
    for q in cached:
        (stash / q.relative_to(R)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(q, stash / q.relative_to(R))
    log = dict(jurisdiction=st, started_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'), steps=[])
    for name, pre in reg.get('prerequisites', {}).items():
        if st in pre['jurisdictions'] and not a.skip_prerequisites:
            for cmd in pre['commands']:
                rc, secs, err = run(cmd[0], cmd[1:], offline=False, refetch=not a.gap_fill_only)
                log['steps'].append(dict(step=f'prerequisite {name}: ' + ' '.join(cmd), rc=rc, seconds=secs, tail=err[-400:] if rc else ''))
    for script in j['collectors']:
        c = reg['collectors'][script]
        if c['scope'] == 'national' and not a.include_national:
            log['steps'].append(dict(step=script, skipped='national collector; pass --include-national (refreshes every state it covers)'))
            continue
        if not c['live']:
            log['steps'].append(dict(step=script, skipped='no live mode; inputs are hand-pinned (see registry overrides)'))
            continue
        rc, secs, err = run(script, c['live'], offline=False, refetch=not a.gap_fill_only)
        log['steps'].append(dict(step=script + ' ' + ' '.join(c['live']), rc=rc, seconds=secs, tail=err[-400:] if rc else ''))
    live_failed = [s['step'] for s in log['steps'] if s.get('rc')]
    touched = sorted(k for k, v in siblings_before.items() if sha(R / k) != v)
    log['other_jurisdictions_changed'] = touched
    if touched and not a.allow_sibling_writes:
        live_failed.append('changed other jurisdictions: ' + ', '.join(touched)
                           + ' (refresh those jurisdictions, or pass --allow-sibling-writes)')
    result = check(st, reg)
    log['check'] = result
    after = rows_by_id(j['series'])
    log['diff'] = dict(
        added=sorted(set(after) - set(before)),
        removed=sorted(set(before) - set(after)),
        changed=sorted(k for k in set(after) & set(before) if after[k] != before[k]),
    )
    ok = result['ok'] and not live_failed
    if not ok:
        for d in ('data', 'output'):
            shutil.rmtree(R / d)
            shutil.copytree(stash / d, R / d)
        for q in cached:
            shutil.copy2(stash / q.relative_to(R), q)
        log['restored_previous_edition'] = True
        log['live_failures'] = live_failed
        print('Refresh incomplete (' + ('; '.join(live_failed) or 'check failed') + '). Previous edition restored; '
              'the diff below is what the attempt produced. New cache bytes are kept for review.')
    result = dict(result, ok=ok)
    log['finished_utc'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    out = OUT / 'refresh' / f'{st}.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(log, indent=2) + '\n')
    d = log['diff']
    print(f"{st}: +{len(d['added'])} -{len(d['removed'])} ~{len(d['changed'])} rows. Log: {out.relative_to(R)}")
    print('Next: review the diff, then `make build` to republish (build re-runs every gate).')
    shutil.rmtree(stash, ignore_errors=True)
    sys.exit(0 if result['ok'] else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list').set_defaults(f=cmd_list)
    sub.add_parser('trace').set_defaults(f=cmd_trace)
    c = sub.add_parser('check'); c.add_argument('jurisdictions', nargs='*'); c.add_argument('--all', action='store_true'); c.set_defaults(f=cmd_check)
    r = sub.add_parser('refresh'); r.add_argument('jurisdiction')
    r.add_argument('--include-national', action='store_true', help='also run national collectors (FAA, Corps, EPA water...) live')
    r.add_argument('--skip-prerequisites', action='store_true', help='do not re-download shared inputs such as the EPA ICIS archive')
    r.add_argument('--allow-sibling-writes', action='store_true', help='accept changes a multi-state collector makes to other jurisdictions')
    r.add_argument('--gap-fill-only', action='store_true', help='only fetch sources not yet archived (old behavior); default re-pulls everything')
    r.set_defaults(f=cmd_refresh)
    a = ap.parse_args()
    if a.cmd == 'check' and not a.all and not a.jurisdictions:
        ap.error('check needs a jurisdiction code or --all')
    a.f(a)


if __name__ == '__main__':
    main()
