PYTHON ?= python3
.DEFAULT_GOAL := build
.PHONY: build verify uat history collect geography discover-va replay-sample jurisdictions check-all
# Every published site build goes through data checks and browser journeys.
build:
	$(PYTHON) scripts/collectors/virginia/statewide/telecom_right_of_way.py
	$(PYTHON) scripts/ordinances/discovery/screen_local_sites.py
	$(PYTHON) scripts/pipeline/validate_screen.py
	$(PYTHON) scripts/ordinances/codebooks/current_editions.py
	$(PYTHON) scripts/ordinances/rules/township_rules.py
	$(PYTHON) scripts/ordinances/rules/georgia_douglas_county.py
	$(PYTHON) scripts/ordinances/codebooks/second_pass_rules.py
	$(PYTHON) scripts/ordinances/codebooks/alternate_publishers.py
	$(PYTHON) scripts/ordinances/codebooks/publish_rules.py
	$(PYTHON) scripts/ordinances/compass/code_sources.py --reuse-export --screen --claims
	$(PYTHON) scripts/ordinances/codebooks/ocr.py --verify
	$(PYTHON) scripts/ordinances/rules/import_sources.py
	$(PYTHON) scripts/pipeline/build.py
	$(PYTHON) scripts/pipeline/check_pathway_links.py
	$(PYTHON) scripts/ordinances/discovery/screen_indirect.py
	$(PYTHON) scripts/ordinances/rules/extract_values.py
	$(PYTHON) scripts/pipeline/worklist.py
	$(PYTHON) scripts/pipeline/worklist.py --basis forecast
	$(PYTHON) scripts/pipeline/worklist.py --basis power
	$(PYTHON) scripts/pipeline/export_gis.py
	$(PYTHON) scripts/pipeline/build_history.py
	$(PYTHON) scripts/pipeline/history_evidence_receipts.py
	$(PYTHON) scripts/pipeline/history_materialization.py --strict
	$(PYTHON) scripts/pipeline/export_permit_geography.py
	$(PYTHON) scripts/pipeline/card_identity_audit.py
	$(PYTHON) scripts/pipeline/check_site_copy.py
	$(PYTHON) scripts/pipeline/audit_descriptions.py
	$(PYTHON) scripts/ordinances/discovery/national_local_screen.py
	$(PYTHON) scripts/pipeline/national_geocheck.py
	$(PYTHON) scripts/pipeline/national_gate.py
	$(PYTHON) scripts/pipeline/validate_federal.py
	$(PYTHON) scripts/pipeline/screen_recall.py
	$(PYTHON) scripts/pipeline/state_scorecard.py
	$(PYTHON) scripts/pipeline/build_coverage.py
	$(PYTHON) scripts/pipeline/build_viewer.py
	$(PYTHON) scripts/pipeline/project_scale.py
	$(PYTHON) scripts/pipeline/validate_compass.py --strict-taxonomy
	$(PYTHON) scripts/pipeline/rank_states.py --check
	$(PYTHON) scripts/pipeline/publish_site.py
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) -m unittest discover -s tests -p test_publication.py
	$(MAKE) uat
verify: build
uat:
	node tests/viewer.mjs
	$(PYTHON) scripts/pipeline/release_summary.py
