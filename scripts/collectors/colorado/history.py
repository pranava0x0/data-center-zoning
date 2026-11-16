"""Colorado permit history: combines the state air tracker and notices with the Denver, Colorado Springs and Aurora
sources below into output/history/colorado/history.json. Offline replay by default; --refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import sys, json
from lib.records import save, CUT
from collectors.colorado import cdphe_apcd_air_permits as air, cdphe_apcd_public_notices as notices, colorado_springs_land_use_appeals as taurus, aurora_building_permits as aurora, denver_commercial_permits as denver, centennial_epl_address_points as centennial
SOURCES=(air, taurus, notices, aurora, denver, centennial)
def make():
    cent,cent_n=centennial.rows();rows,sites,total=air.rows(cent);d,dv_count,den_n=denver.rows(sites)
    rows=rows+d+notices.rows()+taurus.rows()+aurora.rows()
    rows=[r for r in rows if r];save('CO',rows);v=collector_data('colorado','validation.json');q=json.loads(v.read_text());q.update(air_source_rows=total,denver_site_candidates=dv_count,city_narrative_search=dict(Denver=den_n,Centennial=cent_n),cutoff=CUT);v.write_text(json.dumps(q,indent=2)+'\n')
if __name__=='__main__':
    if '--refresh' in sys.argv:
        for s in SOURCES:s.download()
    make()
