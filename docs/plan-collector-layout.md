# Proposed layout: collectors grouped by geography, shared code by format

Status (November 16, 2026): phases 1 to 5 done (phase 4 brief: docs/refactor-tools/phase4_brief.md). It extends the Codex handoff
[plan-permit-cards-and-telecom-rights-of-way.md](plan-permit-cards-and-telecom-rights-of-way.md) section 2 and the
existing [registry](../data/jurisdiction_registry.json).

## Why

Today 217 files sit flat in `scripts/`, and the names record the order work happened rather than what a file does.
About 110 imports cross jurisdictions: Colorado, Iowa, Maryland, Massachusetts, Nebraska, Utah and Wisconsin import
helpers from `history_mn.py` and `history_ms.py`; ten states import `history_nj_or_nc.py`; seven import a
text helper from `history_ca.py`; 23 `status_*.py` files import from `status_ms.py`. Several names refer to the
agent or batch that produced them (`*_astra`, `*_terra`, `westmetro`, `metropriority`). Changing one state's file
can change another state's output.

## Rules

1. **Collectors are grouped by geography, then by issuing jurisdiction, then by source:**
   `collectors/<state>/<jurisdiction or statewide>/<source>.py`, e.g. `collectors/virginia/loudoun_county/building_and_zoning_gis.py`.
   Federal agencies: `collectors/federal/<agency>_<register>.py`. Collectors that read one shared multi-state
   source (Legistar, CKAN catalogs, Accela case pages) live in `collectors/multistate/` and are named for that source.
2. **Shared code is named for its format, never for a state:** `lib/net.py` (HTTP), `lib/arcgis.py`,
   `lib/archive.py`, `lib/geo.py` (IM3 markers, Census places, point-in-polygon), `lib/epa_icis.py`,
   `lib/records.py` (record builder, `save`, `reconcile`), `lib/text.py` (HTML/PDF text), `lib/status.py`.
   A collector may import `lib/` only. Never another collector.
3. **Each state folder is self-contained:** its collectors, its `status.py`, and (phase 3) its config JSON. Removing a
   folder removes only that jurisdiction.
4. **Pipeline and ordinance research are separate trees:** `pipeline/` (build, export, validate, release) and
   `ordinances/` (`discovery/`, `codebooks/`, `compass/`, `rules/`).
5. **Old commands keep working during migration:** every moved file leaves a three-line shim at its old path that
   runs the new module, so the Makefile, registry, docs and the other session's notes stay valid until they are updated.

## Phases (each ends with `make check-all` and `python3 -m unittest`)

1. **Extract `lib/`**: move shared helpers out of `history_tx`, `history_oh`, `history_fl`, `history_mn`, `history_ms`,
   `history_ms_la_epa`, `history_nj_or_nc`, `history_ca`, `history_ia`, `history_ky` and `status_ms` into `lib/`. The
   old modules re-export them. Test: no collector imports another collector (static check added to the suite).
2. **Move files** per the table below, with shims; switch `scripts/` path roots to a single `lib.paths.ROOT` (many files
   use `Path(__file__).parents[1]`, which breaks one level deeper). Regenerate the registry with `jurisdiction.py trace`.
3. **Split mixed state files by issuer** (`all_sources.py` → e.g. `minnesota/statewide/eqb_reviews.py`,
   `minnesota/minneapolis/building_permits.py`, `minnesota/chaska/council_decisions.py`), and move each source's
   config next to it. Follow the Codex plan's rule that a statewide register serving many localities is fetched once.
4. **Rename data and output files** to match (`data/history_corpslibrary_oh.json` style names), behind a mapping
   so published URLs and CSV columns don't change.
5. Delete shims after the Makefile, registry, docs and tests point at the new paths.

## How to read the layout

- **One folder per jurisdiction.** States and territories never share a folder or import each other's code. The
  folder name is the jurisdiction whose permits it collects (`collectors/texas/`), not the agency that issued them.