history:
	$(PYTHON) scripts/collectors/virginia/loudoun_county/building_and_zoning_gis.py
	$(PYTHON) scripts/collectors/virginia/loudoun_county/monthly_reports.py
	$(PYTHON) scripts/collectors/virginia/henrico_county/permits.py
	$(PYTHON) scripts/collectors/illinois/elk_grove_village_cook_assessor.py
	$(PYTHON) scripts/collectors/virginia/manassas/development_actions.py
	$(PYTHON) scripts/collectors/virginia/fairfax_county/land_use_cases.py
	$(PYTHON) scripts/collectors/multistate/water_fire_authorizations.py
	$(PYTHON) scripts/collectors/oregon/portland_west_metro.py
	$(PYTHON) scripts/collectors/virginia/statewide/deq_air_permits.py
	$(PYTHON) scripts/collectors/virginia/statewide/deq_water_permits.py
	$(PYTHON) scripts/collectors/multistate/ckan_catalog_csv.py
	$(PYTHON) scripts/collectors/multistate/accela_case_pages.py
	$(PYTHON) scripts/collectors/ohio/history.py
	$(PYTHON) scripts/collectors/ohio/central_ohio_entitlements.py
	$(PYTHON) scripts/collectors/texas/history.py
	$(PYTHON) scripts/collectors/arizona/history.py
	$(PYTHON) scripts/collectors/indiana/history.py
	$(PYTHON) scripts/collectors/tennessee/history.py
	$(PYTHON) scripts/collectors/nevada/history.py
	$(PYTHON) scripts/collectors/mississippi/history.py
	$(PYTHON) scripts/collectors/louisiana/history.py
	$(PYTHON) scripts/collectors/new_mexico/history.py
	$(PYTHON) scripts/collectors/california/history.py
	$(PYTHON) scripts/collectors/georgia/history.py
	$(PYTHON) scripts/collectors/new_york/history.py
	$(PYTHON) scripts/collectors/pennsylvania/history.py
	$(PYTHON) scripts/collectors/minnesota/history.py
	$(PYTHON) scripts/collectors/florida/history.py
	$(PYTHON) scripts/collectors/new_jersey/history.py
	$(PYTHON) scripts/collectors/colorado/history.py
	$(PYTHON) scripts/collectors/oregon/history.py
	$(PYTHON) scripts/collectors/michigan/history.py
	$(PYTHON) scripts/collectors/utah/history.py
	$(PYTHON) scripts/collectors/north_carolina/history.py
	$(PYTHON) scripts/collectors/south_carolina/history.py
	$(PYTHON) scripts/collectors/oklahoma/history.py
	$(PYTHON) scripts/collectors/kentucky/history.py
	$(PYTHON) scripts/collectors/washington/history.py
	$(PYTHON) scripts/collectors/district_of_columbia/history.py
	$(PYTHON) scripts/collectors/iowa/history.py
	$(PYTHON) scripts/collectors/alabama/history.py
	$(PYTHON) scripts/collectors/wisconsin/history.py
	$(PYTHON) scripts/collectors/north_dakota/history.py
	$(PYTHON) scripts/collectors/kansas/history.py
	$(PYTHON) scripts/collectors/connecticut/history.py
	$(PYTHON) scripts/collectors/west_virginia/history.py
	$(PYTHON) scripts/collectors/nebraska/history.py
	$(PYTHON) scripts/collectors/idaho/history.py
	$(PYTHON) scripts/collectors/montana/history.py
	$(PYTHON) scripts/collectors/wyoming/history.py
	$(PYTHON) scripts/collectors/vermont/history.py
	$(PYTHON) scripts/collectors/south_dakota/history.py
	$(PYTHON) scripts/collectors/hawaii/history.py
	$(PYTHON) scripts/collectors/alaska/history.py
	$(PYTHON) scripts/collectors/maryland/history.py
	$(PYTHON) scripts/collectors/massachusetts/history.py
	$(PYTHON) scripts/collectors/arkansas/history.py
	$(PYTHON) scripts/collectors/puerto_rico/history.py
	$(PYTHON) scripts/collectors/multistate/open_data_feeds.py
	$(PYTHON) scripts/collectors/multistate/open_data_release.py
	$(PYTHON) scripts/collectors/multistate/legistar_search.py
	$(PYTHON) scripts/collectors/multistate/legistar_matters.py
	$(PYTHON) scripts/collectors/multistate/meeting_votes.py
	$(PYTHON) scripts/collectors/federal/epa_named_water_permits.py
	$(PYTHON) scripts/collectors/federal/epa_npdes.py
	$(PYTHON) scripts/collectors/federal/epa_npdes_timeline.py
	$(PYTHON) scripts/collectors/federal/decisions.py
	$(PYTHON) scripts/collectors/federal/doe_nepa.py
	$(PYTHON) scripts/collectors/territories/federal_grants.py
	$(PYTHON) scripts/collectors/federal/ferc_orders.py
	$(PYTHON) scripts/collectors/federal/faa_obstruction_evaluations.py
	$(PYTHON) scripts/collectors/federal/faa_letters_california_energy.py
	$(PYTHON) scripts/collectors/federal/epa_npdes_discovery.py
	$(PYTHON) scripts/collectors/federal/usace_regulatory.py
	$(PYTHON) scripts/collectors/federal/usace_virginia_prior_actions.py
	$(PYTHON) scripts/collectors/federal/usace_digital_library.py
	$(PYTHON) scripts/collectors/federal/epa_air_cases.py
	$(PYTHON) scripts/collectors/federal/fast41_dashboard.py
	$(PYTHON) scripts/collectors/federal/usace_consultations.py
	$(PYTHON) scripts/collectors/guam/land_use_referrals.py
	$(MAKE) build
collect:
	$(PYTHON) scripts/ordinances/discovery/fetch_sources.py
geography:
	$(PYTHON) scripts/pipeline/geography.py
discover-va:
	$(PYTHON) scripts/ordinances/discovery/virginia_directory_sweep.py

replay-sample:
	$(PYTHON) scripts/pipeline/replay_transfer_sample.py

# Per-jurisdiction refresh/validation (see docs/jurisdiction-refresh.md).
#   make check-TX     offline replay x2 with the network blocked; byte-compare to the published edition
#   make refresh-TX   live pull with each collector's own flag, re-check, row diff in output/refresh/TX.json
jurisdictions:
	$(PYTHON) scripts/pipeline/jurisdiction.py list
check-all:
	$(PYTHON) scripts/pipeline/jurisdiction.py check --all
check-%:
	$(PYTHON) scripts/pipeline/jurisdiction.py check $*
refresh-%:
	$(PYTHON) scripts/pipeline/jurisdiction.py refresh $*

# Evidence cache (not in git): pack it for any storage, restore it into a fresh clone.
#   make cache-pack DEST=/Volumes/backup     make cache-restore BUNDLE=/Volumes/backup/cache-2026-11-16.tar
cache-pack:
	$(PYTHON) scripts/pipeline/cache_bundle.py pack $(DEST)
cache-restore:
	$(PYTHON) scripts/pipeline/cache_bundle.py restore $(BUNDLE)

.PHONY: telecom site
telecom:
	$(PYTHON) scripts/pipeline/jurisdiction.py telecom
site:
	$(PYTHON) scripts/collectors/virginia/statewide/telecom_right_of_way.py
	$(PYTHON) scripts/pipeline/build_viewer.py --snapshot-geography
	$(PYTHON) scripts/pipeline/publish_site.py
	$(PYTHON) -m unittest discover -s tests -p test_publication.py
