"""City-County of Durham building permits (Inspections MapServer layer 12). Issuer: Durham City-County Inspections."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.north_carolina.evidence_store import epoch, gis_download, gis_rows
GIS=('https://webgis.durhamnc.gov/server/rest/services/PublicServices/Inspections/MapServer/12','COMMENTS,DESCRIPTION,PROJECT_NAME,PROJECT_TYPE','OBJECTID,PARCEL_ID,PermitNum,ISSUE_DATE,CO_SIGNOFF_DATE,COMMENTS,DESCRIPTION,PROJECT_NAME,PROJECT_TYPE,BLDB_ACTIVITY,BLD_Type,Occupancy,TYPE,PmtStatus')
def download():gis_download('durham',*GIS)
def parse(a):
 num=a['PermitNum'];status=a['PmtStatus'];issued=epoch(a['ISSUE_DATE']);co=epoch(a['CO_SIGNOFF_DATE']);scope='Durham County';kind='Building permit — '+str(a['BLDB_ACTIVITY'] or a['TYPE']);d=dict(county=scope,issuer='Durham City-County building inspections',co_signoff_date=co,issue_date=issued,building_type=a['BLD_Type'],occupancy=a['Occupancy']);ds='Durham City-County building permits'
 return num,status,issued,scope,kind,d,ds
def rows(events,held):gis_rows(events,held,'durham',GIS,['DESCRIPTION','PROJECT_NAME','PROJECT_TYPE'],parse)
