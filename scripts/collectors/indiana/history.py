"""Indiana permit history: combines the sources below into output/history/indiana/history.json, with coverage counts in
data/history/indiana/coverage.json and the place ranking in data/history/indiana/rank.json. Offline by default; --fetch re-downloads
every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections
from collectors.indiana.evidence_store import C, M, OUT, AUDIT, j, collect, make_adder
from collectors.indiana import im3_atlas_place_ranking as atlas, dhs_project_activity as dhs, idem_air_water_decisions as idem, hobart_plan_commission_minutes as hobart
def main():
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');args=p.parse_args();c=j(C);m=j(M) if M.exists() else {'captured_utc':collect.now(),'queries':{},'docs':{}}
    if args.fetch:
        atlas.download(m,c); dhs.download(c,m); dhs.formfetch(m); dhs.casefetch(m); idem.download(); hobart.download()
    build(c,m)
def build(c,m):
    atlas.rank(m);out=[];add=make_adder(c,out)
    held,projs=dhs.rows(c,m,add);idem.rows(c,m,add);hobart.rows(c,m,add)
    if len({a['id'] for a in out})!=len(out):raise ValueError('Duplicate event ID')
    collect.dump(OUT,sorted(out,key=lambda a:(a['date'] or '',a['id'])))
    count=lambda a:dict(collections.Counter(a))
    collect.dump(AUDIT,dict(queries=len(m['queries']),query_errors=[dict(area=w['area'],start=w['start'],end=w['end'],error=w['error']) for w in m['queries'].values() if 'error' in w],unique_screened_projects=len(projs),strict_matching_projects=len(projs)-len(held),event_kinds=count(a['kind'] for a in out),jurisdictions=count(a['jurisdiction'] for a in out),held_projects=held))
    print(len(out),'events;',len(projs)-len(held),'verified DHS projects')
if __name__=='__main__':main()
