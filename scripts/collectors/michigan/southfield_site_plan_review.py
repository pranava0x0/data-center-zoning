"""City of Southfield, Oakland County: Planning Commission review of PSP25-0009 (Metrobloks, 27252 Inkster Road), annual report and city statement.
Issuer: City of Southfield."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.michigan.evidence_store import fetch_keys
KEYS=('south_annual','south_statement','south_agenda','south_minutes')
def download(m):fetch_keys(m,KEYS)
def rows(m,txt,add):
    city='City of Southfield site-plan review'
    add('south_minutes',133,'a favorable recommendation for PSP25-0009','southfield-recommend',city,'Southfield','PSP25-0009','Metrobloks, 27252 Inkster Road','Site plan recommendation','Favorable recommendation','2025-11-19','planning commission meeting','Transcript p. 133; motion and voice vote',county='Oakland County',county_source=m['south_statement']['url'])
    add('south_annual',3,'To construct a new data center.','southfield-approval',city,'Southfield','PSP25-0009','Metrobloks, 27252 Inkster Road','Site plan review','Approved',None,'exact vote date not established','Approved 2025 annual report p. 3; confirmation from December 19 city statement',county='Oakland County',corroboration=m['south_statement']['url'],approved_by='2025-12-19')
