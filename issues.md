# UAT issues · November 15, 2026

| Issue | Evidence and resolution | Regression check |
|---|---|---|
| UAT-001 · Expanded filters displaced the result | In the supplied Botetourt screenshot the expanded filters occupied the space above the only card. A dismissible filter panel now applies a choice immediately; the finding and direct source stay on the card. | Filter dismissal, collapsed Botetourt finding and visible source in four viewports. |
| UAT-002 · The card title hid the decision | “Use permission” did not state whether a center could be built. The card now names Greenfield business park and says that county zoning allows data centers there and the separate town rules. | Two actions from Virginia; no disclosure or scrolling. |
| UAT-003 · The source passage fell below the first screen | During testing at 360×740, the quote still took a swipe after opening evidence. Put the quoted passage first and removed the repeated Botetourt summary. | Evidence fits after one click; see [small-phone evidence](uat-screenshots/small-phone-evidence.png). |
| UAT-004 · Permit history required leaving the ordinance view | Both modes now share place selection. Filtered history and links open in the same panel. Missing and slow state payloads support retry and cannot overwrite a newer selection. | County-to-history, data-request failure, late response, legacy deep link. |
| UAT-005 · Map colors lacked a definition | Each color has a permanent definition. Hover/focus reveals the place, checked ordinances and published history. A tap selects the place. | Pointer, keyboard, touch-sized layout and three coverage classes. |
| UAT-006 · A permit number also matched neighboring file descriptions | Searching the precise Columbus number NEWC2203324 returned related files that cited it. Exact file numbers now take precedence over keyword matches, while multiple actions on that exact number remain visible. | Named Ohio permit and multi-action Belmont case. |

Limits: tests use desktop Chromium with narrow viewport emulation, not physical-device Safari or a screen reader. Government registers have different search and time coverage; zero displayed records is not evidence that no permit exists. See the state coverage notes for source-side limitations.

**Follow-up fixes.** The desktop file preview could show ordinance cards but fail when it requested a second JavaScript file for permits. The delivered HTML now contains all its records; the browser suite opens Botetourt's history and individual permit fields without neighboring assets. The default tabs have clickable topic counts. No reader has to interpret a research status to understand a map color.

## November 18: telecom pilot and public release

Added a separate Virginia telecom dataset and public Pages build. Fixed unsupported Edgewood SUP approver attribution, labeled inferred history offices, corrected Fairfax PDF locators and exposed hearing/timing information. Two review passes caught telecom filter/reset state and PDF labeling errors; regression checks now cover them. Leesburg source access and county-controlled Loudoun ROW remain open; nationwide completeness remains unknown. See `docs/2026-11-18-telecom-pages-release.md`.
