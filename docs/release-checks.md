# Atlas release checks · 2026-11-15

[Open the standalone atlas](../viewer/index.html) · [Federal records](../viewer/federal.html) · [Local follow-up queue](../output/priority_local_backlog.csv)

| What the atlas counts | Records |
|---|---:|
| Published rules and official permitting requirements | 312 |
| Ordinance candidates withheld from default results | 18 |
| Dated or explicitly undated project history records | 14,479 |
| Distinct permit keys | 5,654 (245 active, 1,895 historical, 3,514 current status unconfirmed) |
| Federal records already included in history | 2,034 |
| Distinct federal permit keys already included above | 45 |
| Saved checksums recomputed from local files | 1,093 of 1,093 |

The [COMPASS cross-check](../output/compass_crosscheck.json) reconciles 34,466 feature rows across five upstream releases. No history, facility or agency-action count should be read as the number of active data centers. [How a row is cited](evidence-receipts.md).

**Geographic limits.** The first pass reconciled 72,418 geographic entries and 91,811 government units across 50 states, DC and the five inhabited territories. Some are overlapping geographies, statistical places or special districts. 102 leading county, city or township entries have no matched action in our reviewed local registers. [State-by-state counts](national-progress.md) distinguish local provisions, statewide requirements and federal records.

**Browser results.** 5,633 passing assertions. Cold-open measurements are from local Chrome on the test machine, not cellular or production-network benchmarks. The single-file download was 2.43 MB. Tests also opened an isolated copy without its neighboring files.

| Viewport | Cold open | Filter change | Local history |
|---|---:|---:|---:|
| desktop | 543 ms | 8 ms | 229 ms |
| tablet | 493 ms | 4 ms | 201 ms |
| phone | 577 ms | 4 ms | 217 ms |
| small-phone | 569 ms | 5 ms | 213 ms |

| Task | Maximum actions / swipes / navigations across measured viewports |
|---|---:|
| Read first rule | 0 / 0 / 0 |
| Find the Botetourt zoning rule | 2 / 0 / 0 |
| Read cited evidence | 1 / 0 / 0 |
| Open the government source | 1 / 0 / 1 |
| Switch to local permit history | 1 / 0 / 0 |

[All browser journeys and measured interaction budgets](../output/uat.json) · [Repeat the build](../Makefile) · [Token and storage estimates](scale.md).