- **One file per issuing source.** Inside a folder, each file is named for who issued the records and which register
  they come from: `texas/fort_worth_development_permits.py` (City of Fort Worth), `texas/tdlr_accessibility_registrations.py`
  (Texas Department of Licensing and Regulation). A state with a single issuing agency has a single source file, e.g.
  `vermont/anr_act250_docket.py`.
- **`history.py` is always the entry point.** It runs that folder's sources and writes the folder's published file,
  `output/history/<folder>/history.json`. Run `python3 scripts/collectors/<state>/history.py` (offline) or
  `make refresh-XX` (live).
- **`common.py` / `evidence_store.py`** hold helpers shared by sources in the same state only (one archive, one record
  numbering). Code shared across states lives in `scripts/lib/`.
- **Seven config-only states** (KY, ID, KS, MT, ND, SD, WY) list their sources in `data/history/<state>/config.json`;
  their `history.py` runs `lib/config_collector.py` over that file.
- **Not states:** `federal/` (one file per federal agency register, writing one output file per state),
  `multistate/` (one file per shared source type such as Legistar or CKAN catalogues), `territories/` (reviews that
  span AS, GU, MP, VI). Data and output files mirror these paths.

## Phase 1 result

`scripts/lib/` now holds the shared code, moved verbatim (outputs are byte-identical):

| Module | What it holds | Came from |
|---|---|---|
| `lib/paths.py` | `ROOT`, `R`, `D`, `OUT`, `CACHE` | per-file `Path(__file__).parents[1]` |
| `lib/net.py` | robots-aware GET/POST, sessions, streaming download, `req`, `get_simple`, `query` | `fetch.py`, `history_tx.req`, `history_mn.get/query` |
| `lib/arcgis.py` | `pull`, `records`, `oid_field`, `arcstore`, `snapshot` | `arcgis.py`, `history_fl.arcstore`, `history_mn.arc` |
| `lib/archive.py` | `Store` (content-addressed), `NamedArchive` (named files + sealed manifest) | `history_fl.Store`, `history_nj_or_nc.Archive` |
| `lib/geo.py` | Census place shapefiles, point-in-polygon, IM3 ranking, `PNNL`, `GAZ` | `history_tx`, `history_oh.pinring`, `history_fl.geofetch/rank` |
| `lib/text.py` | HTML/PDF text, date parsing, table parser | `history_tx`, `history_fl`, `history_ca`, `history_ia`, `history_mn`, `history_air`, `history_az` |
| `lib/terms.py` | data-center regexes and SQL predicates | `history_tx.MATCH/patterns`, `history_mn.EX/pred` |
| `lib/files.py` | `dump`, `sha`, `j`, `pack`, `unpack` | `history_tx`, `history_fl`, `history_mn` |
| `lib/records.py` | `rec`, `CUT`, `reconcile`, `save`, `reviewed`, `digest` | `history_mn`, `history_ms`, `history_ky` |
| `lib/epa_icis.py` | EPA ICIS-NPDES national archive, per-state slices, `state_rows` | `history_ms_la_epa` |
| `lib/config_collector.py` | config-only state collector (`run`, `cli`) | `history_ky` |
| `lib/status.py` | `day`, `det`, `epa` for `status_<st>.py` | `status_ms` |

84 files were repointed to `lib/`. The old modules re-export the moved names, and `fetch.py`, `arcgis.py` and
`history_ms_la_epa.py` are now aliases of their `lib/` modules, so existing commands and the registry still work.
`tests/test_lib_boundaries.py` fails if any script imports a shared helper from a collector, or if `lib/` imports
a collector. Same-state imports remain (Virginia's Loudoun files, New York's cases/council, Nebraska's ECM, Utah's
DAQ, Louisiana's quarterlies, New Mexico's water); phase 3 puts each group in its state folder.

## Phase 2 and 5 result

