"""EPA ICIS-NPDES wastewater and stormwater permits for the Mississippi data center sites, joined to MDEQ's permit
numbers (mdeq_ensearch_permits.PROOFS). Issuer: EPA ICIS-NPDES (Mississippi DEQ permits)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.epa_icis import state_rows
from collectors.mississippi import mdeq_ensearch_permits as mdeq
def rows():
    return list(state_rows('MS',lambda f,p:mdeq.PROOFS.get(p['EXTERNAL_PERMIT_NMBR'])))
