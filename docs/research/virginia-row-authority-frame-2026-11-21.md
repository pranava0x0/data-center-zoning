# Virginia ROW authority frame · November 21, 2026

This release tracks a source-review queue. A reviewed page is not a completed ordinance search, permit-history census, or determination of who owns a particular road, pole, or easement.

The pinned Census 2022 government roster in `data/national/government_units.csv` contains 322 Virginia general-purpose governments: 95 counties, 38 cities, and 189 towns. Cities occur in the municipal group once; they are not added again as county equivalents. The statewide review baseline adds VDOT as a separate state agency, producing 323 entries. The exact source-file hash, selection and exclusions are in `data/telecom/codex-research/authority-frame.json`. Later government changes have not been reconciled. Census government identifiers are preserved as strings and are distinct from geographic GEOIDs.

The original pilot remains four authorities: VDOT, Fairfax County, Loudoun County, and the Town of Leesburg. VDOT's Loudoun and Fairfax samples are two work-location checks against one authority. Reviews in Ohio and Texas do not enter either Virginia numerator. A bare Fairfax name cannot merge Fairfax County with the independent City of Fairfax.

## Legal authority and work location

| Source | What it establishes | Limit retained |
|---|---|---|
| [Code of Virginia §56-462](https://law.lis.virginia.gov/vacode/title56/chapter15/section56-462/) | Municipal franchise authority for the covered wireline corporations; subsection D addresses permission for certificated telecommunications providers. | The 45-day decision provision applies to its stated provider class and permissions. It is not a universal deadline for all zoning, construction or wireless applications. |
| [§56-484.27](https://law.lis.virginia.gov/vacode/title56/chapter15.1/section56-484.27/) | Restrictions on local and VDOT treatment of wireless providers in public ROW. | A generally applicable, nondiscriminatory requirement and a wireless-specific prohibition must not be summarized as the same rule. |
| [§56-484.28](https://law.lis.virginia.gov/vacode/title56/chapter15.1/section56-484.28/) | Distinct VDOT and local wireless ROW provisions, including existing-structure permission and defined permit exceptions. | A districtwide co-location permission is not ownership of a pole or a blanket authorization for excavation, lane closure or new structures. Preserve each subsection's conditions. |
| [VDOT guide for Arlington and Henrico](https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/guide-for-county-road-systems-in-arlington-and-henrico-counties/) | VDOT describes these counties' local-road responsibilities separately from the primary and interstate systems. | A county work address alone does not establish the controller of the particular road. This guide is a lead until an archived primary capture is linked to a published claim. |
| [Loudoun Code §805.03](https://codelibrary.amlegal.com/codes/loudouncounty/latest/loudounco_va/0-0-0-3181) and [§805.08](https://codelibrary.amlegal.com/codes/loudouncounty/latest/loudounco_va/0-0-0-3326) | Cable-franchise and construction requirements, including county permits and separate VDOT permission. | The cable-franchise grant does not authorize other services. The ordinance does not turn every county street into county-controlled ROW. Primary-publisher extracted text and native HTTP failures are separate research receipts. |
| [Leesburg ROW process](https://www.leesburgva.gov/departments/public-works/traffic-management-services/right-of-way-permits) | Discovery lead for Town-controlled ROW permits. | Native requests remain blocked. Search-index text alone must not become a verified requirement. |
| [Leesburg DCSM](https://online.encodeplus.com/regs/leesburg-va-dcsm/doc-viewer.aspx?secid=99) versus [DCSM Update](https://online.encodeplus.com/regs/leesburg-va-dcsm-update/doc-viewer.aspx?secid=645) | Separate published-manual and update-draft locations. | The update labels its content as draft. The published page currently yields a JavaScript shell to the text retriever; neither shell nor search extract is a verified legal passage. |
| [Leesburg zoning rewrite](https://www.leesburgva.gov/departments/community-development/current-department-projects/zoning-ordinance-rewrite/-toggle-allupcoming) | The official project page lists tentative adoption on November 23, 2026. | November 21 precedes that date. Do not promote a draft, commission recommendation, or tentative Council schedule as adoption. |

The authority table leaves road ownership unconfirmed unless a record-specific primary source establishes it. County-controlled property and franchises can require local review even when VDOT controls the road. Utility pole permission, easement rights, zoning permission, street-work permits and service franchises remain separate questions.

## Coverage contract

Only a coverage row marked verified and linked to a retrieved, hashed primary-source archive can count toward source review. Blocked pages and unsearched registers remain explicit. One primary review can advance the source-review queue while its history remains a bounded sample or unsearched.

The full 323-entry authority queue belongs in downloadable tables. Only the small summary enters the standalone viewer. Federal agencies, tribal authorities, private owners, railroads and utilities are outside this government baseline. National completeness remains unknown.

## Additional city guidance captured

Richmond’s [ROW guide](https://www.rva.gov/public-works/right-way-management) supplies utility-cut permit and installation-path/traffic-plan requirements, including government-own-crew and emergency caveats. Virginia Beach’s [ROW guide](https://planning.virginiabeach.gov/permits/right-of-way) supplies the Oceanfront/Sandbridge seasonal closure policy and its documented variance process. Both are archived raw HTML guidance, not adopted-code captures, and remain outside the adopted-feature table. No permit history census is claimed. With these source reviews, Virginia is 9/323 (2.8%); the original pilot remains 3/4 (75%).
