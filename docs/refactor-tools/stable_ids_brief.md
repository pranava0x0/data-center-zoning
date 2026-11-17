# Make record IDs, links and locators independent of portal row numbers

Project: /Users/pranava/Projects/local ordinance zoning (git repo; commit nothing). Read docs/plan-collector-layout.md
("How to read the layout"). Another agent is fixing other series in other folders at the same time; edit only the
collector files that write your series (find them in data/jurisdiction_registry.json or by grepping the dataset name).

Problem: GIS/open-data portals renumber internal row ids (ArcGIS OBJECTID, Socrata :id/src_row_id/row-xxxx) when they
republish, so a refresh rewrites links/IDs with no real change. Reference fixes already done:
scripts/collectors/district_of_columbia/dob_building_permits.py, scripts/collectors/north_carolina/ (Durham, Raleigh),
scripts/collectors/california/ladbs_building_permits.py and sfdbi_building_permits.py.

Rule for every record you touch:
- `id`: built only from the issuer's identifier (permit/case/application/GIS asset number). If one identifier has
  several rows, add a stable field of the row (status, issue date, DBI-style record id), never a portal row id.
- `url`: a stable link on the same official host for that identifier, e.g. ArcGIS
  `<layer>/query?where=<FIELD>%3D'<value>'&outFields=*&f=html` (match the existing f= style if the link is JSON),
  Socrata `<dataset>.json?<field>=<value>`, or the issuer's own permit page if the record already links one.
- `locator`: the identifier(s) only (e.g. `permit PB26-15093`, `Layer 312; SSWD-000071`). Move the row id to
  `details.portal_row_id_at_capture`.
- If a record has no identifier other than the portal row id, leave it and list it in your report.
- Change nothing else: same records, same count, same other fields. `source_url`/`source_sha256` describe the
  archived capture and may stay as they are unless they are themselves row-id links (then treat like `url`).

Verify (network blocked: HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9): run the collector's entry
(`python3 scripts/collectors/<state>/history.py`, or the collector file for federal/multistate/Virginia sources) twice;
output identical between runs, same record count as `git show HEAD:<output path>`, and differences vs HEAD only in
id/url/locator/details.portal_row_id_at_capture (check with a small diff script). If an ID changes, check nothing else
references the old ID (grep data/ and tests/). Then `python3 -m unittest discover -s tests`.

Report per series: scheme with one before→after example, records changed, records left with only a row id, and the
verification lines.
