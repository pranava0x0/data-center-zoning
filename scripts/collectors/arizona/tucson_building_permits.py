"""City of Tucson commercial building permits (Tucson GIS layer), screened for data centers.
Issuer: City of Tucson Planning and Development Services."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
def download(query,queries):gis_layer('tucson',query,queries)
def branch(b,k,n,x,a,oid,evidence):
    add=b.add
    no=a['NUMBER'];dt=date(a['ISSUEDATE']) or date(a['APPLYDATE'])
    add(k,n,no,a['PROJECTNAME'] or a['ADDRESS'],a['WORKCLASS'] or a['TYPE'],a['STATUS'],dt,'Issue date' if a['ISSUEDATE'] else 'Application date','Tucson',a['PRO_URL'] or a['CSS_URL'],'NUMBER '+no,dict(evidence,work_description=a['DESCRIPTION'],application_date=date(a['APPLYDATE']),completion_date=date(a['COMPLETEDATE'])))
def rows(b):scan(b,'tucson',branch)
