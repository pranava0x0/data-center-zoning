"""Edition-level storage measurements + explicitly assumption-based capacity planning."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import json, csv, math, statistics, os, collections
import lib.discovery as c
def main():
    rule=c.read(c.OUT/'rules.json',[]);frame=list(csv.DictReader((c.R/'data/jurisdictions.csv').open()))
    us=sum(c.read(c.R/'data/geography_sources.json',{})['national_frame_rows_by_layer_excluding_pr'].values())
    idx=c.read(c.INDEX,{});used={c.address(r['url']) for r in rule}
    snap={idx[u]['sha256']:idx[u]['bytes'] for u in used if u in idx and idx[u].get('sha256')}
    if not snap:raise SystemExit('Fetch pilot sources first.')
    size=sorted(snap.values());median=statistics.median(size);p90=size[math.ceil(.9*len(size))-1]
    s=c.read(c.OUT/'virginia_screen.json',{})['results'];search=sum(p.stat().st_size for p in (c.R/'cache/va_sweep').glob('*.bin'));usage=c.read(c.OUT/'token_usage.json',{})
    observed={'unique_curated_snapshots':len(size),'archived_curated_bytes':sum(size),'median_curated_doc_bytes':median,'p90_curated_doc_bytes':p90,'summed_raw_discovery_bytes':search,'va_directory_entries':len(s),'va_successes':sum(bool(x['documents']) for x in s),'bytes_per_rule_export':(c.OUT/'rules.json').stat().st_size/len(rule),'standalone_viewer_bytes':(c.R/'viewer/index.html').stat().st_size,'viewer_asset_bytes':sum(p.stat().st_size for p in (c.R/'viewer').glob('*') if p.is_file())}
    frame56=list(csv.DictReader((c.R/'data/national/jurisdictions.csv').open()));gov=list(csv.DictReader((c.R/'data/national/government_units.csv').open()))
    timeline=c.read(c.OUT/'permit_history_summary.json',{});num=timeline['rows'];sz=timeline['storage'];observed.update(national_geographies=len(frame56),government_entries=len(gov),history_events=num,history_csv_bytes=sz['csv_bytes'],directory_bytes=(c.R/'viewer/coverage.html').stat().st_size)
    # Logical bytes reflect the files needed to reproduce this checkout (including mirrored
    # originals, versioned snapshots, indexes and partial downloads). This is not a count
    # of distinct source bytes or APFS allocation/compression savings.
    archives=collections.Counter();file_count=0
    for directory,subdirs,files in os.walk(c.R/'cache'):
        for name in files:
            path=c.R/directory/name
            try:archives[path.relative_to(c.R/'cache').parts[0]]+=path.stat().st_size;file_count+=1
            except FileNotFoundError:continue
    observed.update(cache_logical_bytes=sum(archives.values()),cache_file_count=file_count,cache_bytes_by_collection=dict(archives.most_common()),cache_measurement_utc=c.now())
    plans=[]
    for label,N in [('Ten requested states',len(frame)),('US 50 states + DC pilot-layer definition',us),('Full Census geographic frame incl. territories',len(frame56))]:
        for case,docs,hits,rules,frac,inp,out in [('lean',3,.12,5,.2,12000,1200),('extended',10,.35,12,.6,40000,4000)]:
            # Sensitivity cases: include 2 retained versions in extended storage, but not in one-pass token budget.
            doc_bytes=median if case=='lean' else p90;vers=1 if case=='lean' else 2
            plans.append(dict(frame=label,case=case,N=N,documents_per_geo=docs,raw_bytes_per_document=doc_bytes,versions=vers,raw_archive_GB=round(N*docs*doc_bytes*vers/1e9,2),positive_fraction=hits,rules_per_positive=rules,feature_rows=round(N*hits*rules),json_MB=round(N*hits*rules*observed['bytes_per_rule_export']/1e6,1),model_review_fraction=frac,input_per_review=inp,output_per_review=out,uncached_input_M=round(N*frac*inp/1e6,2),output_M=round(N*frac*out/1e6,2)))
    c.dump(c.OUT/'scale.json',dict(observed=observed,scenarios=plans))
    rows='\n'.join(f"| {p['frame']} | {p['case']} | {p['N']:,} | {p['feature_rows']:,} | {p['json_MB']:,} MB | {p['raw_archive_GB']:,} GB | {p['uncached_input_M']:,}M / {p['output_M']:,}M |" for p in plans)
    t=usage.get('total',{});tokens=(f"At {usage['measured_utc']}, the four cooperating chats reported **{t['input_tokens']:,} input, including {t['cached_input_tokens']:,} cached; {t['output_tokens']:,} output**. That leaves {usage['uncached_input']:,} uncached input. Repeated cached context explains the large gross number. This includes research, code, tool results and QA up to the recorded checkpoints; it excludes the final reply and is not a bill. See [per-role counters](../output/token_usage.json)." if t else "No local token telemetry was exported.")
    text=f"""# Measured pilot and scale estimates
{tokens}

