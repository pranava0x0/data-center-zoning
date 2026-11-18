# UAT baseline · November 15, 2026

Run `make uat` in this folder. `make build`, `make verify` and the offline source replay `make history` all run the same gate. A failure exits nonzero; the failing journey and completed checks are in [uat.json](output/uat.json). The last run’s [screenshots](uat-screenshots/) are replaced by the next run. Set `CHROME_PATH` if Chrome/Chromium is not in a default location; use Node 22 or later.

The atlas is a static page with the published state and territory permit registers and their supporting fields compressed inside index.html; a register is decoded only when opened. A legacy link to history.html opens the same page and retains the locality. The isolated-file test copies index.html to an otherwise empty directory and opens Botetourt’s permit cards and record details. The suite starts a loopback HTTP server on an unused port, disables the browser cache, uses an isolated profile, and also opens a file:// deep link. No external site has to be reachable to rebuild.

| From | Find or do | Allowed actions | Swipes | Internal navigations |
|---|---|---:|---:|---:|
| Home | First ordinance finding | 0 | 0 | 0 |
| Virginia | Botetourt: is the use permitted, and where? | 2 (open + choose locality) | 0 | 0 |
| A Botetourt card | Quoted evidence / official source | 1 each | 0 | 0 |
| Botetourt ordinances | County permit history | 1 | 0 | 0 |
| Loudoun history | Specific Belmont case and decision | 2 (focus + enter case number) | 0 | 0 |
| Desktop map | Name, ordinance coverage, and permit count | Hover or focus | 0 | 0 |
| Phone ordinances | Select Loudoun on the map and return to its records | 2 | 0 | 0 |
| Permit history | Change to another state and see first result | 2 | 0 | 0 |

From a fresh home view, finding Columbus permit **NEWC2203324** or Abilene site plan **SP-2026-18** must also take at most five actions (permit tab, state selection, search focus, text), no swipes and no page navigation. Arizona PMT26-09976 and Indiana 089-42502-00639 have the same budget. The tests check the case number and official host at all four sizes.

Selecting a government citation has one **external** navigation; the test intercepts activation and checks the destination rather than downloading the public site on every build. Selects use DOM selection and a change event with a two-action charge; typing uses Chrome input. Clicks check hit targets and the suite charges a swipe for each 75% of viewport height needed to reach the target. Results must be visible, not merely present in the document. Steps above are measured from the specified starting point; the setup for another county is not counted twice. These are automated interaction costs, not human usability scores.

The harness adapts the task-by-task action/swipe accounting from [SI Policy’s explorer](../SI%20Policy/explorer/uat.cjs) and viewport expectations from [FirstPassRx](../FirstPassRx/uat/interaction_budgets.json). The versioned [budgets](tests/uat-budgets.json) enforce cold load, search latency, first permit rendering, initial bytes and unexpected external requests. Timings are local Chrome measurements, not estimates of a mobile network or an upstream government portal.

Other checks cover the map legend, keyboard selection, town/county scope, all-state navigation, register/year/pathway filters, empty results, direct sources, open/closed evidence, lazy permit details, CSV filtering, pagination, mobile overflow, isolated-file loading and out-of-order view changes. The [data validation](docs/compass-crosswalk.md) runs independently. Viewports: 1320×900, 768×900, 390×844 and 360×740. See [resolved issues](issues.md).

The default is All states. Test the topic counts and filtering, visible place counts on the map, and one card per counted permit in the active/historical views.

National releases retain the original cold-ready, filter, local history, click and scroll limits. The standalone file includes every record and historical detail: its byte ceiling stays at 1.55 MB through 6,731 rows and increases by at most 150 bytes per additional row, with a 3.5 MB hard ceiling. Each viewport reports actual bytes, its calculated budget and cold-ready time. The separate national directory is tested over HTTP and from disk.

## Card identity and map insets · November 16, 2026

Every ordinance and permit-history card must show the approval or record name, then who issues or decides it, without expanding: the suite checks that every rendered card has a title above an issuer line and a closed disclosure. The four Fairfax cards are checked for their title, deciding office and the county's six-month estimate. Rule search finds a card by its official title or its issuer; history search finds an issuer-supplied document title and records by issuer. Alaska, Hawaii, Puerto Rico, the US Virgin Islands, Guam, the Northern Mariana Islands and American Samoa are drawn as insets on the national map in both the ordinance and permit views; at every viewport the test checks that each is inside the map, hovers to show its counts, uses the same color bin as any state, and selects by click and by keyboard. The old chips under the map are gone. [Card identity audit](docs/card-identity-audit.md).

## Telecom and public release · November 18, 2026

The suite adds the VDOT application deep link, technology isolation, separate counts for instruments/applications and actions, multi-locality deduplication, visible type filtering, filtered export authority and hash fields, map print controls, PDF generation and isolated-file telecom loading at four widths. The existing cold-load, click and swipe budgets still apply. Representative screenshots are saved by default; set `ATLAS_ALL_SCREENSHOTS=1` to save every state/case screenshot. Public-download tests validate row counts, hashes, formula escaping, feature units, string GEOIDs, cross-table keys, ZIP round trips, static links and metadata.
