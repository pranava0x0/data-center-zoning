"""Write the handoff from the UAT, COMPASS, coverage and byte-audit outputs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv
import lib.discovery as c
def main():
 def j(name):return c.read(c.OUT/(name+'.json'),{})
 qa=j('uat');geo=j('national_scope_check');checks=j('compass_crosscheck');f=j('federal_summary');h=j('permit_history_summary');rule=j('validation');mat=j('receipts/materialization')
 assert qa['passed'] and not qa['errors'] and checks['check']=='pass' and not checks['errors'] and geo['local_first_pass_complete']
 # Each browser profile must have loaded exactly the bytes in the finalized standalone HTML.
 size=(c.R/'viewer/index.html').stat().st_size
 for v in qa['profiles'].values():assert v['coldAssetBytes']==size, 'Browser report describes a different build; run make uat'
 assert mat['history_records_with_matched_bytes']==h['rows'] and not mat['unmatched_hashes']
 with (c.OUT/'priority_local_backlog.csv').open() as fp:backlog=len(list(csv.DictReader(fp)))
 buckets={k:sum(x.get(k,0) for x in h['permit_status_counts'].values()) for k in ('active','historical','unconfirmed')}
 dest=f"""# Atlas release checks · {h['as_of']}

[Open the standalone atlas](../viewer/index.html) · [Federal records](../viewer/federal.html) · [Local follow-up queue](../output/priority_local_backlog.csv)

| What the atlas counts | Records |
|---|---:|
| Published rules and official permitting requirements | {rule['default_visible_count']:,} |
| Ordinance candidates withheld from default results | {rule['held_count']:,} |
| Dated or explicitly undated project history records | {h['rows']:,} |
| Distinct permit keys | {sum(buckets.values()):,} ({buckets['active']:,} active, {buckets['historical']:,} historical, {buckets['unconfirmed']:,} current status unconfirmed) |
| Federal records already included in history | {f['events']:,} |
| Distinct federal permit keys already included above | {sum(f['distinct_permits'].values()):,} |
| Saved checksums recomputed from local files | {mat['matched_files']:,} of {mat['unique_receipt_hashes']:,} |

The [COMPASS cross-check](../output/compass_crosscheck.json) reconciles {checks['upstream_feature_rows']:,} feature rows across five upstream releases. No history, facility or agency-action count should be read as the number of active data centers. [How a row is cited](evidence-receipts.md).

**Geographic limits.** The first pass reconciled {geo['geographies']:,} geographic entries and {geo['government_units']:,} government units across 50 states, DC and the five inhabited territories. Some are overlapping geographies, statistical places or special districts. {backlog} leading county, city or township entries have no matched action in our reviewed local registers. [State-by-state counts](national-progress.md) distinguish local provisions, statewide requirements and federal records.

**Browser results.** {len(qa['checks']):,} passing assertions. Cold-open measurements are from local Chrome on the test machine, not cellular or production-network benchmarks. The single-file download was {size/1e6:.2f} MB. Tests also opened an isolated copy without its neighboring files.

| Viewport | Cold open | Filter change | Local history |
|---|---:|---:|---:|
"""
 for name,v in qa['profiles'].items():dest+=f"| {name} | {v['coldReadyMs']} ms | {v['filterMs']} ms | {v['localHistoryMs']} ms |\n"
 dest+='\n| Task | Maximum actions / swipes / navigations across measured viewports |\n|---|---:|\n'
 for k,name in [('firstRule','Read first rule'),('botetourtFinding','Find the Botetourt zoning rule'),('evidence','Read cited evidence'),('primarySource','Open the government source'),('localPermitHistory','Switch to local permit history')]:
    samples=[v['journeys'][k] for v in qa['profiles'].values() if k in v['journeys']]
    if samples:dest+='| '+name+' | '+' / '.join(str(max(x[field] for x in samples)) for field in ('actions','swipes','navigations'))+' |\n'
 dest+='\n[All browser journeys and measured interaction budgets](../output/uat.json) · [Repeat the build](../Makefile) · [Token and storage estimates](scale.md).\n'
 (c.R/'docs/release-checks.md').write_text(dest)
if __name__=='__main__':main()
