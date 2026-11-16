"""City of Centennial (ArcGIS address points and History_EPL project layer): proof that 12500 E Arapahoe Rd lies in
Centennial, and the narrative project search that must return nothing. Publishes no records of its own."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.files import pack, unpack
from lib.arcgis import snapshot as arc
from lib.terms import pred
from lib.net import get_simple as get, query
from lib.paths import CACHE
import json
D=CACHE/'co'
CENT='https://maps.centennialco.gov/arcgis/rest/services'
def download():
    D.mkdir(exist_ok=True,parents=True)
    addr=query(CENT+'/Address_Points/FeatureServer/0/query',where="UPPER(FULLADDR) LIKE '12500%ARAPAHOE%' OR UPPER(FULLADDR) LIKE '11900%CORNELL%'",outFields='OBJECTID,PARCEL_ID,FULLADDR,PIN,City',outSR=4326,returnGeometry='true',f='json');j=json.loads(get(addr));pack(D/'centennial-address.json.gz',dict(url=addr,rows=j['features']))
    arc(CENT+'/History_EPL/MapServer/0',pred(['PROJECTNAME','WORKCLASS'])+" OR UPPER(PROJECTNAME) LIKE '%FLEXENTIAL%'",['OBJECTID','CASENUMBER','CASEID','APPLICATIONDATE','PROJECTNAME','WORKCLASS','CaseType','Link','MODULENAME','SPATIALID'],D/'centennial-projects.json.gz')
def rows():
    """Address-point proof used by the state air rows, and the narrative-search count the validation file reports."""
    cent=unpack(D/'centennial-address.json.gz')
    if unpack(D/'centennial-projects.json.gz')['rows']:raise ValueError('New narrative matches require review')
    return cent,unpack(D/'centennial-projects.json.gz')['count']
