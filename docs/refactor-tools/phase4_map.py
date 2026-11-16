"""Phase 4 mapping: where every history_* file goes so that its path names the collector that writes it.

Used by phase4_move.py (moves + mapping log) and phase4_rewrite.py (code and doc references).
Not imported by the pipeline.
"""
import csv, json, re, sys
from pathlib import Path

P = Path('/Users/pranava/Projects/local ordinance zoning')

sys.path.insert(0, str(P / 'scripts'))
from lib.paths import STATE_FOLDERS  # noqa: E402
# Collectors whose own state folder is the data folder (config-only and state entry points).
TERRITORIES = {'AS', 'GU', 'MP', 'VI'}  # *_supp_sources.json are written by collectors/territories/notice_indexes.py

# Non-state-prefixed data files: old stem (after history_) -> (owner folder under data/history/, new file name)
OWNERS = {
    # Virginia
    'air_application_leads.json': ('virginia/statewide/deq_air_permits', 'application_leads.json'),
    'air_applications.json': ('virginia/statewide/deq_air_permits', 'applications.json'),
    'air_config.json': ('virginia/statewide/deq_air_permits', 'config.json'),
    'air_hashes.json': ('virginia/statewide/deq_air_permits', 'hashes.json'),
    'air_held.json': ('virginia/statewide/deq_air_permits', 'held.json'),
    'air_site_crosswalk.json': ('virginia/statewide/deq_air_permits', 'site_crosswalk.json'),
    'water_manifest.json': ('virginia/statewide/deq_water_permits', 'manifest.json'),
    'water_sources.json': ('virginia/statewide/deq_water_permits', 'sources.json'),
    'loudoun_config.json': ('virginia/loudoun_county/building_and_zoning_gis', 'config.json'),
    'loudoun_counts.json': ('virginia/loudoun_county/building_and_zoning_gis', 'counts.json'),
    'loudoun_manifest.json': ('virginia/loudoun_county/building_and_zoning_gis', 'manifest.json'),
    'loudoun_supplement_config.json': ('virginia/loudoun_county/monthly_reports', 'config.json'),
    'loudoun_supplement_counts.json': ('virginia/loudoun_county/monthly_reports', 'counts.json'),
    'loudoun_supplement_manifest.json': ('virginia/loudoun_county/monthly_reports', 'manifest.json'),
    'loudoun_epd_crosswalk.json': ('virginia/loudoun_county/monthly_reports', 'epd_crosswalk.json'),
    'henrico_audit.json': ('virginia/henrico_county/permits', 'audit.json'),
    'henrico_sources.json': ('virginia/henrico_county/permits', 'sources.json'),
    'fairfax_audit.json': ('virginia/fairfax_county/land_use_cases', 'audit.json'),
    'fairfax_sources.json': ('virginia/fairfax_county/land_use_cases', 'sources.json'),
    'metrova_sources.json': ('virginia/fairfax_county/land_use_cases', 'metrova_sources.json'),  # no reader found
    'elkgrove_sources.json': ('illinois/elk_grove_village_cook_assessor', 'sources.json'),
    # multistate
    'cases.json': ('multistate/accela_case_pages', 'config.json'),
    'pwc_config.json': ('multistate/ckan_catalog_csv', 'config.json'),
    'casebook_sources.json': ('multistate/meeting_votes', 'sources.json'),
    'councilvotes_sources.json': ('multistate/legistar_matters', 'sources.json'),
    'catalog_permits_sources.json': ('multistate/catalog_permits', 'sources.json'),
    'municipal_sources.json': ('multistate/open_data_feeds', 'sources.json'),
    # one-state collectors that are not the state's history.py
    'dcprojects_sources.json': ('district_of_columbia', 'sources.json'),
    'wastate_sources.json': ('washington', 'sources.json'),
    # territories
    'territorial_review.json': ('territories', 'territorial_review.json'),
    'territorial_sources.json': ('territories', 'territorial_sources.json'),
    'as_supp_sources.json': ('territories', 'as_supp_sources.json'),
    'gu_supp_sources.json': ('territories', 'gu_supp_sources.json'),
    'mp_supp_sources.json': ('territories', 'mp_supp_sources.json'),
    'vi_supp_sources.json': ('territories', 'vi_supp_sources.json'),
    # federal
    'corps_cases.json': ('federal/usace_regulatory', 'cases.json'),
    'corps_coverage.json': ('federal/usace_regulatory', 'coverage.json'),
    'corps_district.json': ('federal/usace_regulatory', 'district.json'),
    'corps_district_files.json': ('federal/usace_regulatory', 'district_files.json'),  # no reader found
    'corps_documents.json': ('federal/usace_regulatory', 'documents.json'),
    'corps_geo.json': ('federal/usace_regulatory', 'geo.json'),
    'corps_held.json': ('federal/usace_regulatory', 'held.json'),
    'corps_manifest.json': ('federal/usace_regulatory', 'manifest.json'),  # no reader found
    'corps_queries.json': ('federal/usace_regulatory', 'queries.json'),
    'corps_rrs.json': ('federal/usace_regulatory', 'rrs.json'),
    'corps_rrs_documents.json': ('federal/usace_regulatory', 'rrs_documents.json'),
    'corps_library.json': ('federal/usace_digital_library', 'library.json'),  # no reader found
    'corps_library_notices.json': ('federal/usace_digital_library', 'library_notices.json'),  # no reader found
    'corpslibrary_sources.json': ('federal/usace_digital_library', 'sources.json'),
    'corpslib_queries_sources.json': ('federal/usace_digital_library', 'queries_sources.json'),
    'corps_prior_inquiry.json': ('federal/usace_virginia_prior_actions', 'inquiry.json'),
    'federal_va_prior_sources.json': ('federal/usace_virginia_prior_actions', 'sources.json'),
    'doe_more_sources.json': ('federal/doe_nepa', 'sources.json'),
    'fast_manifest.json': ('federal/fast41_dashboard', 'manifest.json'),
    'federal_aviation_sources.json': ('federal/faa_obstruction_evaluations', 'sources.json'),
    'federal_cases_sources.json': ('federal/decisions', 'sources.json'),
    'federal_power_sources.json': ('federal/ferc_orders', 'sources.json'),
    # pipeline / ordinance scripts that archive their own sources
    'national_sources.json': ('pipeline/national_frame', 'sources.json'),
    'nationalextras_sources.json': ('pipeline/national_authorities', 'sources.json'),
    'hotspots_sources.json': ('pipeline/national_hotspots', 'sources.json'),
    'national_catalog_sources.json': ('pipeline/national_permit_catalog', 'sources.json'),
    'tribalsites_sources.json': ('ordinances/discovery/tribal_screen', 'sources.json'),
}
# Stay where they are: shared by more than one owner or by the pipeline.
STAY = {'series.csv', 'uat_cases.json', 'federal_geo_sources.json'}
# Output (non-series) by-products: old name -> new path relative to output/
OUTPUT_EXTRA = {
    'history_cases_coverage.json': 'history/multistate/accela_case_pages_coverage.json',
    'history_pwc_coverage.json': 'history/multistate/ckan_catalog_csv_coverage.json',
    'history_wtr_nd.json': 'history/federal/epa_named_water_permits/north_dakota.json',  # stale, empty, not a series
}
OUTPUT_STAY = {'history_evidence.csv', 'history_evidence_files.csv', 'history_evidence_quality.json', 'history_materialization.json'}


