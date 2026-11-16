"""Oklahoma county/place geography for the data-center ranking: Census place boundaries and the PNNL IM3 atlas
(lib.geo), captured into the manifest and ranked into rank.json."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.geo import geofetch, rank
import lib.net as netfetch
import lib.discovery as collect
from collectors.oklahoma.common import ST, M
def download(m):
    if 'geo' not in m or netfetch.REFETCH:m['geo']=geofetch(ST,'40');collect.dump(M,m)
    rank(ST,m['geo'])
def rankings(m):rank(ST,m['geo'])