All 214 scripts moved to the table below; 4 compatibility modules were deleted (`fetch.py`, `arcgis.py`,
`history_ms_la_epa.py`, `history_nj_or_nc.py`). There are no shims: every import is dotted from `scripts/`
(`import collectors.virginia.statewide.deq_water_permits as water`). Each runnable file starts with a one-line
bootstrap that puts `scripts/` on the import path, so `python3 scripts/collectors/ohio/history.py` works from
anywhere. The Makefile, README, docs, `data/jurisdiction_registry.json`, the replay sample and the tests point at the
new paths; `permit_status.py` maps states to `collectors.<state>.status`. The OCR helper is `lib/ocr_vision.swift`;
the vendored copy checkers are `pipeline/copy_checks/` and `pipeline/tells/`.

Changes beyond the table: `iso`/`details` moved from `pipeline/permit_status.py` to `lib/status.py`; the EPA named
water collector is `collectors/federal/epa_named_water_permits.py` (with the EPA NPDES collectors that read it);
New Mexico's source list is `collectors/new_mexico/sources.py`. `tests/test_lib_boundaries.py` enforces the layout,
with four allowlisted cross-folder imports, each with a reason.

Verified: `make check-all` 55/55 byte-identical, 91 unit tests, `make build` (COMPASS, 5,499 UAT assertions,
1,093/1,093 receipts).

## Phase 3 pattern

A state's `all_sources.py` becomes one module per issuing source (e.g. `minnesota/eqb_environmental_reviews.py`,
`minnesota/minneapolis_building_permits.py`, `minnesota/chaska_council_decisions.py`), each exposing `download()`
(live) and `rows()` (offline), plus `minnesota/history.py`, which combines them and writes the unchanged series.
Output must stay byte-identical; the registry then lists the per-source modules.

## Phase 3 result

Every state folder now has `history.py` (entry point, same live flag as before) plus one module per issuing source,
e.g. `texas/fort_worth_development_permits.py`, `california/cec_small_power_plant_dockets.py`,
`louisiana/usace_vicksburg_regulatory_notices.py`. Where several sources share an archive or record numbering, a
folder-local `evidence_store.py` or `common.py` holds that state's helpers. Ohio, Puerto Rico and Oklahoma share one
build loop per state, which now lives in a folder-local `common.py` and dispatches to one module per issuer. States
with a single issuing agency have one issuer-named module (`district_of_columbia/dob_building_permits.py`,
`washington/ecology_quincy_air_dockets.py`, `pennsylvania/dep_data_center_permit_tracker.py`,
`west_virginia/wvdep_permit_records.py`, `vermont/anr_act250_docket.py`) and a one-line `history.py`. The seven config-only states (KY, ID, KS, MT, ND, SD, WY) keep a two-line
`history.py`. Each split was verified byte-identical with `docs/refactor-tools/verify_state.py`; then
`check --all` 55/55 and 91 tests. Live download code was moved but not run; several modules now fetch in a different
order (Alaska, Utah, Arkansas, New York, Michigan, Tennessee, California), and Michigan, Tennessee and Nevada re-sort
their manifests to keep the written files identical.

## Handoff (if this work resumes in a new session)

Phase 3 status is tracked by which `scripts/collectors/<state>/all_sources.py` files still exist
(`ls scripts/collectors/*/all_sources.py`). For each remaining state, follow `docs/refactor-tools/agent_brief.md`
(it points at the verifier, `docs/refactor-tools/verify_state.py <state>`, which must print PASS before
`all_sources.py` is deleted), then run `python3 docs/refactor-tools/rename_entry.py <state>` to repoint the Makefile,
registry, docs and tests at `history.py`. Finish with `make check-all`, `python3 -m unittest discover -s tests` and
`make build`.

## Phase 4 result

A file's path now names the collector that writes it. `docs/refactor-tools/phase4_moves.tsv` lists every move (old, new).

