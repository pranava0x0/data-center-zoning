"""Saline Township, Washtenaw County: advisory committee updates and the consent judgment in case 2025-001577-CZ. Issuer: Saline Township."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.michigan.evidence_store import fetch_keys
KEYS=('saline_notes','saline_judgment','saline_counter','saline_court_index','saline_judgment_current')
def download(m):fetch_keys(m,KEYS)
def rows(m,txt,add):
    add('saline_notes',None,'Permits have been issued for Operations and Warehouse building foundations','saline-foundations','Saline Township advisory committee','Saline Township','April 29 advisory committee','Saline data center operations/warehouse buildings','Foundation permit issuance report','Issuance reported','2026-04-29','committee meeting date','April 29, 2026 update; no instrument IDs or issue dates published',county='Washtenaw County')
    sn='2025-001577-CZ';ref='Saline Township / RD Michigan Property Owner I';ds='Saline Township land use proceedings'
    for needle,suffix,day,kind,status,role in [('On August 14, 2025','application','2025-08-14','Final site-plan application','Submitted','application date'),('by a vote of 4 to 1, denied','denial','2025-09-10','Conditional rezoning request','Denied','township board vote'),('filed this action on September 12, 2025','filed','2025-09-12','Challenge to rezoning denial','Filed','court filing date'),('public information meeting on September 24, 2025','meeting','2025-09-24','Public information meeting','Held','meeting date')]:
        add('saline_judgment_current',4,needle,'saline-'+suffix,ds,'Saline Township',sn,ref,kind,status,day,role,'Township-posted execution copy, p. 4, findings n–q; case '+sn,county='Washtenaw County')
