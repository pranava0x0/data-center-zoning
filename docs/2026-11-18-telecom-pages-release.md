# Telecom pilot and GitHub Pages release · November 18, 2026

The data-center collection and Virginia fiber/telecom ROW pilot are separate collections in the atlas. GitHub repository: [data-center-zoning](https://github.com/pranava0x0/data-center-zoning). Public address: [atlas](https://pranava0x0.github.io/data-center-zoning/). Deployment status must be checked against the Actions run and the live-byte validation report; this document alone does not establish publication.

The pilot contains 14 requirements (12 Virginia regulations and two Fairfax agency guidance entries), 17 instruments/applications (five approved VDOT permits, 11 applications, one county easement authorization), 33 dated actions, and 17 agency-reported locations. No record establishes a data-center customer. No route geometry is inferred. Project identifiers remain null where a shared official project identity is unavailable.

## Evidence and scope

The archived VDOT search returned 163 Loudoun County and 125 Fairfax County matches for agency VDOT, application type Utility - Fiber Optic, without a date restriction. This batch reviews the newest ten Loudoun and five Fairfax details plus the independently selected Bolyn Road fixture. The search request, page length, response, retrieval time and raw detail bytes are committed under `data/telecom/`; it is a bounded sample, not a completed register. Agency categories include some coax and pole work; preserve the original category and work description. No candidate was promoted using a search-engine snippet.

VDOT application 949:61269 reports receipt August 21, 2025, determination/completion October 19, 2026, original target October 16, 2025, and a revised target November 18, 2026 in this snapshot. An approved record retains an in-progress information-request substep. The completion and target dates are separate fields; validity remains unconfirmed. Identical repeated timeline observations are deduplicated, while distinct starts remain separate events.

Fairfax's April 16 authorization to advertise and May 21 authorization to prepare and execute conveyance documents are two actions linked to one easement authorization. The original PDFs were read and the relevant pages rendered and visually inspected (April p. 30; May p. 36). Neither vote establishes a recorded deed or street-opening permit. Fairfax's UP guidance applies to county-controlled property/easements and qualifying ROW not accepted by VDOT; a Fairfax work address is not county issuance.

Leesburg's official page returned HTTP 403. Search-index text was a discovery lead only and was not published as a requirement or zero-result history. The Loudoun County-controlled process remains unreviewed. The registry retains these gaps. `python3 scripts/pipeline/jurisdiction.py telecom` replays the saved evidence twice without the network and verifies sibling data-center histories remain unchanged. Live source replacement still requires review and new archived receipts.

## Coverage measures

Data centers: **44/146 priority locality entries (30.1%)** have a matched action in a reviewed local register. The denominator excludes statistical places and preserves the original priority entries; it is not a count of unique governments or a measure of ordinance completeness. The other 102 entries remain on the follow-up queue.

Telecom: **2/4 pilot authorities (50%)** have directly archived and verified source checks: VDOT and Fairfax County. Leesburg is blocked and the county-controlled Loudoun process remains unreviewed. VDOT work in Loudoun is a separate observation. This does not mean half of Virginia permits or national telecom ordinances have been collected. National completeness is unknown for both technologies.

## Exports, reuse and publication

The site publishes CSV, JSON, GeoJSON and a deterministic ZIP, with schema version 1.0.0, per-file SHA-256 receipts, CSV row counts and a whole-archive checksum. Quantitative features are split by measurement; Fairfax's 200 ft building and 300 ft equipment setbacks retain one original rule ID and separate feature IDs. Agency guidance and project history stay outside the adopted-feature table. Instrument, event and location tables retain their links. GEOIDs remain strings. These are atlas extension tables, not a certified NLR release or tested direct COMPASS ingestion.

`make site` rebuilds from committed outputs, telecom evidence and the hash-pinned display geometry snapshot without the 10 GB research cache. The full `make verify` additionally requires the documented cache bundle, verifies archived ordinance evidence, numeric recipes, geographic joins, review pins, history receipts, taxonomy and browser journeys. CI gates Pages on export contracts, two isolated telecom replays and the browser suite. Public output is allowlisted; neither private session files nor the research cache enters the Pages artifact.

The site has canonical and social metadata, Dataset JSON-LD, static data-center and telecom indexes, a sitemap, robots.txt, llms.txt, and a no-JavaScript download path. These make the content accessible to crawlers; they do not promise search ranking or indexing. Print map / PDF preserves selected technology, scope, metric, vintage and coverage caveat. The PDF is generated by the browser without a map-service dependency.

## Accuracy and review passes

The data-center edition remains 312 published requirements and 18 holds, with 14,479 history events. Source integrity/passage/review-pin checks cover every published requirement; seven independent numeric extraction recipes are replayed. This is validation against saved evidence, not a fresh legal opinion or a claim that every source remains current. A separate numeric pass checked all 93 structured thresholds: 85 digit-presence matches, six written-number reviews and two scanned Fairview provisions re-rendered and visually inspected. See `output/ordinance_numeric_review.json`; numeric presence alone is not proof of a comparator or legal interpretation. Automated prose checks cover all 330 research summaries plus 14 telecom summaries and public card sentences; original government descriptions and quotations remain verbatim.

Corrections: the archived Fairfax amendment places the size clauses on **PDF page 3**, which has no printed page number. The earlier page-2 fixture/audit note was incorrect. The old records, source pins and pathway fingerprints are archived in `data/publication/fairfax-locator-corrections.json` before explicit resealing. Fairfax cards now expose the hearing process and six-month estimate. Edgewood names the council as ordinance-adopting authority and says its SUP decision-maker is unresolved. Inferred history office mappings are labeled and no longer certified as issuers; citations travel in both full and filtered exports.

Review pass 1 covered legal units, authority/location separation, table relationships, export integrity and browser behavior. Findings fixed: an inaccessible telecom type selector, a retained type filter hiding deep-linked applications, and an inferred office promoted to issuer.

Review pass 2 covered deployment isolation, fresh-checkout rebuilding, print output, reset behavior and unknown project identity. Findings fixed: a telecom reset selecting a data-center metric, the wrong technology heading and irrelevant inset note in the printed map, synthetic project IDs implying unsupported project relationships, and a map-joining assumption that would drop secondary locations. A multi-locality fixture now appears in each local view and counts once nationally. Tests cover these cases. Check the final release reports for measured results.

Small-phone review caught evidence requiring an extra swipe after the new navigation and coverage notice. The compact header keeps a linked coverage percentage and limitations visible; the full definition is on Downloads and in print. Print lives in the map controls. Interaction and performance budgets were retained. Browser runs retain representative screenshots by default; `ATLAS_ALL_SCREENSHOTS=1` captures every intermediate case.

## Measured local validation

112 Python tests and 5633 browser assertions passed across four viewports, HTTP and isolated file loading. All four browser receipts match the exact 2434320-byte packed build. No uncaught browser errors or external startup dependencies were observed. The focused smallest-phone evidence journey also passed 34 checks. Timings are local Chrome measurements, not a promise about cellular networks or government portals.

| Viewport | Cold ready (ms) | Filter (ms) | Local history (ms) |
|---|---:|---:|---:|
| desktop | 543 | 8 | 229 |
| tablet | 493 | 4 | 201 |
| phone | 577 | 4 | 217 |
| small-phone | 569 | 5 | 213 |

The first GitHub runner exposed a browser-harness setup assumption: the ignored cache directory did not exist on a fresh checkout. The harness now creates its temporary-profile parent directory itself. CI also requires browser receipts to match the exact packed-file byte size before publishing.

The GitHub review also found that the place directory expected data-center metric fields while telecom used distinct counting units. The directory and counting explanation now switch with the technology, and four-viewport regressions cover opening the directory and changing filters while it remains open.

The Linux runner measured a 2.55-second cold open against the unchanged 1.8-second budget. The startup geography and rules now use gzip/Pako rather than JavaScript LZMA decoding; deferred history bundles retain LZMA. The packed page remains under the unchanged edition byte ceiling.
