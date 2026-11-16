"""Puerto Rico permit history from the Junta de Planificación's MIPR Permisos GIS (sigejp.pr.gov), one module per issuing
register: OGPe SuperSIP cases (layer 2), OGPe SIP permits (layer 8), ARPE permits (layer 16) and Planning Board location
consultations (layer 20). They share one capture file and one build loop (common.py). --fetch re-downloads the register."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import argparse
from lib.files import j
from collectors.puerto_rico.common import build
from collectors.puerto_rico import ogpe_supersip_cases, ogpe_sip_permits, arpe_permits, planning_board_location_consultations
SOURCES=(ogpe_supersip_cases, ogpe_sip_permits, arpe_permits, planning_board_location_consultations)
def fetch():
 p=collector_data('puerto_rico','register.json');m=j(p) if p.exists() else {}
 for s in SOURCES:s.download(m,p)
 return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');options=p.parse_args()
 if options.fetch:fetch()
 print(len(build({s.LAYER:s for s in SOURCES})),'published Puerto Rico case dispositions')
