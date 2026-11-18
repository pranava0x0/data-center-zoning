# Card identity audit

Every card shows the title of the approval or record, then the jurisdiction and the issuing or deciding office, then one short sentence. This page counts how many cards can say that from the recorded data, by source series. [Review queue](../output/card_identity_review.csv) lists each card whose issuing or deciding office is still unknown.

## How titles and offices are chosen

- **Official title**: the issuer's own document title when the register supplies one (`filing_title`, `document_label`, `document_title`); a file extension is dropped. File names such as Iowa DNR `19-A-481.pdf` and permittee names are not titles.
- **Type plus identifier**: the agency's record type and record number, for example "Building permit B2011476". Identifiers over 40 characters or containing " / " are agency file locators, not permit numbers, so those cards show the record type alone.
- **Office from the register**: the register's own issuer or authority field, the federal issuer, or an agency the register title names (`data/card_identity_datasets.tsv`). Abbreviations such as ADEM, NDEQ or KY DEP are expanded from `data/card_identity_state_agencies.tsv`.
- **Office from the record type**: when a register names no office, `data/card_identity_offices.tsv` maps the record type to the office the jurisdiction's own ordinance or agency page assigns it to, with the citation on the row. The `evidence` column says whether the cited page states the assignment or the row is inferred from the register's own publisher.
- **State agency for EPA-reported permits**: ICIS lists the issuing agency of state-issued NPDES records as blank, "State" or "STA" for many states. Those records take the state agency that runs the EPA-authorized NPDES program, per EPA's state program page.
- **Unresolved**: only the publisher is known. The card would show the publisher and the record is queued.

## Permit-history records (14,479)

