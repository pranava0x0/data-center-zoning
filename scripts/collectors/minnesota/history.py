"""Minnesota permit history: combines the state and city sources below into output/history/minnesota/history.json.
Offline replay by default; --refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import json, sys
from lib.records import save, CUT
from collectors.minnesota import eqb_environmental_reviews as eqb, minneapolis_building_permits as mpls, chaska_council_decisions as chaska
SOURCES=(eqb, mpls, chaska)
def make():
    a,eqb_stats=eqb.rows();b,mpls_stats=mpls.rows();c=chaska.rows()
    rows=[r for r in a+b+c if r];save('MN',rows)
    vf=collector_data('minnesota','validation.json');v=json.loads(vf.read_text());v.update(**eqb_stats,**mpls_stats,cutoff=CUT);vf.write_text(json.dumps(v,indent=2)+'\n')
if __name__=='__main__':
    if '--refresh' in sys.argv:
        for s in SOURCES:s.download()
    make()
