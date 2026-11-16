"""City of Stillwater data-center project page. Captured into the manifest only; no records are published from it."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.oklahoma.common import capture
KEYS=('still',)
def download(m):capture(m,KEYS)
