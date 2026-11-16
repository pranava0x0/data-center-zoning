"""Maricopa County air permit register (county air quality GIS layer), screened for data center facilities.
Issuer: Maricopa County Air Quality Department."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
def download(query,queries):gis_layer('air',query,queries)
def branch(b,k,n,x,a,oid,evidence):
    add=b.add;reject=b.reject
    no=a['permit_nbr']
    if not no or not re.fullmatch('P[0-9]+',no):reject.append([k,a['facility_id'],'Facility matches but no permit number']);return
    loc=(a.get('city') or 'Maricopa County').title()
    add(k,n,no,a['facility_nm'],'County air permit register / '+str(a['permit_classification_dsc'] or 'Unspecified'),a['permit_status_cd'] or 'Not stated',None,'Date not stated',loc,a['OnBaseWebLink'] or x['url'],'Facility ID '+a['facility_id']+', permit '+no,dict(evidence,issuer='Maricopa County Air Quality Department',county=a['county_nm']+' County' if a['county_nm'] else None,facility_id=a['facility_id'],facility_scope=a['facility_desc'],operating_status=a['operating_status_dsc'],permit_status_code=a['permit_status_cd'],publisher_key=a['OBJECTID']),key=a['facility_id']+'-'+no)
def rows(b):scan(b,'air',branch)
