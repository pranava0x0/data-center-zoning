"""Louisiana permit history: combines the sources below into output/history/louisiana/history.json. Offline by default; --refresh
re-downloads the DEQ quarterly publications."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import json, sys
from lib.records import save
from collectors.louisiana.deq_quarterly_reports import ROOT, fetch
from collectors.louisiana import epa_icis_npdes as icis, deq_quarterly_actions as quarterly, deq_public_notices as notices, usace_vicksburg_regulatory_notices as usace, bossier_parish_police_jury as bossier, shreveport_land_use_decisions as shreveport
def main():
    ep=icis.rows();rows,stats=quarterly.rows(ep);rows+=notices.rows()+usace.rows()+bossier.rows()+shreveport.rows()
    save('LA',rows);vp=collector_data('louisiana','validation.json');v=json.loads(vp.read_text());v['quarterly_screen']=dict(stats);vp.write_text(json.dumps(v,indent=2)+'\n')
if __name__=='__main__':
    if '--refresh' in sys.argv:fetch()
    main()
