"""Iowa permit history: combines the sources below into output/history/iowa/history.json. Offline by default; --refresh re-downloads
every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
from lib.records import CUT, save
import sys, json
from collectors.iowa import dnr_air_construction_permits as construction, dnr_title_v_permits as title_v, council_bluffs_building_permits as council_bluffs, west_des_moines_site_plans as west_des_moines
SOURCES=(construction, title_v, council_bluffs, west_des_moines)
def make():
    rows,names,stats=construction.rows();rows+=title_v.rows(names)+council_bluffs.rows()+west_des_moines.rows()
    save('IA',rows)
    p=collector_data('iowa','validation.json');v=json.loads(p.read_text());v.update(**stats,cutoff=CUT);p.write_text(json.dumps(v,indent=2)+'\n')
if __name__=='__main__':
    if '--refresh' in sys.argv:
        for s in (construction,title_v):s.download()
    make()
