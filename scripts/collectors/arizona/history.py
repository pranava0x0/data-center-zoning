"""Arizona permit history: combines the sources below into output/history/arizona/history.json. Build from local evidence, or
--refresh to replace the source snapshot."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from collectors.arizona.common import *
from collectors.arizona import (mesa_building_permits as mesa, phoenix_permits as phoenix, maricopa_air_permits as maricopa_air,
    tempe_building_permits as tempe, tucson_building_permits as tucson, adeq_stormwater_permits as adeq,
    scottsdale_building_permits as scottsdale, accela_citizen_access as accela, chandler_council_decisions as chandler,
    pima_maricopa_county_notices as notices, pnnl_census_rankings as rankings)
def refresh(reuse_details=False):
    m,queries,save,query=session()
    rankings.download(save);chandler.download(save);notices.download(save)
    mesa.download(save,query,queries)
    phoenix.download(query,queries);maricopa_air.download(query,queries);tempe.download(query,queries);tucson.download(query,queries);adeq.download(query,queries)
    scottsdale.download(save,query,queries)
    accela.download(save,queries,reuse_details)
    notices.register(m)
    lib.files.dump(manifest,{'cutoff':ASOF,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'files':m,'candidate_counts':queries})
def build():
    b=Build()
    mesa.rows(b);phoenix.rows(b);maricopa_air.rows(b);tempe.rows(b);tucson.rows(b);adeq.rows(b)
    accela.rows(b);scottsdale.rows(b);chandler.rows(b);notices.rows(b)
    rows=b.rows;reject=b.reject;stats=b.stats;m=b.m;meta=b.meta
    wlabels={'storm':'ADEQ myDEQ construction stormwater','storm_old':'ADEQ legacy construction stormwater','industrial':'ADEQ myDEQ industrial stormwater','industrial_old':'ADEQ legacy industrial stormwater','demin':'ADEQ myDEQ de minimis discharge','demin_old':'ADEQ legacy de minimis discharge'}
    out=sorted(rows.values(),key=lambda a:(a['date'] or '',a['id']),reverse=True)
    for r in out:
        r['dataset']=wlabels.get(r['dataset'],r['dataset'])
        if r['dataset']=='City citizen access record':r['dataset']=r['jurisdiction']+' Citizen Access'
    lib.files.dump(OUT,out);lib.files.dump(collector_data('arizona','exclusions.json'),reject)
    summary={}
    for name in sorted({r['dataset'] for r in out}):
        rr=[r for r in out if r['dataset']==name];ds=sorted(r['date'] for r in rr if r['date']);summary[name]=dict(rows=len(rr),unique_numbers=len({r['record_no'] for r in rr}),statuses=Counter(r['status'] for r in rr),date_roles=Counter(r['date_role'] for r in rr),first=ds[0] if ds else None,last=ds[-1] if ds else None)
    lib.files.dump(collector_data('arizona','validation.json'),dict(cutoff=ASOF,records=len(out),archives=len(m),registers=summary,candidate_counts=meta['candidate_counts'],rejected=len(reject),exclusions=stats,geography=rankings.rank()))
    print(len(out),'records;',len(reject),'excluded candidates;',len(m),'archives verified')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--refresh',action='store_true');p.add_argument('--reuse-accela',action='store_true',help='With --refresh, reuse previously acquired slow portal responses.');a=p.parse_args()
    if a.refresh:refresh(a.reuse_accela)
    build()
