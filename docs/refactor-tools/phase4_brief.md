# Phase 4: data and output files mirror the collector that writes them

Project: /Users/pranava/Projects/local ordinance zoning (not a git repo; nobody outside has seen it, so breaking old file
names is fine: no redirects or compatibility copies). Read docs/plan-collector-layout.md first. Code layout is final:
scripts/{lib,collectors,pipeline,ordinances}; collectors/<state>/history.py is each state's entry point, plus per-issuer
modules; collectors/{federal,multistate,territories}/<source>.py.

## The rule
A file's path tells you which collector produced it.

- Published series: `output/history_<series>.json` → `output/history/<collector path without .py>.json` for a
  single-jurisdiction collector, or `output/history/<collector path without .py>/<state folder>.json` for a collector
  that writes one file per state. Examples:
  - output/history_tx.json → output/history/texas/history.json
  - output/history_loudoun.json → output/history/virginia/loudoun_county/building_and_zoning_gis.json
  - output/history_faa_al.json → output/history/federal/faa_obstruction_evaluations/alabama.json
  - output/history_fcon_la.json → output/history/federal/usace_consultations/louisiana.json
  - output/history_case_fl.json → output/history/multistate/meeting_votes/florida.json
- Inputs and by-products under data/ that belong to one collector (`data/history_<x>_config.json`, `_manifest`,
  `_validation`, `_rank`, `_rankings.csv`, `_coverage`, `_sources`, `_review`, ...) → `data/history/<collector folder>/<kind>.<ext>`,
  e.g. data/history_mn_validation.json → data/history/minnesota/validation.json,
  data/history_corps_queries.json → data/history/federal/usace_regulatory/queries.json. Use the registry
  (data/jurisdiction_registry.json, `other_outputs`) and grep to find each file's writer and readers. Files read by
  several collectors or by the pipeline stay where they are unless one owner is obvious.
- Leave cache/ and the published aggregates (output/permit_history.csv, output/published.csv, viewer/, output/*.geojson,
  output/validation.json, etc.) where they are.

## Single source of truth
Replace the `series` naming with paths: extend data/history_series.csv with a `path` column (relative to output/), keep
the `series` key (the build and viewer use it as an identifier), and make every reader/writer resolve the file through
one helper in scripts/lib/paths.py (e.g. `series_path(series) -> Path`, `collector_data(folder, name) -> Path`). Update
every writer (collectors call `save`, `dump`, `collect.dump`, `R/'output/history_x.json'`, f-strings: find them all),
every reader (pipeline/build_history.py, history_evidence_receipts.py, history_materialization.py, jurisdiction.py,
replay_transfer_sample.py, state_scorecard, build_viewer, tests), the Makefile, README and docs links.

## Verify
1. Before changing anything: record `python3 scripts/pipeline/jurisdiction.py check --all` (expect 55 PASS) and the
   record count in output/permit_history_summary.json (14,441).
2. Move files with a script that also writes a mapping log (old → new) to docs/refactor-tools/phase4_moves.tsv.
3. After: `python3 scripts/pipeline/jurisdiction.py trace` (regenerates the registry: check it lists the new paths),
   `make check-all` (55 PASS, deterministic), `python3 -m unittest discover -s tests`, `make build` (COMPASS checks,
   browser UAT, 1093/1093 receipts). Row counts must be unchanged. Record contents may change only where a record
   embeds a moved data path; list every such field.
4. `ls output/history_*.json data/history_*` should return nothing that has a single owner.

Report: what moved (counts by area), files left in place and why, anything whose contents changed, and the final
verification output lines.
