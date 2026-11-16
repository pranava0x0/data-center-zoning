"""Vermont permit history. One issuing source: the Vermont ANR Act 250 docket and exhibits, in anr_act250_docket.py.
Same command-line flags as that module (offline replay by default)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import runpy
if __name__ == '__main__':
    runpy.run_module('collectors.vermont.anr_act250_docket', run_name='__main__')
