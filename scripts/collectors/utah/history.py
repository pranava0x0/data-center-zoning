"""Utah permit history: combines the sources below into output/history/utah/history.json. Offline replay by default;
--refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import sys, json
from lib.records import CUT, save
from collectors.utah import daq_air_permits as daq, bluffdale_planning_minutes as bluffdale, salt_lake_city_building_permits as slc
SOURCES=(slc, bluffdale, daq)
def make():
    a,qc=daq.rows();b=bluffdale.rows();c,slc_qc=slc.rows();qc.update(slc_qc)
    rows=a+b+c
    rows=[r for r in rows if r];save('UT',rows);v=collector_data('utah','validation.json');a=json.loads(v.read_text());a.update(source_counts=qc,cutoff=CUT,excluded_false_positive='DAQ document 164894: Uinta Wax gas-processing/dehydrator order at a historically named data-center power station; no demonstrated causal connection to a center.');v.write_text(json.dumps(a,indent=2)+'\n')
if __name__=='__main__':
    if '--refresh' in sys.argv:
        for s in SOURCES:s.download()
    make()
