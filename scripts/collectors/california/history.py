"""California permit history: combines the Los Angeles, San Francisco, San Jose, Santa Clara, Hayward and CEC sources below
into output/history/california/history.json (plus exclusions, validation and ranking files in data/). Offline build by default; --refresh
captures government registers and docket histories."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import argparse, json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import lib.files
from collectors.california.evidence_store import R, C, D, MAN, ASOF, Ctx, m, counts
from collectors.california import atlas_place_ranking as atlas, ladbs_building_permits as ladbs, sfdbi_building_permits as sfdbi, san_jose_building_permits as sj_permits, san_jose_planning_permits as sj_planning, santa_clara_legistar_matters as santa_clara, hayward_legistar_matters as hayward, cec_small_power_plant_dockets as cec
SOURCES=(atlas, santa_clara, hayward, sj_planning, ladbs, sfdbi, sj_permits, cec)
def refresh():
 C.mkdir(exist_ok=True,parents=True)
 tasks=[t for s in SOURCES for t in s.download_tasks()]
 def run(f):f()
 with ThreadPoolExecutor(4) as ex:
  futures=[ex.submit(run,f) for f in tasks];errors=[]
  for v in futures:
   try:v.result()
   except Exception as err:errors.append(str(err));print('error:',str(err),flush=True)
 lib.files.dump(MAN,dict(files=dict(sorted(m.items())),candidate_counts=dict(sorted(counts.items())),cutoff=ASOF,errors=errors));print(counts,errors)
 if errors:raise ValueError('Incomplete refresh: '+str(errors))
def build():
 man=json.loads(MAN.read_text());assert not man['errors'];files=man['files']
 for n,f in files.items():assert lib.files.sha((C/n).read_bytes())==f['sha256'],n
 ctx=Ctx(files)
 for s in (ladbs,sfdbi,sj_permits,sj_planning,santa_clara,hayward,cec):s.rows(ctx)
 out,exc,dups=ctx.out,ctx.exc,ctx.dups
 outlist=sorted(out.values(),key=lambda a:a['id']);lib.files.dump(series_path('ca'),outlist);lib.files.dump(collector_data('california','exclusions.json'),exc);lib.files.dump(collector_data('california','validation.json'),dict(events=len(outlist),dataset_counts=dict(sorted(Counter(r['dataset'] for r in outlist).items())),overlap=dict(dups),geography=atlas.rank(),hashes=len(files),exclusions=len(exc)));print(len(outlist),'events',dups)
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--refresh',action='store_true');args=a.parse_args()
 if args.refresh:refresh()
 build()
