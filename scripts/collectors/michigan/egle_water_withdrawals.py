"""Michigan EGLE water withdrawal determination for the Saline Township data center (SSR 10188-20264-23), as posted by Saline Township.
Issuer: Michigan Department of Environment, Great Lakes, and Energy."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.michigan.evidence_store import fetch_keys
KEYS=('saline_water',)
def download(m):fetch_keys(m,KEYS)
def rows(m,txt,add):
    add('saline_water',2,'you are hereby authorized to proceed with making the withdrawal','saline-water-ssr','Michigan EGLE water withdrawal determinations','Saline Township','SSR 10188-20264-23','Related Data Center','Site-specific water withdrawal review','Authorized','2026-04-24','determination date','EGLE letter p. 2, SSR 10188-20264-23',county='Washtenaw County',scope='Conditional groundwater withdrawal determination under Part 327; not a construction permit or proof of ongoing pumping.')