The deterministic collectors, extractors, ranker and viewer call **no model APIs**. A repeat against fixed inputs takes zero model tokens. Human or model review is still needed for new facts, amendments, scans, negatives and conflicting versions. Do not multiply the engineering session's gross token count by the number of states.

## Measurements
* The full working evidence cache currently contains {observed['cache_logical_bytes']/1e9:.2f} GB across {file_count:,} files, including history, nationwide searches and codebooks. These are logical file sizes; mirrored copies count once per file. The [breakdown](../output/scale.json) separates archives from the much smaller viewer and exports.
* {len(rule)} research rows, {len(size)} unique archived source documents referenced by those rows, {sum(size)/1e6:.2f} MB of original curated source bytes. Median {median/1000:.1f} kB; 90th percentile {p90/1000:.1f} kB. Failed or blocked downloads contribute no source bytes and skew this sample.
* The Virginia first-pass archive used {search/1e6:.1f} MB to screen {len(s)} directory entries; {observed['va_successes']} returned a document. It includes home pages/local PDFs, not a full run through each code book. Discovery files can overlap curated sources; adding the two is not a distinct-document estimate.
* The expanded JSON export uses {observed['bytes_per_rule_export']:,.0f} bytes per row; the standalone atlas is {observed['standalone_viewer_bytes']/1e6:.2f} MB including permit records and map boundaries. Raw documents are stored separately and deduplicated by hash within each archive.
* [Census / registry provenance](../data/geography_sources.json) gives the 2025 frame. There are {len(frame):,} rows in the ten states; {us:,} across the US frame. They are geography rows, not distinct lawmaking bodies. Consolidations, overlapping townships/places and independent cities require reconciliation, and utilities, tribal and federal authorities require additional rosters.

The nationwide frame now has {len(frame56):,} geographic features across 56 state/territory areas, plus {len(gov):,} separate government roster entries. The standalone searchable roster uses {observed['directory_bytes']/1e6:.2f} MB. {num:,} permit actions occupy {sz['csv_bytes']/1e6:.2f} MB in CSV, or approximately {sz['csv_bytes']/num:,.0f} bytes per event; at the same mix, 100,000 actions would be about {sz['csv_bytes']/num/10:.1f} MB, one million about {sz['csv_bytes']/num/1000:.2f} GB (CSV only). Signed PDFs, scans, historical versions and supporting documents are extra. Calculations for the full frame are sensitivity bounds, not a proposal to treat statistical geographies as legislatures.

## What a larger inventory might require
| Frame | Case | Geography rows | Provision rows | JSON export | Original document archive | Uncached input / output tokens |
|---|---|---:|---:|---:|---:|---:|
{rows}

**Lean assumption:** 3 documents per geography at the measured median, one retained version; 12% produce 5 provisions; 20% of geography rows need one targeted 12k-input / 1.2k-output model review. **Extended:** 10 documents at the measured 90th percentile, two retained versions; 35% produce 12 provisions; 60% need a 40k-input / 4k-output review. All percentages, review budgets and hit rates are planning assumptions, not measured national prevalence or guaranteed recall. Input/output budgets are for a single collection pass; another full review cycle adds another pass. Storage uses decimal MB/GB and excludes full parcel/district geometry, rendered page images, indexes and backups. Code corpora or GIS history can substantially exceed these figures.

Equations: original bytes = geographies × documents × bytes per document × retained versions; rows = geographies × positive fraction × provisions per positive; tokens = geographies × reviewed fraction × tokens per review. Substitute local measurements in [the calculator](../scripts/project_scale.py) or [machine-readable scenarios](../output/scale.json). Fixed-source validation is cheap; recall and amendment review are the scaling constraints. Before funding a full pass, stratify by jurisdiction type and portal, hand-search a random sample of apparent negatives, then measure confidence intervals, review time and positive yield.
"""
    (c.R/'docs/scale.md').write_text(text)
if __name__=='__main__':main()
