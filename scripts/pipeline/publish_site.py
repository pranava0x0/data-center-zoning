"""Build an allowlisted GitHub Pages artifact and versioned, checksummed dataset downloads.

Uses saved, reviewed outputs. No private session files or the research cache enter the site.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv
import hashlib
import html
import json
import re
import shutil
import zipfile
from collectors.virginia.statewide.telecom_right_of_way import csv_write

R = Path(__file__).resolve().parents[2]
SITE = R / '_site'
BASE = 'https://pranava0x0.github.io/data-center-zoning/'
VERSION = '2026-11-21-v1'


def feature_rows(rules, telecom):
    rows = []
    for r in rules:
        if r['check'] not in ('snapshot_match', 'visual_source_check') or r['document_status'] != 'adopted':
            continue
        for n, t in enumerate(r.get('thresholds') or [{}]):
            rows.append(dict(feature_id=r['id'] + '-f' + str(n + 1), rule_id=r['id'], technology='data_center', state=r['state'], jurisdiction=r['jurisdiction'], jurisdiction_type=r['level'], geoid=r.get('map_geoid') or None, feature=t.get('metric') or r['topic'], value=t.get('value'), units=t.get('unit'), comparator=t.get('operator'), condition=t.get('context'), summary=r['summary'], section=r['locator'], effective=r.get('effective'), source_url=r['url'], source_sha256=r['sha256']))
    for r in telecom['provisions']:
        if r['publication_status'] != 'published' or r['document_status'] != 'adopted':
            continue
        for n, t in enumerate(r.get('thresholds') or [r]):
            rows.append(dict(feature_id=r['id'] + '-f' + str(n + 1), rule_id=r['id'], technology='fiber_telecom', state=r['state'], jurisdiction=r['jurisdiction'], jurisdiction_type=r['jurisdiction_type'], geoid=r['geoid'], feature=t.get('feature') or r.get('feature') or r['title'], value=t.get('value'), units=t.get('units'), comparator=t.get('comparator'), condition=t.get('condition') or r['summary'], summary=r['summary'], section=r['locator'], effective=r.get('effective'), source_url=r['url'], source_sha256=r['source_sha256'], scope_class=r['scope_class'], scope_basis=r['scope_basis']))
    return rows


def page(title, description, body, path):
    url = BASE + path
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(description, quote=True)}"><link rel="canonical" href="{url}"><meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(description, quote=True)}"><meta property="og:url" content="{url}"><meta property="og:type" content="website"><link rel="stylesheet" href="style.css"></head><body><header><h1>{html.escape(title)}</h1></header><main class="info-page"><nav><a href="index.html">Atlas</a> · <a href="downloads.html">Downloads</a> · <a href="about.html">Methods and limits</a> · <a href="records.html">Ordinance index</a></nav>{body}</main></body></html>'''


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    downloads = SITE / 'downloads'
    downloads.mkdir()
    rules = json.loads((R / 'output/rules.json').read_text())
    telecom = json.loads((R / 'output/telecom/release.json').read_text())
    features = feature_rows(rules, telecom)
    csv_write(downloads / 'features.csv', features)
    (downloads / 'features.json').write_text(json.dumps(features, ensure_ascii=False, indent=2) + '\n')
    copied = {'data-center-rules.csv': 'output/published.csv', 'data-center-research.json': 'output/rules.json', 'data-center-history.csv': 'output/permit_history.csv', 'data-center-geographies.geojson': 'output/jurisdictions.geojson', 'data-center-held.csv': 'output/holds.csv', 'priority-localities.csv': 'output/priority_localities.csv', 'priority-backlog.csv': 'output/priority_local_backlog.csv', 'telecom-release.json': 'output/telecom/release.json'}
    copied.update({'telecom-' + n + '.csv': 'output/telecom/' + n + '.csv' for n in ('provisions', 'published', 'held', 'instruments', 'events', 'locations', 'coverage', 'authority_coverage')})
    for name, source in copied.items():
        shutil.copyfile(R / source, downloads / name)
    with (R / 'output/priority_localities.csv').open() as f:
        priority = [r for r in csv.DictReader(f) if r['group'] != 'statistical place']
    matched = sum(int(r['reviewed_local_register_rows']) > 0 for r in priority)
    coverage = dict(data_center=dict(national_completeness=None, measure='Priority locality entries with a matched reviewed local-register action; not ordinance completeness or distinct governments', numerator=matched, denominator=len(priority), percent=round(100 * matched / len(priority), 1)), fiber_telecom=telecom['coverage_summary']['pilot'], fiber_telecom_virginia=telecom['coverage_summary']['virginia'])
    (downloads / 'coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
    schema = dict(date_fields='Telecom original_target, revised_target and completion_date are agency tracker fields and do not establish physical construction timing. Event date and date_role travel together. Current validity is unconfirmed independently of reported application approval.', coverage_interpretation='Numerators count authorities with a source check marked verified; partial reviews are excluded. A verified check can concern guidance or a filed proposal. Adoption, publication and history completeness are separate.', schema_version='1.1.0', release=VERSION, data_center_history_as_of='2026-11-15', telecom_as_of=telecom['as_of'], csv_safety='Formula-like CSV cells beginning with =, +, -, @, tab or CR receive an apostrophe prefix. JSON preserves original values; do not strip arbitrary source apostrophes.', nulls='Empty CSV cell and JSON null mean unknown or inapplicable; never a negative finding.', history_classification='Data-center review_class is a workflow class, not approval status; land-use cases can be pending, denied or withdrawn. Count rows as records/actions, not distinct permits.', telecom_coverage_baseline=telecom['coverage_summary'], project_linkage='project_id is null when no official cross-instrument project identity is established. Applicant name or proximity is insufficient.', identifiers='All GEOIDs and identifiers are strings. Preserve leading zeros. geoid describes issuing geography for features, work location for instrument-location rows.', units='Feature value, comparator, units and condition must travel together. Each quantitative threshold has its own linked feature row. Qualitative features have null value/units.', technologies=['data_center', 'fiber_telecom'], table_units=dict(features='One adopted, published legal feature; excludes guidance, held research, individual approvals and history.', rules='One reviewed requirement, with document_status and telecom publication_status; thresholds can contain several features. Full research includes holds; telecom-published excludes them.', instruments='One documented application, permit or easement authorization. Count only land_use_permit as a permit; validity is separate.', events='One dated action, linked by instrument_id. Repeated identical VDOT steps are deduplicated; different starts remain separate.', locations='One agency-reported instrument location, linked by instrument_id; geometry null when route unmapped.', coverage='One researched authority/locality source check with explicit limits.', authority_coverage='One government or VDOT entry in the pinned 2022 Virginia baseline; source review is not ROW ownership or a permit census.'), relationships=['features.rule_id -> data-center-research.id or telecom-provisions.id', 'telecom-events.instrument_id -> telecom-instruments.id', 'telecom-locations.instrument_id -> telecom-instruments.id'], compass='Atlas extension schema, not an official NLR release or tested NLR ingest. Feature names and units require a reviewed crosswalk before direct COMPASS integration.', field_dictionary={k: v for k, v in [('feature_id','Stable feature key; original rule ID plus ordinal. Ordinals are release-scoped.'),('rule_id','Stable reviewed source requirement ID.'),('scope_class','Telecom data_center_specific or general; read scope_basis. Empty for data-center features.'),('scope_basis','Evidence and limits of telecom customer/provider scope.'),('technology','data_center or fiber_telecom.'),('state','Two-letter US postal code.'),('jurisdiction','Named authority jurisdiction; not work location.'),('jurisdiction_type','State, county, municipality or other original authority type.'),('geoid','String identifier or null. Never coerce to number.'),('feature','Measurement metric or qualitative requirement.'),('value','Number, source-supported nonnumeric value, or null; preserve type from JSON.'),('units','Source-reviewed unit; not inferred from prose.'),('comparator','Original comparison such as >=, > or <=; null for qualitative features.'),('condition','Scope, exceptions and alternatives.'),('summary','Reviewed legal summary; not parcel advice.'),('section','Original legal locator.'),('effective','Supported ISO date or null; never retrieval date.'),('source_url','Primary official source URL.'),('source_sha256','SHA-256 of archived source bytes.')]})
    (downloads / 'schema.json').write_text(json.dumps(schema, indent=2) + '\n')
    manifest = dict(release=VERSION, schema_version='1.1.0', coverage=coverage, files=[])
    for p in sorted(downloads.iterdir()):
        item = dict(name=p.name, bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        if p.suffix == '.csv':
            with p.open() as f:
                item['rows'] = sum(1 for _ in csv.DictReader(f))
        manifest['files'].append(item)
    (downloads / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(downloads / ('atlas-' + VERSION + '.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(downloads.iterdir()):
            if p.suffix != '.zip':
                info=zipfile.ZipInfo(p.name,date_time=(2026,11,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,p.read_bytes())
    archive=downloads / ('atlas-' + VERSION + '.zip')
    (downloads / 'archive.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    for p in (R / 'viewer').iterdir():
        if p.suffix == '.html':
            public_html = re.sub(r'href="\.\./docs/[^"]+"', 'href="about.html"', p.read_text())
            (SITE / p.name).write_text(public_html)
        elif p.suffix == '.css':
            shutil.copyfile(p, SITE / p.name)
    # All viewer entry points are self-contained or redirect to index. The directory uses these local files.
    for name in ['coverage.js', 'coverage-data.js']:
        if (R / 'viewer' / name).exists():
            shutil.copyfile(R / 'viewer' / name, SITE / name)
    index = (SITE / 'index.html').read_text()
    description = 'Search cited data-center zoning rules and permit history. Explore a separate Virginia fiber and telecom right-of-way pilot, download datasets, and print the map.'
    metadata = f'<meta name="description" content="{description}"><link rel="canonical" href="{BASE}"><meta property="og:title" content="Data center zoning and telecom rights-of-way"><meta property="og:description" content="{description}"><meta property="og:url" content="{BASE}"><meta property="og:type" content="website"><meta name="twitter:card" content="summary">'
    structured = dict({'@context':'https://schema.org','@type':'Dataset','name':'Data center zoning and Virginia telecom ROW atlas','description':description,'url':BASE,'dateModified':'2026-11-21','isAccessibleForFree':True,'distribution':[{'@type':'DataDownload','encodingFormat':'text/csv','contentUrl':BASE+'downloads/features.csv'},{'@type':'DataDownload','encodingFormat':'application/json','contentUrl':BASE+'downloads/telecom-release.json'}]})
    index = index.replace('</head>', metadata + '<script type="application/ld+json">' + json.dumps(structured) + '</script></head>')
    # Local development links into ../docs are replaced with actual public destinations.
    index = re.sub(r'href="\.\./docs/[^"]+"', 'href="about.html"', index)
    index = index.replace('<noscript>', '<noscript><p>Browse the <a href="records.html">ordinance index</a> or <a href="downloads.html">download the datasets</a> without JavaScript.</p>')
    (SITE / 'index.html').write_text(index)
    dc, tc, va = coverage['data_center'], coverage['fiber_telecom'], coverage['fiber_telecom_virginia']
    coverage_body = f'<h2>Coverage and incompleteness</h2><p>Data centers: {dc["percent"]}% ({dc["numerator"]}/{dc["denominator"]}) of priority locality entries have a matched action in a reviewed local register. This measures evidence coverage, not the share of ordinances collected. National ordinance completeness is unknown.</p><p>Fiber and telecom: {tc["percent"]}% ({tc["numerator"]}/{tc["denominator"]}) of the original Virginia pilot authorities have an archived primary-source review. Statewide source checks: {va["percent"]}% ({va["numerator"]}/{va["denominator"]}) against a pinned 2022 Census baseline of 322 general-purpose governments plus VDOT. This is not a current government census, code completeness or road ownership inventory. Leesburg has a partial charter review; its ROW permit process remains blocked. Histories are bounded samples; national and history completeness are unknown. Ohio and Texas checks do not count toward Virginia. Only checks marked verified count; partial reviews do not. A verified source check can cover guidance or a filed proposal and does not establish adoption.</p>'
    links = ''.join(f'<li><a href="downloads/{html.escape(p.name)}" download>{html.escape(p.name)}</a> ({p.stat().st_size:,} bytes)</li>' for p in sorted(downloads.iterdir()))
    body = '<p>Version ' + VERSION + '. Data-center history through November 15; telecom snapshots through November 21, 2026. The filtered CSV button in the atlas exports the current list.</p>' + coverage_body + '<h2>Download</h2><ul>' + links + '</ul><h2>What is a row?</h2><p>A feature is one legal requirement or measurement. A history row is an action, not necessarily a permit. Telecom applications, instruments, events and locations have separate tables and stable links. Read schema.json before joining them. Keep GEOIDs as strings.</p><p>The ZIP contains the same tables, schema and SHA-256 manifest. <a href="https://github.com/pranava0x0/data-center-zoning/releases">Version archives on GitHub Releases</a> preserve earlier datasets across site updates. The full telecom provisions table and research JSON include held records. telecom-published.csv excludes holds; telecom-held.csv lists filed proffers and historical law pending currency review. Guidance is included in the published requirement table but excluded from adopted features. telecom-authority_coverage.csv lists the Virginia follow-up queue. Each authority source check establishes only the cited document, not a complete local code or permit history.</p>'
    (SITE / 'downloads.html').write_text(page('Download the zoning and ROW datasets', 'Versioned CSV, JSON, GeoJSON and ZIP downloads with schemas, checksums and separate coverage measures.', body, 'downloads.html'))
    about = '<h2>What does the atlas cover?</h2><p>The data-center collection and the Virginia wireline fiber/telecom pilot are separate research areas. Telecom requirements distinguish data center connectivity from general provider/work classes. Some tax provisions concern network equipment without naming fiber. Instruments are linked to a data center only when an official record establishes that relationship; none of the current instruments establishes one. Filed proffers and unchecked historical statutes are held separately.</p>' + coverage_body + '<h2>How reliable are the records?</h2><p>Published requirements pass archived-source integrity, passage, review-pin, geography and taxonomy checks. Numeric extraction recipes are replayed independently. These tests do not establish repeal status, complete discovery, current enforcement or parcel eligibility. Some agency roles are inferred and labeled in the export; a publisher is not automatically a decision-maker. Read the primary instrument before relying on a rule.</p><h2>What do map counts mean?</h2><p>Data-center maps distinguish provisions and distinct permits by reported status. Telecom maps count requirements, instruments/applications and dated actions separately. County and city totals may overlap; never add them to infer unique instruments. There are no inferred fiber routes. A blank place means no matching atlas record.</p><h2>How do I save the map as PDF?</h2><p>Select the technology, place and map metric, then choose Print map / PDF. In the browser print dialog, select Save as PDF. The map, selected scope, metric and coverage note are retained. No external map service is needed.</p><h2>Can I import this into COMPASS?</h2><p>The feature table is a versioned atlas extension inspired by the NLR feature model. It is not a certified COMPASS release, and direct NLR ingestion has not been tested. Fairfax building and equipment setbacks export as two linked feature rows. A permit and its timeline live in separate history tables.</p><h2>Sources, corrections and reuse</h2><p>Official source links, section locators, snapshot hashes and dates travel with the records. Source captures distinguish raw agency bytes from extracted primary-publisher text. Source materials retain their original rights; no blanket license is asserted for third-party documents. Submit corrections with the record ID and official source.</p><p><a href="https://github.com/pranava0x0/data-center-zoning/issues">Report a correction</a> · <a href="https://github.com/pranava0x0/data-center-zoning">Source code and audit documents</a></p>'
    (SITE / 'about.html').write_text(page('Methods, coverage and limits', 'How the atlas separates ordinances, requirements, permit actions and two technology collections.', about, 'about.html'))
    articles = []
    for r in rules:
        if r['check'] not in ('snapshot_match', 'visual_source_check'):
            continue
        articles.append('<article id="' + html.escape(r['id'], quote=True) + '"><h2>' + html.escape(r.get('card_title') or r['topic']) + '</h2><p>' + html.escape(r['jurisdiction'] + ', ' + r['state'] + ' · ' + r['document_status']) + '</p><p>' + html.escape(r['summary']) + '</p><p><a href="' + html.escape(r['url'], quote=True) + '">Official source</a> · ' + html.escape(r['locator']) + '</p></article>')
    (SITE / 'records.html').write_text(page('Data-center ordinance index', 'Cited summaries of data-center ordinances and permitting requirements, readable without JavaScript.', '<p>Data-center records only. Agency guidance and individual decisions are labeled. <a href="index.html#view=telecom">Fiber and telecom ROW records</a> have a separate collection.</p>' + ''.join(articles), 'records.html'))
    def telecom_article(r):
        label = ' · '.join([r['jurisdiction'] + ', ' + r['state'], r['record_type'], r['document_status'], r['publication_status'], r['scope_class']])
        return '<article id="'+html.escape(r['id'],quote=True)+'"><h2>'+html.escape(r['title'])+'</h2><p>'+html.escape(label)+'</p><p>'+html.escape(r['summary'])+'</p><p>'+html.escape(r['scope_basis'])+'</p><p>'+html.escape(r['locator'])+' · <a href="'+html.escape(r['url'],quote=True)+'">Official source</a></p></article>'
    current=[r for r in telecom['provisions'] if r['publication_status']=='published']
    held=[r for r in telecom['provisions'] if r['publication_status']=='held']
    telecom_articles='<h2>Published requirements ('+str(len(current))+')</h2>'+''.join(map(telecom_article,current))+'<h2>Held research ('+str(len(held))+')</h2><p>These records are not established as current adopted requirements. Filed proffers need adoption evidence; historical enrolled laws need amendment review. They are excluded from the current interactive view and adopted-feature export.</p>'+''.join(map(telecom_article,held))
    (SITE/'telecom.html').write_text(page('Fiber and telecom ROW requirements','Cited Virginia ROW requirements with separate Ohio and Texas research, published guidance and clearly held proposals or historical law.',coverage_body+telecom_articles,'telecom.html'))
    (SITE / 'llms.txt').write_text(f'''# Data center zoning and telecom ROW atlas

> Source-linked research, not parcel eligibility or legal advice. National completeness is unknown.

- [Atlas]({BASE}): Data-center rules and history; separate Virginia fiber/telecom ROW view.
- [Static telecom requirements]({BASE}telecom.html): Published requirements and separately held research; Virginia expansion with limited Ohio and Texas records.
- [Static ordinance index]({BASE}records.html): Cited data-center summaries without JavaScript.
- [Methods and limits]({BASE}about.html): Units, dates, authority and incompleteness.
- [Downloads]({BASE}downloads.html): CSV, JSON, GeoJSON and ZIP.
- [Version archives](https://github.com/pranava0x0/data-center-zoning/releases): Preserved dataset ZIPs and checksums.
- [Schema]({BASE}downloads/schema.json): Versioned table definitions and relationships.
- [Manifest]({BASE}downloads/manifest.json): Release, row counts and SHA-256 hashes.
- [Coverage]({BASE}downloads/coverage.json): Numerators, denominators and definitions.

## Interpretation
Data centers and fiber/telecom are distinct technologies. Telecom source checks distinguish the original four-authority Virginia pilot from a 323-entry 2022 Virginia government/VDOT baseline. Neither measures ordinance or history completeness. Numerators count verified source-review milestones, which can cover guidance or filed proposals; partial checks are excluded and adoption is tracked separately. Leesburg permit-process access is blocked; charter review is partial. Ohio and Texas checks are excluded from Virginia percentages. Data center connectivity and general provider requirements have explicit scope fields. Filed proffers and unchecked historical laws are held, not current adopted requirements. A project locality is not the permitting authority. Agency guidance is not an enacted ordinance. Applications, hearings, conveyance votes and timeline actions are not interchangeable with issued permits. Approved does not establish current validity. Do not infer a data-center customer, route geometry or zero-rule finding. Preserve source URL, section, scope, exceptions, comparator and units. Use source dates, not retrieval dates, for legal effect. Read primary sources and report holds or unresolved roles.
''')
    (SITE / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + BASE + 'sitemap.xml\n')
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + BASE + p + '</loc></url>' for p in ['', 'downloads.html', 'about.html', 'records.html', 'telecom.html', 'coverage.html']) + '</urlset>')
    (SITE / '.nojekyll').touch()
    (SITE / '404.html').write_text(page('Page not found', 'Return to the zoning atlas.', '<p><a href="' + BASE + '">Open the atlas</a></p>', '404.html'))
    print(f'Pages artifact: {len(features)} features; {len(manifest["files"])} checksummed downloads; {sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file()):,} bytes')


if __name__ == '__main__':
    build()
