# Virginia ROW expansion · November 21, 2026

Prepared on the shared `codex/virginia-row-expansion` branch for one PR with Claude's data-center classifier work.

## Evidence added

- Loudoun: seven cable-franchise/construction requirements from Code §§805.03 and 805.08. County construction permits, VDOT permission and rights held by other utilities remain separate. These rules concern cable franchise grantees, not every telecom provider.
- Leesburg: Charter §3-3 permits a limited replacement-easement acquisition/exchange for adjacent or approximately adjacent replacement interests when the original utility property serves a public use. This does not establish a Town street-work permit or franchise process. The ROW page/manual still returns 403, including in an ordinary browser. A November 23 tentative zoning-rewrite adoption date is not treated as an adopted ordinance on November 21.
- Henrico, Lynchburg and Arlington: official ROW guidance, preserving bond-routing, franchise/license insurance exceptions, emergency procedures and separate transportation permit conditions.
- Richmond: official utility-cut permit and installation-path/traffic-plan guidance, preserving the government-own-crew exemption and emergency caveats.
- Virginia Beach: official Oceanfront/Sandbridge seasonal closure guidance, including the documented variance process.
- Claude's source batch: Virginia statutes, limited Ohio/Texas requirements, and 18 additional VDOT Prince William application pages. Filed Hanover proffers and the 2017 Texas enrolled act do not establish current adopted requirements.

The research table has 48 requirements: 42 published and 6 held. The instrument table has 35 instruments/applications; 60 dated actions are linked separately. No instrument establishes a data-center customer, a mapped fiber route or current permit validity.

## Coverage contract

The original Virginia pilot is 3/4 (75%) authority source reviews. Statewide source review is 9/323 (2.8%): a pinned 2022 Census roster of 322 general-purpose governments plus VDOT. This is not a current government census, ROW ownership inventory, complete code search or permit-history census. Leesburg remains partial. National completeness is unknown.

The full authority queue retains government identifiers as strings, blocked check IDs, source IDs and history-review limits. VDOT work in multiple counties counts as one authority. Ohio and Texas source reviews do not enter Virginia's numerator. [Authority frame](research/virginia-row-authority-frame-2026-11-21.md).

## Exports and review findings

Schema 1.1.0 separates full research, published requirements and held research. Adopted-feature export includes supported municipal ordinances/charters with their authority type, excludes guidance and holds, and retains the linked 60-day deadline and conditional 30-day extension as two rows. Source captures identify primary-publisher text extraction separately from raw HTTP archives.

Review round one found incomplete small-cell conditions, overbroad general-provider copy, a denominator that could include out-of-state authorities, and pending/denied land-use records labeled approvals. Review round two found public coverage-page links escaping the Pages artifact, collector imports crossing the lib boundary, event work descriptions overwriting agency step descriptions, and linkage prose implying verified source quotations from display fields. Subsequent record checks removed inferred nonissuance, bounded customer linkage and historical ownership to their archived sources, and labeled agency tracking dates separately from construction timing. Final reconciliation must retain these corrections.

The standalone payload excludes the unused detailed check array and full government queue; both remain downloadable. The 3.5 MB hard cap and latency budgets stay unchanged. Payload growth accounting includes embedded telecom rows as well as history rows.

Validation: final `make build` passed, including 132 Python tests, 5,654 browser assertions, offline loading and map PDF generation. A focused telecom pass separately passed 65 assertions. All source/numeric gates passed. GitHub checks and deployment remain the final release gates.

Automated PR review found three existing discretionary case records with unrecognized kind labels: Wyoming `Zone change LU to PUD` and two Kentucky `Land use application withdrawal` rows. Both kind variants now classify as land use while preserving the original statuses. New unit and exported-record regressions pass; the Python suite now has 134 checks. The focused telecom/PDF pass remains 65/65. Updated GitHub browser validation is required before merge.
