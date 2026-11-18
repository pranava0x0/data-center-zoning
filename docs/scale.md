# Measured pilot and scale estimates
At 2026-11-16T09:01:23+00:00, the four cooperating chats reported **662,338,306 input, including 654,105,088 cached; 1,509,710 output**. That leaves 8,233,218 uncached input. Repeated cached context explains the large gross number. This includes research, code, tool results and QA up to the recorded checkpoints; it excludes the final reply and is not a bill. See [per-role counters](../output/token_usage.json).

The deterministic collectors, extractors, ranker and viewer call **no model APIs**. A repeat against fixed inputs takes zero model tokens. Human or model review is still needed for new facts, amendments, scans, negatives and conflicting versions. Do not multiply the engineering session's gross token count by the number of states.

## Measurements
* The full working evidence cache currently contains 11.35 GB across 72,414 files, including history, nationwide searches and codebooks. These are logical file sizes; mirrored copies count once per file. The [breakdown](../output/scale.json) separates archives from the much smaller viewer and exports.
* 330 research rows, 207 unique archived source documents referenced by those rows, 360.64 MB of original curated source bytes. Median 201.4 kB; 90th percentile 3717.2 kB. Failed or blocked downloads contribute no source bytes and skew this sample.
* The Virginia first-pass archive used 84.7 MB to screen 324 directory entries; 249 returned a document. It includes home pages/local PDFs, not a full run through each code book. Discovery files can overlap curated sources; adding the two is not a distinct-document estimate.
* The expanded JSON export uses 2,322 bytes per row; the standalone atlas is 2.70 MB including permit records and map boundaries. Raw documents are stored separately and deduplicated by hash within each archive.
* [Census / registry provenance](../data/geography_sources.json) gives the 2025 frame. There are 7,302 rows in the ten states; 38,859 across the US frame. They are geography rows, not distinct lawmaking bodies. Consolidations, overlapping townships/places and independent cities require reconciliation, and utilities, tribal and federal authorities require additional rosters.

The nationwide frame now has 72,418 geographic features across 56 state/territory areas, plus 91,811 separate government roster entries. The standalone searchable roster uses 3.07 MB. 14,479 permit actions occupy 20.10 MB in CSV, or approximately 1,388 bytes per event; at the same mix, 100,000 actions would be about 138.8 MB, one million about 1.39 GB (CSV only). Signed PDFs, scans, historical versions and supporting documents are extra. Calculations for the full frame are sensitivity bounds, not a proposal to treat statistical geographies as legislatures.

## What a larger inventory might require
| Frame | Case | Geography rows | Provision rows | JSON export | Original document archive | Uncached input / output tokens |
|---|---|---:|---:|---:|---:|---:|
| Ten requested states | lean | 7,302 | 4,381 | 10.2 MB | 4.41 GB | 17.52M / 1.75M |
| Ten requested states | extended | 7,302 | 30,668 | 71.2 MB | 542.86 GB | 175.25M / 17.52M |
| US 50 states + DC pilot-layer definition | lean | 38,859 | 23,315 | 54.1 MB | 23.47 GB | 93.26M / 9.33M |
| US 50 states + DC pilot-layer definition | extended | 38,859 | 163,208 | 379.0 MB | 2,888.93 GB | 932.62M / 93.26M |
| Full Census geographic frame incl. territories | lean | 72,418 | 43,451 | 100.9 MB | 43.75 GB | 173.8M / 17.38M |
| Full Census geographic frame incl. territories | extended | 72,418 | 304,156 | 706.3 MB | 5,383.83 GB | 1,738.03M / 173.8M |

**Lean assumption:** 3 documents per geography at the measured median, one retained version; 12% produce 5 provisions; 20% of geography rows need one targeted 12k-input / 1.2k-output model review. **Extended:** 10 documents at the measured 90th percentile, two retained versions; 35% produce 12 provisions; 60% need a 40k-input / 4k-output review. All percentages, review budgets and hit rates are planning assumptions, not measured national prevalence or guaranteed recall. Input/output budgets are for a single collection pass; another full review cycle adds another pass. Storage uses decimal MB/GB and excludes full parcel/district geometry, rendered page images, indexes and backups. Code corpora or GIS history can substantially exceed these figures.

Equations: original bytes = geographies × documents × bytes per document × retained versions; rows = geographies × positive fraction × provisions per positive; tokens = geographies × reviewed fraction × tokens per review. Substitute local measurements in [the calculator](../scripts/project_scale.py) or [machine-readable scenarios](../output/scale.json). Fixed-source validation is cheap; recall and amendment review are the scaling constraints. Before funding a full pass, stratify by jurisdiction type and portal, hand-search a random sample of apparent negatives, then measure confidence intervals, review time and positive yield.
