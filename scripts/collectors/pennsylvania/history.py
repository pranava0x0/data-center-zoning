"""Pennsylvania permit history. One issuing source: the Pennsylvania DEP data-center project and authorization tracker, in dep_data_center_permit_tracker.py.
Same command-line flags as that module (offline replay by default)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import runpy
if __name__ == '__main__':
    runpy.run_module('collectors.pennsylvania.dep_data_center_permit_tracker', run_name='__main__')
