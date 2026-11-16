"""Nevada permit history: combines the NDEP, Clark County, Henderson, Reno, Las Vegas, Washoe County and EPA ICIS sources
below into output/history/nevada/history.json. Offline replay by default; --refresh re-downloads every source; --epa-zip installs a
fresh EPA ICIS national archive."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import argparse, json
from collections import Counter
from pathlib import Path
import lib.files
from collectors.nevada.common import R, D, C, MAN, ASOF, SOURCES, read, make_add
from collectors.nevada import census_atlas_rankings as geo, henderson_development_permits as henderson, clark_county_inspection_sites as clark_bldg, clark_county_air_quality as clark_air, reno_issued_permits as reno, las_vegas_building_permits as las_vegas, ndep_air_permits as ndep, washoe_county_decisions as washoe, epa_icis_npdes as epa_npdes
SOURCES_MODS=(geo, ndep, clark_air, washoe, henderson, clark_bldg, reno, las_vegas)
def capture():
 m={}; stats={};C.mkdir(parents=True,exist_ok=True)
 for s in SOURCES_MODS:s.download(m,stats)
 order={n:i for i,n in enumerate(SOURCES)};m=dict(sorted(m.items(),key=lambda kv:order.get(kv[0],len(order))))
 lib.files.dump(MAN,{'cutoff':ASOF,'files':m,'candidate_counts':stats})
def build():
 m=json.loads(MAN.read_text())['files']
 for n,f in m.items():assert lib.files.sha((C/n).read_bytes())==f['sha256'],n
 rows={};excluded=[];leads=[]
 add=make_add(rows,m)
 henderson.rows(add,excluded);clark_bldg.rows(add,excluded);clark_air.rows(add,excluded,leads);reno.rows(add,excluded);las_vegas.rows(add,excluded)
 ndep.rows(add);washoe.rows(add);epa_npdes.rows(add)
 out=sorted(rows.values(),key=lambda r:r['id']);assert len(out)==len({r['id'] for r in out})
 lib.files.dump(series_path('nv'),out);lib.files.dump(collector_data('nevada','leads.json'),{'facility_inventory_only':leads,'excluded_municipal_candidates':excluded})
 lib.files.dump(collector_data('nevada','validation.json'),{'events':len(out),'datasets':dict(sorted(Counter(r['dataset'] for r in out).items())),'statuses':dict(sorted(Counter(r['status'] for r in out).items())),'rank':geo.rank(),'candidate_counts':json.loads(MAN.read_text())['candidate_counts'],'hash_checks':len(m),'excluded_candidates':len(excluded),'facility_inventory_only':len(leads)})
 print(len(out),'events,',len(leads),'stationary-source inventory leads')
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--refresh',action='store_true');ap.add_argument('--epa-zip',type=Path,help='Fresh EPA ICIS national archive; otherwise retain the pinned slices');args=ap.parse_args()
 if args.epa_zip:
  epa_npdes.split(args.epa_zip)
 if args.refresh:capture()
 if args.refresh or args.epa_zip:epa_npdes.seal()
 build()
