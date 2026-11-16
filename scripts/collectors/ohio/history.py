"""Fetch Ohio official-source snapshots, or rebuild the history and its county/place ranking offline.
One module per issuing source, combined into output/history/ohio/history.json by one hash-pinned capture manifest and
one record-key set (common.py): New Albany zoning entitlements and project updates; Columbus site-engineering and
building-permit GIS plus the Columbus Accela portal; Ohio EPA NPDES registers; Ohio EPA selected air and water permit
PDFs; Hilliard and Dublin planning-decision PDFs; and the PNNL IM3 atlas county/place ranking."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, json
from collectors.ohio.common import CONF, MAN, new_manifest, dump, build
from collectors.ohio import census_pnnl_rankings as geo, new_albany_zoning_entitlements, new_albany_project_updates, columbus_site_engineering, columbus_building_permits, columbus_accela_portal, ohio_epa_npdes, hilliard_planning_decisions, ohio_epa_selected_permits, dublin_planning_decisions
LAYERS={'new_albany':new_albany_zoning_entitlements,'engineering':columbus_site_engineering,'building':columbus_building_permits,**{k:ohio_epa_npdes for k in ('npdes0','npdes1','npdes2','npdes3','npdes4','npdes6','npdes7')}}
DOCS={'hilliard_jun':hilliard_planning_decisions,'hilliard_jul':hilliard_planning_decisions,'ohio_air':ohio_epa_selected_permits,'ohio_water':ohio_epa_selected_permits,'dublin4':dublin_planning_decisions,'dublin5':dublin_planning_decisions}
def fetch(c):
    m=new_manifest(c)
    geo.download(c,m)
    for k,l in c['layers'].items():LAYERS[k].download(c,m,k,l)
    columbus_building_permits.download_parcel_joins(c,m)
    for s in (hilliard_planning_decisions,ohio_epa_selected_permits,dublin_planning_decisions):s.download(c,m)
    dump(MAN,m)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--reuse-portal',action='store_true',help='reuse previously captured municipal detail pages for matching permit IDs');args=p.parse_args()
    c=json.loads(CONF.read_text())
    if args.fetch:
        fetch(c);columbus_accela_portal.portal_fetch(json.loads(MAN.read_text()),args.reuse_portal);new_albany_project_updates.new_albany_leads(True)
    new_albany_project_updates.new_albany_leads();build(c,json.loads(MAN.read_text()),geo,LAYERS,columbus_building_permits,DOCS)
if __name__=='__main__':main()