| Source series | Records | Official title | Type + identifier | Type only | Named office | Unresolved |
|---|---:|---:|---:|---:|---:|---:|
| ia | 4,635 | 0 | 4,635 | 0 | 4,635 | 0 |
| loudoun | 1,933 | 0 | 1,933 | 0 | 1,933 | 0 |
| tx | 650 | 0 | 650 | 0 | 650 | 0 |
| faa_va | 515 | 0 | 515 | 0 | 515 | 0 |
| ny | 504 | 0 | 501 | 3 | 504 | 0 |
| in | 458 | 0 | 458 | 0 | 458 | 0 |
| water | 447 | 0 | 447 | 0 | 447 | 0 |
| az | 408 | 0 | 408 | 0 | 408 | 0 |
| ca | 403 | 32 | 371 | 0 | 403 | 0 |
| air | 229 | 0 | 229 | 0 | 229 | 0 |
| portal_il | 216 | 0 | 216 | 0 | 216 | 0 |
| faa_tx | 212 | 0 | 212 | 0 | 212 | 0 |
| faa_ga | 190 | 0 | 190 | 0 | 190 | 0 |
| ma | 154 | 0 | 153 | 1 | 154 | 0 |
| faa_il | 149 | 0 | 149 | 0 | 149 | 0 |
| oh | 141 | 0 | 141 | 0 | 141 | 0 |
| ne | 132 | 0 | 29 | 103 | 132 | 1 |
| westmetro_or | 130 | 0 | 130 | 0 | 130 | 0 |
| pa | 125 | 0 | 123 | 2 | 125 | 0 |
| nc | 120 | 0 | 120 | 0 | 120 | 0 |
| ga | 109 | 29 | 80 | 0 | 109 | 1 |
| faa_oh | 97 | 0 | 97 | 0 | 97 | 0 |
| pwc | 96 | 0 | 96 | 0 | 96 | 0 |
| wtr_tx | 95 | 0 | 95 | 0 | 95 | 0 |
| faa_az | 90 | 0 | 90 | 0 | 90 | 0 |
| building | 84 | 0 | 84 | 0 | 84 | 0 |
| faa_ca | 67 | 0 | 67 | 0 | 67 | 0 |
| ak | 65 | 0 | 22 | 43 | 65 | 0 |
| or | 65 | 0 | 36 | 29 | 65 | 0 |
| faa_ia | 62 | 0 | 62 | 0 | 62 | 0 |
| wi | 60 | 0 | 50 | 10 | 60 | 0 |
| faa_nv | 55 | 0 | 55 | 0 | 55 | 0 |
| fairfax_va | 53 | 0 | 53 | 0 | 53 | 0 |
| fcon_va | 52 | 0 | 52 | 0 | 52 | 0 |
| tn | 50 | 0 | 50 | 0 | 50 | 0 |
| co | 46 | 0 | 46 | 0 | 46 | 0 |
| corps_va | 46 | 0 | 46 | 0 | 46 | 0 |
| faa_ut | 46 | 0 | 46 | 0 | 46 | 0 |
| ut | 45 | 0 | 39 | 6 | 45 | 0 |
| nv | 42 | 0 | 42 | 0 | 42 | 0 |
| md | 40 | 0 | 39 | 1 | 40 | 0 |
| wa | 39 | 39 | 0 | 0 | 39 | 0 |
| mn | 38 | 0 | 38 | 0 | 38 | 0 |
| ok | 38 | 0 | 38 | 0 | 38 | 0 |
| faaletters_ca | 38 | 0 | 38 | 0 | 38 | 0 |
| waterfire_va | 37 | 0 | 37 | 0 | 37 | 0 |
| nm | 33 | 0 | 33 | 0 | 33 | 0 |
| pr | 33 | 0 | 33 | 0 | 33 | 0 |
| fl | 31 | 0 | 31 | 0 | 31 | 5 |
| ms | 30 | 0 | 30 | 0 | 30 | 0 |
| al | 28 | 0 | 28 | 0 | 28 | 0 |
| nj | 28 | 0 | 28 | 0 | 28 | 0 |
| faa_or | 28 | 0 | 28 | 0 | 28 | 0 |
| wtr_ga | 27 | 0 | 27 | 0 | 27 | 0 |
| wtr_il | 24 | 0 | 24 | 0 | 24 | 0 |
| la | 24 | 0 | 24 | 0 | 24 | 0 |
| ar | 23 | 0 | 23 | 0 | 23 | 2 |
| portal_wa | 23 | 0 | 23 | 0 | 23 | 0 |
| fcon_ga | 21 | 0 | 21 | 0 | 21 | 0 |
| wtr_co | 19 | 0 | 19 | 0 | 19 | 0 |
| dc | 18 | 0 | 18 | 0 | 18 | 18 |
| corps_ga | 17 | 0 | 17 | 0 | 17 | 0 |
| mi | 17 | 0 | 17 | 0 | 17 | 0 |
| wtr_ut | 17 | 0 | 17 | 0 | 17 | 0 |
| wtr_or | 17 | 0 | 17 | 0 | 17 | 0 |
| faa_mo | 15 | 0 | 15 | 0 | 15 | 0 |
| sc | 15 | 0 | 15 | 0 | 15 | 0 |
| wtr_ca | 15 | 0 | 15 | 0 | 15 | 0 |
| fcon_or | 15 | 0 | 15 | 0 | 15 | 0 |
| faa_wa | 14 | 0 | 14 | 0 | 14 | 0 |
| faa_md | 14 | 0 | 14 | 0 | 14 | 0 |
| wv | 13 | 0 | 12 | 1 | 13 | 0 |
| cases | 13 | 0 | 11 | 2 | 13 | 10 |
| waterfire_ca | 13 | 0 | 13 | 0 | 13 | 0 |
| wtr_al | 12 | 0 | 12 | 0 | 12 | 0 |
| faa_mn | 12 | 0 | 12 | 0 | 12 | 0 |
| wy | 11 | 0 | 9 | 2 | 11 | 7 |
| faa_co | 11 | 0 | 11 | 0 | 11 | 0 |
| faa_ne | 11 | 0 | 11 | 0 | 11 | 0 |
| wtr_fl | 11 | 0 | 11 | 0 | 11 | 0 |
| nd | 11 | 0 | 11 | 0 | 11 | 2 |
| portal_md | 11 | 0 | 11 | 0 | 11 | 0 |
| henrico_va | 10 | 0 | 10 | 0 | 10 | 0 |
| corps_oh | 10 | 0 | 10 | 0 | 10 | 0 |
| fast_oh | 10 | 0 | 9 | 1 | 10 | 0 |
| faa_ok | 10 | 0 | 10 | 0 | 10 | 0 |
| metropriority_oh | 10 | 0 | 10 | 0 | 10 | 0 |
| faa_nj | 10 | 0 | 10 | 0 | 10 | 0 |
| elkgrove_il | 10 | 0 | 10 | 0 | 10 | 1 |
| faa_wy | 10 | 0 | 10 | 0 | 10 | 0 |
| faa_al | 10 | 0 | 10 | 0 | 10 | 0 |
| fcon_nc | 10 | 0 | 10 | 0 | 10 | 0 |
| wtr_nc | 9 | 0 | 9 | 0 | 9 | 0 |
| mt | 9 | 0 | 8 | 1 | 9 | 0 |
| ks | 9 | 0 | 8 | 1 | 9 | 0 |
| wtr_nj | 9 | 0 | 9 | 0 | 9 | 0 |
| fast_va | 9 | 0 | 9 | 0 | 9 | 0 |
| corpsprior_va | 9 | 0 | 9 | 0 | 9 | 0 |
| waterfire_wa | 9 | 0 | 8 | 1 | 9 | 0 |
| wtr_wy | 9 | 0 | 9 | 0 | 9 | 0 |
| wtr_in | 8 | 0 | 8 | 0 | 8 | 0 |
| ky | 8 | 0 | 8 | 0 | 8 | 2 |
| ct | 8 | 0 | 8 | 0 | 8 | 0 |
| vt | 8 | 0 | 7 | 1 | 8 | 0 |
| faa_pa | 7 | 0 | 7 | 0 | 7 | 0 |
| manassascity_va | 7 | 0 | 0 | 7 | 7 | 0 |
| wtr_sc | 7 | 0 | 7 | 0 | 7 | 0 |
| council_nv | 7 | 0 | 7 | 0 | 7 | 6 |
| hi | 7 | 0 | 5 | 2 | 7 | 0 |
| corps_nc | 6 | 0 | 6 | 0 | 6 | 0 |
| faa_in | 6 | 0 | 6 | 0 | 6 | 0 |
| wtr_mo | 6 | 0 | 6 | 0 | 6 | 0 |
| faa_sc | 6 | 0 | 6 | 0 | 6 | 0 |
| waterfire_az | 6 | 0 | 6 | 0 | 6 | 0 |
| wtr_wa | 6 | 0 | 6 | 0 | 6 | 0 |
| faa_tn | 6 | 0 | 6 | 0 | 6 | 0 |
| id | 6 | 0 | 5 | 1 | 6 | 0 |
| wtr_mt | 6 | 0 | 6 | 0 | 6 | 0 |
| faa_mi | 5 | 0 | 5 | 0 | 5 | 0 |
| council_nh | 5 | 0 | 5 | 0 | 5 | 5 |
| case_fl | 5 | 0 | 5 | 0 | 5 | 0 |
| sd | 5 | 0 | 5 | 0 | 5 | 0 |
| corps_pa | 5 | 0 | 5 | 0 | 5 | 0 |
| corps_in | 5 | 0 | 5 | 0 | 5 | 0 |
| wtr_az | 5 | 0 | 5 | 0 | 5 | 0 |
| fcon_sc | 5 | 0 | 5 | 0 | 5 | 0 |
| doe_ky | 4 | 0 | 4 | 0 | 4 | 0 |
| faa_wi | 4 | 0 | 4 | 0 | 4 | 0 |
| corps_ok | 4 | 0 | 4 | 0 | 4 | 0 |
| faa_fl | 4 | 0 | 4 | 0 | 4 | 0 |
| edate_nm | 4 | 0 | 4 | 0 | 4 | 0 |
| corps_or | 4 | 0 | 4 | 0 | 4 | 0 |
| wtr_ia | 4 | 0 | 4 | 0 | 4 | 0 |
| federalair_nd | 4 | 0 | 4 | 0 | 4 | 0 |
| fcon_ne | 4 | 0 | 4 | 0 | 4 | 0 |
| wtr_ar | 4 | 0 | 4 | 0 | 4 | 0 |
| guref_gu | 4 | 0 | 4 | 0 | 4 | 0 |
| wtr_sd | 4 | 0 | 4 | 0 | 4 | 0 |
| portal_ma | 4 | 0 | 4 | 0 | 4 | 0 |
| fcon_ca | 4 | 0 | 4 | 0 | 4 | 0 |
| corps_wi | 3 | 0 | 3 | 0 | 3 | 0 |
| fcon_la | 3 | 0 | 3 | 0 | 3 | 0 |
| fcon_in | 3 | 0 | 3 | 0 | 3 | 0 |
| faa_nm | 3 | 0 | 3 | 0 | 3 | 0 |
| portal_la | 3 | 0 | 3 | 0 | 3 | 0 |
| westmetro_ca | 3 | 0 | 1 | 2 | 3 | 2 |
| doe_oh | 3 | 0 | 3 | 0 | 3 | 0 |
| case_de | 3 | 0 | 3 | 0 | 3 | 0 |
| faa_nc | 3 | 0 | 3 | 0 | 3 | 0 |
| corps_sc | 3 | 0 | 3 | 0 | 3 | 0 |
| corps_ca | 3 | 0 | 3 | 0 | 3 | 0 |
| wtr_va | 3 | 0 | 3 | 0 | 3 | 0 |
| wtr_ne | 3 | 0 | 3 | 0 | 3 | 0 |
| case_ri | 3 | 0 | 3 | 0 | 3 | 0 |
| faa_ar | 2 | 0 | 2 | 0 | 2 | 0 |
| faa_ms | 2 | 0 | 2 | 0 | 2 | 0 |
| corps_la | 2 | 0 | 2 | 0 | 2 | 0 |
| land_nv | 2 | 0 | 2 | 0 | 2 | 0 |
| corps_nv | 2 | 0 | 2 | 0 | 2 | 0 |
| land_sc | 2 | 0 | 2 | 0 | 2 | 0 |
| corps_tx | 2 | 0 | 2 | 0 | 2 | 0 |
| corps_ks | 2 | 0 | 2 | 0 | 2 | 0 |
| waterfire_pa | 2 | 0 | 2 | 0 | 2 | 0 |
| faa_nd | 2 | 0 | 2 | 0 | 2 | 0 |
| corps_il | 2 | 0 | 2 | 0 | 2 | 0 |
| corpslibrary_oh | 2 | 0 | 2 | 0 | 2 | 0 |
| fpower_pa | 2 | 0 | 2 | 0 | 2 | 0 |
| wtr_ny | 2 | 0 | 2 | 0 | 2 | 0 |
| fed_gu | 2 | 0 | 2 | 0 | 2 | 0 |
| case_gu | 2 | 0 | 2 | 0 | 2 | 0 |
| council_tx | 2 | 0 | 2 | 0 | 2 | 0 |
| wtr_id | 2 | 0 | 2 | 0 | 2 | 0 |
| wtr_mi | 2 | 0 | 2 | 0 | 2 | 0 |
| wtr_ky | 2 | 0 | 2 | 0 | 2 | 0 |
| wtr_hi | 2 | 0 | 2 | 0 | 2 | 0 |
| corps_nd | 1 | 0 | 1 | 0 | 1 | 0 |
| land_va | 1 | 0 | 1 | 0 | 1 | 0 |
| corps_tn | 1 | 0 | 1 | 0 | 1 | 0 |
| waterfire_tx | 1 | 0 | 1 | 0 | 1 | 0 |
| corpslibrary_la | 1 | 0 | 1 | 0 | 1 | 0 |
| case_me | 1 | 0 | 1 | 0 | 1 | 0 |
| corpslibrary_or | 1 | 0 | 1 | 0 | 1 | 0 |
| edate_ok | 1 | 0 | 1 | 0 | 1 | 0 |
| case_pa | 1 | 0 | 1 | 0 | 1 | 0 |
| fed_ok | 1 | 0 | 1 | 0 | 1 | 0 |
| corps_ne | 1 | 0 | 1 | 0 | 1 | 0 |
| wtr_ks | 1 | 0 | 1 | 0 | 1 | 0 |
| edate_ma | 1 | 0 | 1 | 0 | 1 | 0 |
| edate_gu | 1 | 0 | 1 | 0 | 1 | 0 |
| corpslibrary_il | 1 | 0 | 1 | 0 | 1 | 0 |
| territorygrant_vi | 1 | 0 | 1 | 0 | 1 | 0 |
| fed_ma | 1 | 0 | 1 | 0 | 1 | 0 |
| territorygrant_as | 1 | 0 | 1 | 0 | 1 | 0 |
| edate_id | 1 | 0 | 1 | 0 | 1 | 0 |
| fed_id | 1 | 0 | 1 | 0 | 1 | 0 |
| doe_il | 1 | 0 | 1 | 0 | 1 | 0 |
| doe_id | 1 | 0 | 1 | 0 | 1 | 0 |
| doe_ca | 1 | 0 | 1 | 0 | 1 | 0 |
| corps_mn | 1 | 0 | 1 | 0 | 1 | 0 |
| faa_ky | 1 | 0 | 1 | 0 | 1 | 0 |
| **All** | **14,479** | **100** (0.7%) | **14,159** (97.8%) | **220** | **14,479** (100.0%) | **62** |

