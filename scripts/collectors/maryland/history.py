"""Maryland permit history: combines the Baltimore DHCD and MDE Frederick sources below into output/history/maryland/history.json.
Offline replay by default; --refresh re-downloads every source; --city re-downloads only the Baltimore register."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import sys, json
from lib.records import CUT, save
from collectors.maryland import baltimore_building_permits as baltimore, mde_frederick_permits as mde
SOURCES=(baltimore, mde)
def make():
 a,balt_stats=baltimore.rows();b,mde_stats=mde.rows();rows=a+b
 save('MD',[r for r in rows if r]);p=collector_data('maryland','validation.json');o=json.loads(p.read_text());o.update(**balt_stats,**mde_stats,cutoff=CUT);p.write_text(json.dumps(o,indent=2)+'\n')
if __name__=='__main__' and '--city' in sys.argv:baltimore.download()
if __name__=='__main__' and '--city' not in sys.argv:
 if '--refresh' in sys.argv:
    for s in SOURCES:s.download()
 make()
