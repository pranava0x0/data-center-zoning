"""City of Reno: issued permits ArcGIS feature layer. Any keyword match requires a normalization review."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.nevada.common import candidates, pull_layer
KEY='reno'
def download(m,stats):pull_layer(m,stats,KEY)
def rows(add,excluded):
 for a,n,o,loc,u in candidates(KEY,excluded):
  raise ValueError('New matched municipal source: review normalization for '+KEY)