- Published series: `output/history_<series>.json` became `output/history/<collector path without .py>.json` (one series)
  or `output/history/<collector path without .py>/<state folder>.json` (a collector that writes one file per state), for
  example `output/history/texas/history.json` and `output/history/federal/faa_obstruction_evaluations/alabama.json`.
  `data/history/series.csv` gained a `path` column (relative to `output/`); the `series` key is unchanged.
- Each collector's inputs and by-products: `data/history_<x>_<kind>.<ext>` became `data/history/<collector folder>/<kind>.<ext>`
  (a state's `history.py` uses the state folder, e.g. `data/history/minnesota/validation.json`; any other collector uses its
  path without `.py`, e.g. `data/history/federal/usace_regulatory/queries.json`).
- Code resolves all of these through `scripts/lib/paths.py`: `series_path(series)`, `series_paths(prefix)`,
  `collector_data(folder, name)` and `state_folder(code)`. `lib.url_archive.Archive` and `lib.archive.NamedArchive` take an
  `owner` folder for their source manifests. `pipeline/register_release.py` takes `--path` for a new series.
- Left in place: `data/history/series.csv`, `data/history/pipeline/uat_cases.json` (pipeline-owned, read by the browser UAT),
  `data/history/federal/geo_sources.json` (shared by `federal/epa_npdes.py` and `pipeline/national_map.py`), and the
  pipeline's own receipts `output/history_evidence*.csv/json` and `output/receipts/materialization.json`.

## Live verification after the split (November 16, 2026)

`make refresh-XX` passed for UT, AR, NY (39 new records), MI, AK and TN, whose download order changed in the split.
Fixes found on the way: Alaska's public-notice server returns intermittent 403s, so `lib/net.py` retries a 403 once
after 5 s; the EPA ICIS slice metadata (`epa-source.json`) is now per-state, so splitting one state can't change
another's file (NV, NM and TN were re-pinned to the per-state form; the data slices were byte-identical); and
`refresh` now also stashes and restores cache files rewritten by shared prerequisites (`cache_globs` in the registry).
California is blocked by policy: data.sanjoseca.gov's robots.txt disallows `/api/` and `/datastore/`, which the San José
modules use. Its CKAN resource download links are allowed; switching to them is the fix.

## Also found while migrating

- DC's and North Carolina's GIS feeds renumber OBJECTIDs, so record links built from OBJECTID change on every
  refresh (18 DC rows, 78 NC rows). Build links from the permit number.
- AZ's Maricopa air layer intentionally queries `WHERE … IN (…)` instead of object-ID slices, because of a
  physical/virtual OID mismatch; it stays outside `arcgis.pull`.

## File-by-file mapping

