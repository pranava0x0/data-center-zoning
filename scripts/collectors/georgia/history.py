"""Georgia permit history: combines the sources below into output/history/georgia/history.json, with the review holds and coverage
counts in data/history/georgia/review.json and data/history/georgia/coverage.json. Default is hash-checked offline replay;
--fetch re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections
from collectors.georgia.evidence_store import R, C, M, O, A, REVIEW, j, read, collect, county_names
from collectors.georgia import atlas_place_ranking as atlas, epd_air_permits as epd, arc_dri_reviews as arc, alpharetta_commercial_permits as alpharetta, douglas_county_agendas as douglas, south_fulton_zoning_agenda as south_fulton
def build(m):
    atlas.rank(m);co=county_names()
    out,holds,pool=epd.rows(m,co)
    arc_out,arc_holds,arcs=arc.rows(m,co);out+=arc_out;holds+=arc_holds
    out+=alpharetta.rows();out+=douglas.rows(m);out+=south_fulton.rows()
    if len(out)!=len({v['id'] for v in out}):raise ValueError('Duplicate action key')
    collect.dump(O,sorted(out,key=lambda r:r['id']));collect.dump(REVIEW,holds)
    collect.dump(A,{'cutoff':j(C)['cutoff'],'counts':dict(collections.Counter(v['dataset'] for v in out)),'state_air_candidates':len(pool),'arc_candidates':len(arcs),'holds':len(holds),'alpharetta_layers':{k:{'total':read(v['total'])['count'],'query_hits':len(read(v['ids'])['objectIds'] or [])} for k,v in j(alpharetta.ALPH).items()}})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');args=p.parse_args();m=j(M) if M.exists() else {}
    if args.fetch:
        c=j(C);atlas.fetch(c,m);epd.fetch(c,m);arc.fetch(c,m);douglas.fetch(c,m);epd.fetch_proofs(m);arc.fetch_proofs(m);epd.permitfiles(m);alpharetta.cityfetch();south_fulton.download()
    build(m)
