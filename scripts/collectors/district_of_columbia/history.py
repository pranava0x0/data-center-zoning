"""District of Columbia permit history. One issuing source: the Department of Buildings (DOB) building permit register, in dob_building_permits.py.
Same command-line flags as that module (offline replay by default)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import runpy
if __name__ == '__main__':
    runpy.run_module('collectors.district_of_columbia.dob_building_permits', run_name='__main__')
