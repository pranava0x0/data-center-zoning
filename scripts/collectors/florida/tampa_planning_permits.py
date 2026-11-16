"""City of Tampa: PermitsAll ArcGIS layer. Fetched for the raw-hit counts in the coverage file only; it produces no
history rows."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.florida.common import stage_keys
KEYS=('tampa',)
def download(c,m):stage_keys(c,m,KEYS)
