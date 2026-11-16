import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.config_collector import cli
if __name__=='__main__':cli('ID','16')
