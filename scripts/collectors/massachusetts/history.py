"""Massachusetts permit history: combines the sources below into output/history/massachusetts/history.json. Offline by default; --refresh
re-downloads every source, and --fetch re-downloads only the Boston and Cambridge permit registers."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
from lib.records import CUT, save
import sys, json
from collectors.massachusetts import boston_building_permits as boston, cambridge_building_permits as cambridge, massdep_markley_air_approval as markley, mepa_project_certificates as mepa
def download():boston.download();cambridge.download()
if __name__=='__main__' and '--fetch' in sys.argv:download()
def make():
 a,boston_count=boston.rows();cp=cambridge.rows();rows=a+markley.rows()+mepa.rows()
 save('MA',[r for r in rows if r]);p=collector_data('massachusetts','validation.json');v=json.loads(p.read_text());v.update(boston_candidates=boston_count,cambridge_candidates=cp,cutoff=CUT);p.write_text(json.dumps(v,indent=2)+'\n')
if __name__=='__main__' and '--fetch' not in sys.argv:
 if '--refresh' in sys.argv:download();mepa.download()
 make()