def series_rows():
    with (P / 'data/history_series.csv').open() as f:
        return list(csv.DictReader(f))


def series_collectors(reg):
    own = {}
    for c, v in reg['collectors'].items():
        for s in v['series']:
            own[s] = c
    return own


def series_new_paths(reg):
    """series -> path relative to output/."""
    rows = series_rows()
    own = series_collectors(reg)
    per = {}
    for r in rows:
        per.setdefault(own[r['series']], []).append(r)
    out = {}
    for c, rs in per.items():
        stem = c.removeprefix('collectors/').removesuffix('.py')
        if len(rs) == 1:
            out[rs[0]['series']] = f'history/{stem}.json'
        else:
            for r in rs:
                out[r['series']] = f"history/{stem}/{STATE_FOLDERS[r['state']]}.json"
    assert len(set(out.values())) == len(out), 'path collision'
    return out


def data_new_path(name):
    """name: old file name like history_tx_validation.json -> new path relative to data/, or None to stay."""
    stem = name.removeprefix('history_')
    if stem in STAY:
        return None
    if stem in OWNERS:
        folder, new = OWNERS[stem]
        return f'history/{folder}/{new}'
    m = re.match(r'([a-z]{2})_(.+)$', stem)
    if m and m[1].upper() in STATE_FOLDERS and m[1].upper() not in TERRITORIES:
        return f'history/{STATE_FOLDERS[m[1].upper()]}/{m[2]}'
    raise KeyError(name)
