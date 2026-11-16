"""City of South Fulton (Georgia) Community Zoning Information Meeting agenda (Vantage Data Centers rezoning Z26-003)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import lib.discovery as collect
from collectors.georgia.evidence_store import R, get, j, pdfpages, row
def download():
    xp=collector_data('georgia','local_extra.json')
    if not xp.exists():collect.dump(xp,{'southfulton':get('https://www.cityofsouthfultonga.gov/DocumentCenter/View/15137/CZIM-Agenda_02_2_26','pdf')})
def rows():
    out=[]
    extra=j(collector_data('georgia','local_extra.json'));ref=extra['southfulton'];t=pdfpages(ref['sha256'])[0]
    assert 'Z26-003' in t and 'Vantage Data Centers' in t
    out.append(row('City of South Fulton zoning information meeting','south-fulton-z26-003','South Fulton','Z26-003','Vantage Data Centers Ga 21 LLC','Rezoning request','Request on agenda','2026-02-02','scheduled meeting date',ref,'Community Zoning Information Meeting agenda p. 1; Z26-003',identity_evidence='Vantage Data Centers Ga 21 LLC'))
    return out
