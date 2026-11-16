"""City of Raleigh building permits (Building_Permits feature service). Issuer: City of Raleigh."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.north_carolina.evidence_store import epoch, gis_download, gis_rows
GIS=('https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Building_Permits/FeatureServer/0','proposedworkdescription,projectname,description,proposeduse,landusedescription','OBJECTID,permittypemapped,workclass,permitclass,proposedworkdescription,applieddate,issueddate,constcompletedofficial,coissueddate,expiresdate,countylocation,description,jurisdiction,jurisdiction_atissue,jurisdiction_inout_ral,landusedescription,originaladdress1,originalcity,projectname,proposeduse,statuscurrent,statuscurrentmapped,permitnum,voiddate')
def download():gis_download('raleigh',*GIS)
def parse(a):
 num=a['permitnum'];status=a['statuscurrent'] or a['statuscurrentmapped'];issued=epoch(a['issueddate']);scope='Raleigh';kind=(a['permittypemapped'] or 'Building')+' permit — '+str(a['workclass'] or '');d=dict(issuer='City of Raleigh',co_issue_date=epoch(a['coissueddate']),issue_date=issued,expiration_date=epoch(a['expiresdate']),applied_date=epoch(a['applieddate']),void_date=epoch(a['voiddate']),completed_flag=a['constcompletedofficial'],status_mapped=a['statuscurrentmapped'],jurisdiction_boundary=a['jurisdiction_inout_ral'],address=a['originaladdress1']);ds='Raleigh building permits'
 if a['countylocation']:d['county']=a['countylocation'].title()+' County'
 return num,status,issued,scope,kind,d,ds
def rows(events,held):gis_rows(events,held,'raleigh',GIS,GIS[1].split(','),parse)