| Current | Proposed |
|---|---|
| `alternate_published_rules.py` | `ordinances/codebooks/alternate_publishers.py` |
| `arcgis.py` | `lib/arcgis.py` |
| `audit_rules_terra.py` | `ordinances/rules/audit.py` |
| `build.py` | `pipeline/build.py` |
| `build_coverage.py` | `pipeline/build_coverage.py` |
| `build_history.py` | `pipeline/build_history.py` |
| `build_viewer.py` | `pipeline/build_viewer.py` |
| `case_timelines.py` | `pipeline/case_timelines.py` |
| `casebook.py` | `collectors/multistate/meeting_votes.py` |
| `catalog_permits.py` | `collectors/multistate/catalog_permits.py` |
| `census_screen_roster.py` | `ordinances/discovery/census_roster.py` |
| `check_pathway_links.py` | `pipeline/check_pathway_links.py` |
| `check_site_copy.py` | `pipeline/check_site_copy.py` |
| `codebook_measures.py` | `ordinances/codebooks/measures.py` |
| `codebook_ocr.py` | `ordinances/codebooks/ocr.py` |
| `codebook_rules_astra.py` | `ordinances/codebooks/rules.py` |
| `codebook_terms.py` | `ordinances/codebooks/terms.py` |
| `codebooks.py` | `ordinances/codebooks/inventory.py` |
| `collect.py` | `lib/discovery.py` |
| `compass_audit.py` | `pipeline/compass_audit.py` |
| `compass_code_sources.py` | `ordinances/compass/code_sources.py` |
| `compass_followups.py` | `ordinances/compass/followups.py` |
| `compass_taxonomy.py` | `pipeline/compass_taxonomy.py` |
| `council_history.py` | `collectors/multistate/legistar_matters.py` |
| `council_search.py` | `collectors/multistate/legistar_search.py` |
| `current_codebooks.py` | `ordinances/codebooks/current_editions.py` |
| `douglas_ga_rules.py` | `ordinances/rules/georgia_douglas_county.py` |
| `expand_rules_astra.py` | `ordinances/rules/national_rules_expansion.py` |
| `export_gis.py` | `pipeline/export_gis.py` |
| `export_permit_geography.py` | `pipeline/export_permit_geography.py` |
| `extract_values.py` | `ordinances/rules/extract_values.py` |
| `federal_air.py` | `collectors/federal/epa_air_cases.py` |
| `federal_aviation.py` | `collectors/federal/faa_obstruction_evaluations.py` |
| `federal_aviation_letters.py` | `collectors/federal/faa_letters_california_energy.py` |
| `federal_cases.py` | `collectors/federal/decisions.py` |
| `federal_consultations.py` | `collectors/federal/usace_consultations.py` |
| `federal_corps.py` | `collectors/federal/usace_regulatory.py` |
| `federal_corps_library.py` | `collectors/federal/usace_digital_library.py` |
| `federal_dashboard.py` | `collectors/federal/fast41_dashboard.py` |
| `federal_doe_more.py` | `collectors/federal/doe_nepa.py` |
| `federal_npdes.py` | `collectors/federal/epa_npdes.py` |
| `federal_power_cases.py` | `collectors/federal/ferc_orders.py` |
| `federal_water_discovery.py` | `collectors/federal/epa_npdes_discovery.py` |
| `federal_water_timeline.py` | `collectors/federal/epa_npdes_timeline.py` |
| `fetch.py` | `lib/net.py` |
| `fetch_batch.py` | `ordinances/discovery/fetch_sources.py` |
| `find_local_sites.py` | `ordinances/discovery/find_local_sites.py` |
| `geo_labels.py` | `lib/geo.py` |
| `geography.py` | `pipeline/geography.py` |
| `history_air.py` | `collectors/virginia/statewide/deq_air_permits.py` |
| `history_ak.py` | `collectors/alaska/history.py` (split by issuer later) |
| `history_al.py` | `collectors/alabama/history.py` (split by issuer later) |
| `history_ar.py` | `collectors/arkansas/history.py` (split by issuer later) |
| `history_az.py` | `collectors/arizona/history.py` (split by issuer later) |
| `history_ca.py` | `collectors/california/history.py` (split by issuer later) |
| `history_cases.py` | `collectors/multistate/accela_case_pages.py` |
| `history_catalog_csv.py` | `collectors/multistate/ckan_catalog_csv.py` |
| `history_co.py` | `collectors/colorado/history.py` (split by issuer later) |
| `history_ct.py` | `collectors/connecticut/history.py` (split by issuer later) |
| `history_dc.py` | `collectors/district_of_columbia/history.py` (split by issuer later) |
| `history_elkgrove.py` | `collectors/illinois/elk_grove_village_cook_assessor.py` |
| `history_evidence_receipts.py` | `pipeline/history_evidence_receipts.py` |
| `history_fairfax.py` | `collectors/virginia/fairfax_county/land_use_cases.py` |
| `history_federal_va_prior.py` | `collectors/federal/usace_virginia_prior_actions.py` |
| `history_fl.py` | `collectors/florida/history.py` (split by issuer later) |
| `history_ga.py` | `collectors/georgia/history.py` (split by issuer later) |
| `history_guref.py` | `collectors/guam/land_use_referrals.py` |
| `history_henrico.py` | `collectors/virginia/henrico_county/permits.py` |
| `history_hi.py` | `collectors/hawaii/history.py` (split by issuer later) |
| `history_ia.py` | `collectors/iowa/history.py` (split by issuer later) |
| `history_id.py` | `collectors/idaho/history.py` (split by issuer later) |
| `history_in.py` | `collectors/indiana/history.py` (split by issuer later) |
| `history_in_ocr.swift` | `collectors/indiana/ocr.swift` |
| `history_ks.py` | `collectors/kansas/history.py` (split by issuer later) |
| `history_ky.py` | `collectors/kentucky/history.py` (split by issuer later) |
| `history_la.py` | `collectors/louisiana/history.py` (split by issuer later) |
| `history_la_sources.py` | `collectors/louisiana/deq_quarterly_reports.py` |
| `history_loudoun.py` | `collectors/virginia/loudoun_county/building_and_zoning_gis.py` |
| `history_loudoun_supplement.py` | `collectors/virginia/loudoun_county/monthly_reports.py` |
| `history_ma.py` | `collectors/massachusetts/history.py` (split by issuer later) |
| `history_manassas_city.py` | `collectors/virginia/manassas/development_actions.py` |
| `history_materialization.py` | `pipeline/history_materialization.py` |
| `history_md.py` | `collectors/maryland/history.py` (split by issuer later) |
| `history_mi.py` | `collectors/michigan/history.py` (split by issuer later) |
| `history_mn.py` | `collectors/minnesota/history.py` (split by issuer later) |
| `history_ms.py` | `collectors/mississippi/history.py` (split by issuer later) |
| `history_ms_la_epa.py` | `lib/epa_icis.py` |
| `history_ms_la_rank.py` | `lib/geo.py` |
| `history_mt.py` | `collectors/montana/history.py` (split by issuer later) |
| `history_nc.py` | `collectors/north_carolina/history.py` (split by issuer later) |
| `history_nd.py` | `collectors/north_dakota/history.py` (split by issuer later) |
| `history_ne.py` | `collectors/nebraska/history.py` (split by issuer later) |
| `history_ne_ecm.py` | `collectors/nebraska/dwee_document_viewer.py` |
| `history_nj.py` | `collectors/new_jersey/history.py` (split by issuer later) |
| `history_nj_or_nc.py` | `lib/archive.py` (named store) + lib/geo.py (IM3 ranking) |
| `history_nm.py` | `collectors/new_mexico/history.py` (split by issuer later) |
| `history_nm_water.py` | `collectors/new_mexico/epa_construction_stormwater.py` |
| `history_nv.py` | `collectors/nevada/history.py` (split by issuer later) |
| `history_ny.py` | `collectors/new_york/history.py` (split by issuer later) |
| `history_ny_cases.py` | `collectors/new_york/decisions.py` |
| `history_ny_council.py` | `collectors/new_york/niagara_falls_council.py` |
| `history_oh.py` | `collectors/ohio/history.py` (split by issuer later) |
| `history_ok.py` | `collectors/oklahoma/history.py` (split by issuer later) |
| `history_or.py` | `collectors/oregon/history.py` (split by issuer later) |
| `history_pa.py` | `collectors/pennsylvania/history.py` (split by issuer later) |
| `history_pr.py` | `collectors/puerto_rico/history.py` (split by issuer later) |
| `history_sc.py` | `collectors/south_carolina/history.py` (split by issuer later) |
| `history_sd.py` | `collectors/south_dakota/history.py` (split by issuer later) |
| `history_territory_supp_fetch.py` | `collectors/territories/notice_indexes.py` |
| `history_tn.py` | `collectors/tennessee/history.py` (split by issuer later) |
| `history_tx.py` | `collectors/texas/history.py` (split by issuer later) |
| `history_ut.py` | `collectors/utah/history.py` (split by issuer later) |
| `history_ut_daq.py` | `collectors/utah/daq_submissions.py` |
| `history_vt.py` | `collectors/vermont/history.py` (split by issuer later) |
| `history_wa.py` | `collectors/washington/history.py` (split by issuer later) |
| `history_water.py` | `collectors/virginia/statewide/deq_water_permits.py` |
| `history_water_fire_cases.py` | `collectors/multistate/water_fire_authorizations.py` |
| `history_wi.py` | `collectors/wisconsin/history.py` (split by issuer later) |
| `history_wv.py` | `collectors/west_virginia/history.py` (split by issuer later) |
| `history_wy.py` | `collectors/wyoming/history.py` (split by issuer later) |
| `import_rule_sources.py` | `ordinances/rules/import_sources.py` |
| `jurisdiction.py` | `pipeline/jurisdiction.py` |
| `jurisdiction_sweep.py` | `ordinances/discovery/jurisdiction_sweep.py` |
| `large_rule_source.py` | `ordinances/codebooks/large_sources.py` |
| `local_register_audit.py` | `ordinances/discovery/local_register_audit.py` |
| `metropriority.py` | `collectors/ohio/central_ohio_entitlements.py` |
| `municipal_feeds.py` | `collectors/multistate/open_data_feeds.py` |
| `municipal_release.py` | `collectors/multistate/open_data_release.py` |
| `national_authorities.py` | `pipeline/national_authorities.py` |
| `national_frame.py` | `pipeline/national_frame.py` |
| `national_gate.py` | `pipeline/national_gate.py` |
| `national_geocheck.py` | `pipeline/national_geocheck.py` |
| `national_hotspots.py` | `pipeline/national_hotspots.py` |
| `national_local_screen.py` | `ordinances/discovery/national_local_screen.py` |
| `national_map.py` | `pipeline/national_map.py` |
| `national_permit_catalog.py` | `pipeline/national_permit_catalog.py` |
| `national_portals.py` | `pipeline/national_portals.py` |
| `national_rules_astra.py` | `ordinances/rules/national_rules.py` |
| `national_water.py` | `collectors/multistate/epa_named_water_permits.py` |
| `nm_sources.py` | `ordinances/rules/new_mexico_sources.py` |
| `ordinance_directory.py` | `ordinances/discovery/ordinance_directory.py` |
| `permit_archive.py` | `lib/archive.py` |
| `permit_status.py` | `pipeline/permit_status.py` |
| `project_scale.py` | `pipeline/project_scale.py` |
| `publish_codebook_rules.py` | `ordinances/codebooks/publish_rules.py` |
| `rank_states.py` | `pipeline/rank_states.py` |
| `register_release.py` | `pipeline/register_release.py` |
| `release_summary.py` | `pipeline/release_summary.py` |
| `replay_transfer_sample.py` | `pipeline/replay_transfer_sample.py` |
| `screen_indirect.py` | `ordinances/discovery/screen_indirect.py` |
| `screen_local.py` | `ordinances/discovery/screen_local_sites.py` |
| `screen_recall.py` | `pipeline/screen_recall.py` |
| `second_codebook_rules.py` | `ordinances/codebooks/second_pass_rules.py` |
| `state_construction_rules.py` | `ordinances/rules/state_construction_rules.py` |
| `state_scorecard.py` | `pipeline/state_scorecard.py` |
| `status_ak.py` | `collectors/alaska/status.py` |
| `status_al.py` | `collectors/alabama/status.py` |
| `status_ar.py` | `collectors/arkansas/status.py` |
| `status_ca.py` | `collectors/california/status.py` |
| `status_casebook.py` | `collectors/multistate/status_meeting_votes.py` |
| `status_co.py` | `collectors/colorado/status.py` |
| `status_ct.py` | `collectors/connecticut/status.py` |
| `status_dc.py` | `collectors/district_of_columbia/status.py` |
| `status_federal_corps.py` | `collectors/federal/status_usace.py` |
| `status_fl.py` | `collectors/florida/status.py` |
| `status_ga.py` | `collectors/georgia/status.py` |
| `status_guref.py` | `collectors/guam/status.py` |
| `status_hi.py` | `collectors/hawaii/status.py` |
| `status_ia.py` | `collectors/iowa/status.py` |
| `status_id.py` | `collectors/idaho/status.py` |
| `status_ks.py` | `collectors/kansas/status.py` |
| `status_ky.py` | `collectors/kentucky/status.py` |
| `status_la.py` | `collectors/louisiana/status.py` |
| `status_ma.py` | `collectors/massachusetts/status.py` |
| `status_md.py` | `collectors/maryland/status.py` |
| `status_mi.py` | `collectors/michigan/status.py` |
| `status_mn.py` | `collectors/minnesota/status.py` |
| `status_ms.py` | `collectors/mississippi/status.py + lib/status.py` (day, det, epa) |
| `status_mt.py` | `collectors/montana/status.py` |
| `status_nc.py` | `collectors/north_carolina/status.py` |
| `status_nd.py` | `collectors/north_dakota/status.py` |
| `status_ne.py` | `collectors/nebraska/status.py` |
| `status_nj.py` | `collectors/new_jersey/status.py` |
| `status_nm.py` | `collectors/new_mexico/status.py` |
| `status_nv.py` | `collectors/nevada/status.py` |
| `status_ny.py` | `collectors/new_york/status.py` |
| `status_ok.py` | `collectors/oklahoma/status.py` |
| `status_or.py` | `collectors/oregon/status.py` |
| `status_pa.py` | `collectors/pennsylvania/status.py` |
| `status_pr.py` | `collectors/puerto_rico/status.py` |
| `status_sc.py` | `collectors/south_carolina/status.py` |
| `status_sd.py` | `collectors/south_dakota/status.py` |
| `status_territory_grants.py` | `collectors/territories/status_grants.py` |
| `status_tn.py` | `collectors/tennessee/status.py` |
| `status_ut.py` | `collectors/utah/status.py` |
| `status_vt.py` | `collectors/vermont/status.py` |
| `status_wa.py` | `collectors/washington/status.py` |
| `status_westmetro.py` | `collectors/oregon/status_portland_west_metro.py` |
| `status_wi.py` | `collectors/wisconsin/status.py` |
| `status_wv.py` | `collectors/west_virginia/status.py` |
| `status_wy.py` | `collectors/wyoming/status.py` |
| `territory_case_screen.py` | `collectors/territories/case_screen.py` |
| `territory_grant_review.py` | `collectors/territories/federal_grants.py` |
| `territory_notice_ocr.py` | `collectors/territories/notice_ocr.py` |
| `territory_permit_screen.py` | `collectors/territories/permit_screen.py` |
| `territory_sources.py` | `collectors/territories/sources.py` |
| `township_rules.py` | `ordinances/rules/township_rules.py` |
| `township_screen_roster.py` | `ordinances/discovery/township_roster.py` |
| `tribal_screen.py` | `ordinances/discovery/tribal_screen.py` |
| `usage_snapshot.py` | `pipeline/usage_snapshot.py` |
| `va_sweep.py` | `ordinances/discovery/virginia_directory_sweep.py` |
| `validate_compass.py` | `pipeline/validate_compass.py` |
| `validate_federal.py` | `pipeline/validate_federal.py` |
| `validate_screen.py` | `pipeline/validate_screen.py` |
| `westmetro.py` | `collectors/oregon/portland_west_metro.py` (+ California part split out) |
| `westmetro_papa.py` | `collectors/oregon/portland_west_metro_papa.py` |
| `westmetro_portland.py` | `collectors/oregon/portland_maps.py` |
| `worklist.py` | `pipeline/worklist.py` |
