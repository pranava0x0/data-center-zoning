"""Washington permit history. One issuing source: Washington Department of Ecology air construction dockets for Quincy, in ecology_quincy_air_dockets.py.
Same command-line flags as that module (offline replay by default)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import runpy
if __name__ == '__main__':
    runpy.run_module('collectors.washington.ecology_quincy_air_dockets', run_name='__main__')
