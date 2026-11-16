"""Calculate the queue from original EPRI dashboard values and a dated count inventory.

Default: deterministic offline regeneration. --check: never write. --refresh:
download the specific 2026 edition's public display bundle from EPRI again.
A changed dashboard format fails explicitly; never execute downloaded JS.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse
import csv
import hashlib
import io
import re
import sys
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "cache/priority/epri-dashboard.js"
URL = "https://powering-intelligence.epri.com/assets/index.html-BnOKIAPk.js"
COUNTS = ROOT / "data/directory_counts_2026-10.csv"
OUT = ROOT / "data/state_priority.csv"
STATES = set("VA TX IN OH AZ NV MS TN LA NM".split())
COLUMNS = [f"epri_{yr}_{s}_mw" for yr in (2024,2030) for s in ("low","medium","high")]
# Explicit edition checksum makes drift visible. For a new edition verify new values and version the inputs first.
PIN = "716ba116e3f928abfa711e7cc655f8d009c3bea7f8d72e33d2c10adf84733fab"
def build(source):
    if hashlib.sha256(source).hexdigest() != PIN:
        raise ValueError("EPRI dashboard bundle changed: version and review before reranking")
    values = {s:{} for s in STATES}
    records = re.findall(rb'\{scenario:"(low|medium|high)",state:"([A-Z]{2})",year:(2024|2030),nominal_GW:([\d.]+),', source)
    for scenario,state,year,gw in records:
        s = state.decode()
        if s not in STATES: continue
        k = f"epri_{year.decode()}_{scenario.decode()}_mw"
        if k in values[s]: raise ValueError(f"duplicate {s} {k}")
        mw = Decimal(gw.decode()) * 1000
        if mw != int(mw): raise ValueError("review source unit precision")
        values[s][k] = int(mw)
    with COUNTS.open(newline='') as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != len(STATES) or {r['state'] for r in rows} != STATES: raise ValueError("state coverage drift")
    for r in rows:
        r.update(values[r['state']])
        if not all(k in r for k in COLUMNS): raise ValueError("EPRI data incomplete")
        for year in (2024,2030):
            lo,mid,hi = [r[f'epri_{year}_{s}_mw'] for s in ('low','medium','high')]
            if not 0<=lo<=mid<=hi: raise ValueError("scenario order")
        if sum(int(r[k]) for k in ('operating','under_construction','planned')) != int(r['total']): raise ValueError("count mismatch")
    for key,col in [('scenario_rank','epri_2030_medium_mw'),('count_rank','total'),('directory_power_rank','reported_power_gw')]:
        for r in rows:
            # Competition ranking: ties get the same rank, deterministic state code for display only.
            r[key] = 1 + sum(Decimal(str(o[col])) > Decimal(str(r[col])) for o in rows)
    dest=io.StringIO(newline='')
    w=csv.DictWriter(dest,fieldnames=['scenario_rank','state',*COLUMNS,'count_rank','operating','under_construction','planned','total','directory_power_rank','reported_power_gw'],lineterminator='\n')
    w.writeheader()
    w.writerows(sorted(rows,key=lambda r:(r['scenario_rank'],r['state'])))
    return dest.getvalue()

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--check',action='store_true');p.add_argument('--refresh',action='store_true'); args=p.parse_args()
    raw = urlopen(Request(URL, headers={'User-Agent':'OrdinanceAtlas/1.0 (public-source research)'}),timeout=30).read(5_000_000) if args.refresh else BUNDLE.read_bytes()
    content=build(raw)
    if args.check:
        if not OUT.exists() or content!=OUT.read_text(): sys.exit("ranking missing or stale")
        print("10-state queue matches pinned EPRI and directory inputs.")
    else:
        if args.refresh: BUNDLE.write_bytes(raw)
        OUT.write_text(content)
        print(f"Wrote {OUT.name}")
