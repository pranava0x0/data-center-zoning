"""City of Tempe building safety permits (Tempe GIS layer), screened for data centers.
Issuer: City of Tempe Community Development, Building Safety."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
def download(query,queries):gis_layer('tempe',query,queries)
def branch(b,k,n,x,a,oid,evidence):
    add=b.add
    no=a['PermitNum'];dt=date(a['IssuedDate']) or date(a['AppliedDate'])
    link=x['url']+'/query?'+urlencode({'where':"PermitNum = '"+no+"'","outFields":x['fields'],'returnGeometry':'false','f':'pjson'})
    add(k,n,no,a['ProjectName'] or a['OriginalAddress1'],a['PermitTypeDesc'] or a['PermitType'],a['StatusCurrent'],dt,'Issue date' if a['IssuedDate'] else 'Application date','Tempe',link,'PermitNum '+no,dict(evidence,work_description=a['Description'],completion_date=date(a['CompletedDate']),status_date=date(a['StatusDate']),co_date=date(a['COIssuedDate'])))
def rows(b):scan(b,'tempe',branch)
