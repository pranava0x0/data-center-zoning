"""Florida permit history: combines the SFWMD, Miami, Miami-Dade and Eatonville sources below into output/history/florida/history.json.
Offline replay by default; --fetch re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
from lib.files import j
from lib.geo import geofetch, rank
import argparse, collections
import lib.discovery as collect
import lib.net as netfetch
from collectors.florida.common import R, ST, M
from collectors.florida import sfwmd_water_permits as sfwmd, miami_ibuild_permits as miami, miami_dade_building_permits as dade, tampa_planning_permits as tampa, hillsborough_regulatory_zoning as hills, eatonville_council_agendas as eatonville
O=series_path('fl');A=collector_data('florida','coverage.json');C=collector_data('florida','config.json')
SOURCES=(miami, dade, tampa, sfwmd, hills, eatonville)
def stage(c,m):
    if 'geo' not in m or netfetch.REFETCH:m['geo']=geofetch(ST,'12');collect.dump(M,m)
    rank(ST,m['geo'])
    for s in SOURCES:s.download(c,m)
def build(m):
    rank(ST,m['geo']);related=[]
    out,held=sfwmd.rows(m);out+=miami.rows(m);d,h=dade.rows(m);out+=d;held+=h
    direct={v['record_no'] for v in out};related=miami.related(m,direct)
    out+=eatonville.rows()
    if len({v['id'] for v in out})!=len(out):raise ValueError('Duplicate history key')
    collect.dump(O,sorted(out,key=lambda r:r['id']));collect.dump(collector_data('florida','related.json'),related);collect.dump(collector_data('florida','review.json'),held)
    collect.dump(A,dict(cutoff='2026-11-16',raw_hits={k:len(ST.read(v['ids'])['objectIds'] or []) for k,v in m.items() if k!='geo'},by_dataset=dict(collections.Counter(v['dataset'] for v in out)),held_candidate_occurrences=len(held),parcel_only_rows=len(related)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');z=p.parse_args();m=j(M) if M.exists() else {}
    if z.fetch:stage(j(C),m)
    build(m)
