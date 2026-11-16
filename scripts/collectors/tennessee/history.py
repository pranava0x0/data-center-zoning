"""Tennessee permit history: combines the Metro Nashville, Franklin, Shelby County and EPA ICIS-NPDES sources below into
output/history/tennessee/history.json (plus the coverage, rank and manifest files in data/). Default is hash-checked offline replay;
--fetch re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections
import lib.discovery as collect
from collectors.tennessee.evidence_store import R, C, M, O, A, j, read, dataset_rows, adder
from collectors.tennessee import atlas_place_ranking as atlas, metro_nashville_codes_permits as metro, franklin_planning_commission as franklin, shelby_county_permits as shelby, epa_icis_npdes as epa
SOURCES=(metro, shelby, franklin, epa)
def fetch(c,m):
    atlas.download(c,m)
    for s in SOURCES:s.download(c,m)
    top=['snapshot_utc','atlas','place_ids','places','layers','unavailable_layers','franklin_matters','franklin_histories','docs','parcel_queries','parcels','echo']
    m.update({k:m.pop(k) for k in sorted(m,key=lambda k:top.index(k) if k in top else len(top))})  # keep manifest keys in the original order
    for sub,order in (('layers',c['layers']),('unavailable_layers',c['layers']),('docs',c['documents'])):
        if sub in m:m[sub]={k:m[sub][k] for k in sorted(m[sub],key=lambda k:list(order).index(k) if k in order else len(order))}
    collect.dump(M,m)
def main():
    a=argparse.ArgumentParser();a.add_argument('--fetch',action='store_true');v=a.parse_args();c=j(C);m=j(M) if M.exists() else {'snapshot_utc':collect.now()}
    if v.fetch:fetch(c,m)
    build(c,m)
def build(c,m):
    atlas.rank(m);rows=[];held=[];cut=c['cutoff'];add=adder(rows,cut)
    metro.rows(m,add);franklin.rows(m,add);echo,nfs,nps=epa.rows(c,m,add);shelby.rows(m,add)
    if len({v['id'] for v in rows})!=len(rows):raise ValueError('Duplicate normalized history identity')
    known={v['record_no'] for v in rows if v['dataset'].startswith('EPA')};held=[dict(npdes_id=n,name=f['CWPName'],reason='Alias/address-only ECHO lead; no accepted facility use and permit join') for n,f in echo.items() if n not in known]
    collect.dump(O,sorted(rows,key=lambda r:(r['date'] or '',r['id'])))
    collect.dump(A,dict(rows=len(rows),by_register=dict(collections.Counter(x['dataset'] for x in rows)),parcels=len(m['parcels']),parcel_rows_screened=sum(len(read(r)) for r in m['parcels'].values()),epa_facilities_screened=nfs,epa_permit_versions_screened=nps,epa_held=held,held_remote_catalogs=m.get('unavailable_layers',{}),unreviewed_gis_candidates={k:len(dataset_rows(v['screen'])) for k,v in m.get('layers',{}).items()}))
    print(len(rows),'Tennessee actions')
if __name__=='__main__':main()
