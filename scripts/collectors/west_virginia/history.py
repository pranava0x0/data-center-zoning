"""West Virginia permit history. One issuing source: West Virginia DEP permit applications, hearing notices and enforcement records, in wvdep_permit_records.py.
Same command-line flags as that module (offline replay by default)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import runpy
if __name__ == '__main__':
    runpy.run_module('collectors.west_virginia.wvdep_permit_records', run_name='__main__')
