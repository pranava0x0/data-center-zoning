# Data center zoning and telecom rights-of-way

**[Live atlas](https://pranava0x0.github.io/data-center-zoning/)** · [Downloads and coverage](https://pranava0x0.github.io/data-center-zoning/downloads.html) · [Virginia telecom pilot](https://pranava0x0.github.io/data-center-zoning/#view=telecom&state=VA) · [November 18 release review](docs/2026-11-18-telecom-pages-release.md)

Data centers and the Virginia fiber/telecom ROW pilot are separate collections. National completeness is unknown. The site states measured evidence coverage with its denominator. `make site` builds the public artifact from committed snapshots without the research cache; `make verify` runs the full research and browser gate with the cache. GitHub Actions validates exports and the browser journeys before publishing Pages.

**[Open the atlas](viewer/index.html)** · [Federal permit history](viewer/federal.html) · [Leading counties and cities by state](docs/national-progress.md) · [Local permit follow-up queue](output/priority_local_backlog.csv) · [Evidence receipts](docs/evidence-receipts.md) · [Release checks](docs/release-checks.md) · Permit history: [Virginia](viewer/index.html#state=VA&view=permits), [Ohio](viewer/index.html#state=OH&view=permits), [Texas](viewer/index.html#state=TX&view=permits), [Arizona](viewer/index.html#state=AZ&view=permits), [Indiana](viewer/index.html#state=IN&view=permits) · [All history records (CSV)](output/permit_history.csv)

Open or copy `viewer/index.html` by itself. It contains the map (with Alaska, Hawaii and the territories as insets), ordinances, permit history and supporting record fields. Each tab starts with totals by topic across the selected places. Map totals distinguish ordinance provisions, permits the issuer lists as active, and permits known to have ended. Records without confirmed permit status are listed separately. Government source links need an internet connection.

The [national directory](viewer/coverage.html) includes all 50 states, DC and the five inhabited territories. [State-by-state checks](output/compass_crosscheck.json) show where we have ordinance or permit evidence through November 15, 2026. The directory separates geographic coverage from evidence: it includes jurisdictions with no accessible register. Every card names the approval or record, then the issuer or deciding office and when ([audit of how many records can say so](docs/card-identity-audit.md); [review queue](output/card_identity_review.csv)). Permit cards carry the issuer’s file number, action date and source. The [federal guide](docs/federal-permits.md) distinguishes a permit from a consultation or a stayed decision. The atlas is independent of NLR; a map count cannot establish whether a parcel qualifies.

| Start here | What you get |
|---|---|
| [Published records](output/published.csv) · [All research rows](output/rules.json) · [Held evidence](output/holds.csv) | Cited provisions; conditions, source status, effective dates where known, and byte-level checks. Holds are excluded by default. |
| [Live edition counts and checks](output/validation.json) · [Worklist](output/worklist.csv) · [GIS export](output/jurisdictions.geojson) | Coverage versus findings. A researched county is not necessarily researched for every topic. |
| [Permit-history sources, limits and replication](docs/permit-history.md) | Separate registers for agency actions, local permits, and case decisions. |
| [How COMPASS works](docs/compass.md) · [Dataset and publication inventory](data/compass_sources.json) · [Reproduced counts](output/compass_audit.json) | The five technology releases, original research, early manual collections, documented software modules, and the crosswalk to data centers. |
| [Virginia field guide](docs/virginia.md) · [Statewide sweep dispositions](docs/sweep-review.md) | Loudoun zoning vintages, permits, agency layers, and how the directory search produced and rejected new findings. |
| [Expansion guide and rankings](docs/expansion.md) · [State priority table](data/state_priority.csv) · [Additional city and county checks](docs/local-checks.md) | Operating, under-construction and planned counts; capacity scenarios; local examples and counterexamples. |
| [Schema and collection protocol](docs/schema.md) · [Capacity, storage and token estimates](docs/scale.md) | Reproduction, audit rules, measurements and transparent expansion assumptions. |

**Three readings that change the answer.** In Loudoun, [Phase 1](https://www.loudoun.gov/6221/Phase-1-Project-Plan-for-Data-Center-Sta) changed named industrial districts to special exception, but ordinance vintage, approved applications and town limits matter. In Henrico's [Ordinance 1343](https://henrico.gov/pdfs/planning/Ord-1343-6-10-2025.pdf), the table’s “P” indicates a **provisional use permit**; do not translate it to “permitted by right.” In [Spotsylvania](https://www.spotsylvania.va.us/m/faq?cat=75), a data center discharging to the county sanitary sewer needs an industrial pretreatment permit. That is separate from a zoning classification, direct water withdrawal, construction runoff, or a reclaimed-water service allocation.

**Expansion order.** The [national queue](data/national/priority.csv) ranks all states with a reported count. The original ten-state [queue](output/worklist.csv) follows **combined facility/project counts** across operating, under-construction and planned stages in the [October 2026 directory](https://dcmap.us/states/), with Virginia/Loudoun first: VA, TX, OH, AZ, IN, TN, NV, MS, then LA and NM tied. No government census of the combined pipeline is asserted. [EPRI's published capacity scenarios](https://powering-intelligence.epri.com/nominal-capacity.html) offer a separate, reproducible power-based order; they include cryptocurrency mining and do not promise that every announced project will operate. The [forecast queue](output/worklist_forecast.csv) and [reported-power queue](output/worklist_power.csv) preserve these distinctions.

## Run it

Python 3.9+; `pypdf` for PDFs. The evidence cache (`cache/`, about 10 GB) is not in git: restore it with `make cache-restore BUNDLE=…` (create one with `make cache-pack DEST=…`) before rebuilding offline; without it, `make refresh-XX` re-downloads a jurisdiction's sources. For a fresh environment, run the following **inside this folder**. A checkout with the included snapshots can rebuild offline. The build gate requires Chrome or Chromium and Node 22+ with built-in WebSocket support.

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-research.txt
make verify
python3 scripts/pipeline/compass_audit.py
```

`make verify` rebuilds without contacting publishers, reruns the seven numeric recipes, verifies the priority table, checks source/claim drift behavior, geographic joins, scanned-page attribution and Virginia sweep hashes. `python3 scripts/pipeline/build.py --strict` additionally exits nonzero if **any** research record is held; those holds are expected and listed. `CHROME_PATH` may point to a different Chrome executable. See [UAT budgets and journeys](uat.md), [browser results](output/uat.json), and [COMPASS validation](docs/compass-crosswalk.md). Run `make uat` after UI-only edits or `make history` to replay the registered source collectors and rebuild the site. To check or refresh a single state or territory, run `make check-TX` or `make refresh-TX` (any code from `make jurisdictions`); see [per-jurisdiction refresh](docs/jurisdiction-refresh.md) and [how the collectors share code](docs/jurisdiction-components.md).

## Collect another jurisdiction

1. Pick a work item. Confirm the issuing body and its official website; for a town or utility, do not assume the surrounding county's code applies. Add a verified landing page with state, jurisdiction, GEOID where available, and URL in [seeds.json](data/seeds.json). For a yet-unseeded state/locality the [Census + CISA worklist](data/jurisdictions.csv) provides starting points, not a definitive inventory of authority.
2. Run bounded discovery and inspect its output. For example:
   ```sh
   python3 scripts/lib/discovery.py discover --state VA --geoid 51107 --budget 8
   python3 scripts/lib/discovery.py discover --state TX --budget 20
   ```
   Results include source text offsets, snippets, same-host documents and external code-publisher leads. Virginia's separate directory-wide adapter runs with `python3 scripts/ordinances/discovery/virginia_directory_sweep.py`; this is a shallow screen, not a legal review. Ordinary cached reads are deterministic. Add `--offline` to replay a discovery run from the available cache only, or `--refresh` to the relevant live collector to recheck.
3. Read the primary instrument and disposition. Preserve district, comparison, unit, measurement period, exceptions and project stage. Add a stable rule in an appropriate research input, and a linked pathway if supported. For a new research input, register the file name in `collect.rules()`. Use new IDs for genuinely different provisions; don't create a duplicate for the same ordinance appearing at a second URL.
4. Run `python3 scripts/ordinances/discovery/fetch_sources.py --state VA` (substitute state), inspect the cached bytes and source status, then `python3 scripts/pipeline/build.py --seal-new` and `make verify`. New pins are a deliberate review step. The build **never reseals** an altered claim or silently substitutes a different source. To release an amendment, document the change, archive the previous edition, retire its pin after review, then seal the new version. See [data model](docs/schema.md). Do not run two live collectors against the same source index at once.
5. To regenerate geographical inputs or rankings: `python3 scripts/pipeline/geography.py`; `python3 scripts/pipeline/rank_states.py`; `python3 scripts/pipeline/worklist.py --basis forecast` (or `power`). `python3 scripts/pipeline/compass_audit.py --fetch` downloads missing original NLR workbooks/search CSVs and checks their pinned hashes. Full upstream GIS products are linked, not bundled.

## What remains open

Start from [held records](output/holds.csv) and [candidate dispositions](docs/sweep-review.md). Some code publishers disallow automated retrieval; do not turn a rejected request into a no-rule finding. A successful text match checks a passage and immutable bytes, not repeal, current enforcement, or completeness. Temporal pauses, grandfathering, annexations and parcel entitlements warrant a fresh authority check. No general negative is published. Coverage is especially partial for townships outside the sample, special-purpose districts, tribal territories, water service areas and parcel-level overlays. The next defensible scale test is an independent, stratified review of both positives and apparent negatives before extending the same rules nationally.

[Local government website search](docs/local-screen.md) · [How map counts work](docs/permit-status.md) · [Site writing and design checks](docs/site-copy.md)