Official titles are rare because most registers publish a record type and number, not a document title. Type plus identifier is the intended fallback, not a defect.

### How each office was found

| Basis | Records |
|---|---:|
| The register title names the agency | 7,191 |
| The register names the issuer | 4,736 |
| Office derived from record type (data/card_identity_offices.tsv) | 2,308 |
| State agency from EPA's authorized program (data/card_identity_state_agencies.tsv) | 244 |

Registers whose office comes from the record type or the state program table (one row per register; each mapping and its citation is in the TSV):

| Register | Basis | Records |
|---|---|---:|
| Loudoun issued permits | Office derived from record type (data/card_identity_offices.tsv) | 1,373 |
| Loudoun land-use applications | Office derived from record type (data/card_identity_offices.tsv) | 536 |
| State-issued water permits reported to EPA | State agency from EPA's authorized program (data/card_identity_state_agencies.tsv) | 243 |
| Nebraska DWEE facility air files | Office derived from record type (data/card_identity_offices.tsv) | 124 |
| Loudoun monthly building reports | Office derived from record type (data/card_identity_offices.tsv) | 84 |
| Loudoun submitted permits | Office derived from record type (data/card_identity_offices.tsv) | 24 |
| District of Columbia building permit register | Office derived from record type (data/card_identity_offices.tsv) | 18 |
| Phoenix plan reviews | Office derived from record type (data/card_identity_offices.tsv) | 17 |
| County case files | Office derived from record type (data/card_identity_offices.tsv) | 13 |
| Municipal project planning dockets | Office derived from record type (data/card_identity_offices.tsv) | 11 |
| Albuquerque air quality notifications | Office derived from record type (data/card_identity_offices.tsv) | 10 |
| City of De Soto project and planning records | Office derived from record type (data/card_identity_offices.tsv) | 9 |
| Oklahoma DEQ permit applications | Office derived from record type (data/card_identity_offices.tsv) | 9 |
| Cook County assessor municipal permit register | Office derived from record type (data/card_identity_offices.tsv) | 9 |
| Douglas County Planning and Zoning agendas | Office derived from record type (data/card_identity_offices.tsv) | 6 |
| Palm Beach County Project Tango decisions | Office derived from record type (data/card_identity_offices.tsv) | 5 |
| Laramie County commissioners and planning commission | Office derived from record type (data/card_identity_offices.tsv) | 5 |
| Town of Eatonville council agendas | Office derived from record type (data/card_identity_offices.tsv) | 5 |
| Missoula County Bonner project review | Office derived from record type (data/card_identity_offices.tsv) | 5 |
| Louisville Metro development plans | Office derived from record type (data/card_identity_offices.tsv) | 5 |
| Saline Township land use proceedings | Office derived from record type (data/card_identity_offices.tsv) | 4 |
| City of Kuna planning and zoning cases | Office derived from record type (data/card_identity_offices.tsv) | 4 |
| Framingham building applications | Office derived from record type (data/card_identity_offices.tsv) | 4 |
| Municipal land-use case records | Office derived from record type (data/card_identity_offices.tsv) | 3 |
| Delaware Coastal Zone Act decisions | Office derived from record type (data/card_identity_offices.tsv) | 3 |
| Oregon land-use ordinance and review records | Office derived from record type (data/card_identity_offices.tsv) | 3 |
| Michigan air permits to install | Office derived from record type (data/card_identity_offices.tsv) | 3 |
| City of Cheyenne public planning cases | Office derived from record type (data/card_identity_offices.tsv) | 2 |
| City of Southfield site-plan review | Office derived from record type (data/card_identity_offices.tsv) | 2 |
| McPherson County conditional use proceedings | Office derived from record type (data/card_identity_offices.tsv) | 2 |
| North Dakota DEQ discharge permit notices | Office derived from record type (data/card_identity_offices.tsv) | 2 |
| Oldham County Project Lincoln withdrawals | Office derived from record type (data/card_identity_offices.tsv) | 2 |
| Arkansas DEQ other air requests | Office derived from record type (data/card_identity_offices.tsv) | 2 |
| City of South Fulton zoning information meeting | Office derived from record type (data/card_identity_offices.tsv) | 1 |
| Lincoln-Lancaster County air permits | Office derived from record type (data/card_identity_offices.tsv) | 1 |
| Elk Grove Village redevelopment resolutions | Office derived from record type (data/card_identity_offices.tsv) | 1 |
| Michigan EGLE air compliance inspections | Office derived from record type (data/card_identity_offices.tsv) | 1 |
| EPA ICIS-NPDES permit versions | State agency from EPA's authorized program (data/card_identity_state_agencies.tsv) | 1 |

