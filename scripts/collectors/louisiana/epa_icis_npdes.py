"""EPA ICIS-NPDES facility records for Louisiana (the identity and location crosswalk for DEQ LPDES rows), with the Rayville
Project Sucre and Project Cypress facilities accepted by their named developers."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from lib.epa_icis import state_rows
from collectors.louisiana.usace_vicksburg_regulatory_notices import SUCRE
CYP='https://lpscpubvalence.lpsc.louisiana.gov/portal/PSC/ViewFile?fileId=6PaAyqAncwA%3D'
def accept(f,p):
    nm=f['FACILITY_NAME']
    if f['COUNTY_CODE']=='LA083' and f['CITY']=='RAYVILLE':
        if re.search(r'project sucre',nm,re.I) and re.search(r'laidley|mortenson',nm,re.I):return SUCRE
        if re.search(r'project cypress',nm,re.I) and re.search(r'evest|mortenson',nm,re.I):return CYP
def rows():
    return list(state_rows('LA',accept))
