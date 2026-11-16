"""Wisconsin permit history: combines the sources below into output/history/wisconsin/history.json. Offline by default; --refresh
re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
from lib.records import CUT, save
import sys, json
from collectors.wisconsin import dnr_air_permit_tracking as air, dnr_lighthouse_campus_review as lighthouse, mount_pleasant_plan_commission_minutes as mount_pleasant
SOURCES=(air, lighthouse, mount_pleasant)
def mk():
 a,cnt=air.rows();rows=a+lighthouse.rows()+mount_pleasant.rows()
 save('WI',[r for r in rows if r]);v=collector_data('wisconsin','validation.json');o=json.loads(v.read_text());o.update(air_facility_register_rows_including_inactive=cnt,cutoff=CUT);v.write_text(json.dumps(o,indent=2)+'\n')
if __name__=='__main__':
 if '--refresh' in sys.argv:
    for s in SOURCES:s.download()
 mk()