Another 7,191 records come from registers whose title names the agency (`data/card_identity_datasets.tsv`).

## Ordinance rules (312)

Titles, offices and one-sentence summaries are in [data/card_identity_rules.tsv](../data/card_identity_rules.tsv). Each row carries the verbatim quote and the page that names the office (`role_quote`, `citation`). The four Fairfax cards come from [data/fairfax_card_evidence.json](../data/fairfax_card_evidence.json).

| What the office does | Rules |
|---|---:|
| Issues the permit | 75 |
| Decides the approval | 55 |
| Reviews | 1 |
| Adopted the standard | 123 |
| Adopted the provision | 58 |
| Not known | 0 |

Rules with no office: 0.

## Review queue

62 rows: 62 history records and 0 rules.

| Register (dataset) | Records | Publisher shown |
|---|---:|---|
| District of Columbia building permit register | 18 | District of Columbia Department of Buildings |
| Municipal project planning dockets | 6 | Clark County Board of County Commissioners |
| Municipal project planning dockets | 5 | Concord Planning Board |
| Town of Eatonville council agendas | 5 | Town of Eatonville Town Council |
| Laramie County commissioners and planning commission | 4 | Laramie County Board of Commissioners |
| County case files | 4 | Fairfax County Land Development Services |
| County case files | 3 | Fairfax County Board of Supervisors |
| County case files | 2 | Botetourt County Department of Community Development |
| City of Cheyenne public planning cases | 2 | City of Cheyenne Planning and Development Department |
| North Dakota DEQ discharge permit notices | 2 | North Dakota Department of Environmental Quality |
| Oldham County Project Lincoln withdrawals | 2 | Oldham County Board of Adjustment |
| Arkansas DEQ other air requests | 2 | Arkansas Division of Environmental Quality |
| Laramie County commissioners and planning commission | 1 | Laramie County Planning Commission |
| Municipal land-use case records | 1 | Sacramento County Planning Commission |
| City of South Fulton zoning information meeting | 1 | City of South Fulton Mayor and City Council |
| Municipal land-use case records | 1 | Hayward Planning Commission |
| Lincoln-Lancaster County air permits | 1 | Lincoln-Lancaster County Health Department |
| Elk Grove Village redevelopment resolutions | 1 | Village of Elk Grove Village President and Board of Trustees |
| County case files | 1 | Fairfax County Fire Marshal's Office |

## Fairfax fixtures

Claims on the four Fairfax cards were checked against the adopted text, the county process and acceptance pages, the noise instructions and the October 27, 2026 amendment. Corrections: the size-limit and setback clauses are on page 2 of the adopted PDF, not page 3; the noise instructions cite the clause as 4102.7.A(6), the later codified number; the 2026 amendment states no effective date, so its 100 MW noise-profile requirement is shown as separate detail and not applied to earlier approvals. See each `checks` entry in the fixture file.
