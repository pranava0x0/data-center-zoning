"""Federal Energy Regulatory Commission (FERC): preliminary permit application P-15423 (DeepGreen, Cook Inlet), from
its Federal Register notice."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.alaska.evidence_store import A, adder, pdf
S={'cook.pdf':'https://www.govinfo.gov/content/pkg/FR-2026-09-04/pdf/2026-18151.pdf'}
def download():
 for n,u in S.items():A.fetch(n,u)
def rows(out):
 add=adder(out)
 t=pdf('cook.pdf');assert 'February 11, 2026' in t and 'does not authorize the permit holder to perform any land-disturbing activities' in t
 for dt,stat,role in [('2026-02-11','Application filed','FERC filing date'),('2026-06-26','Application supplemented','Supplement filed'),('2026-09-04','Accepted for filing','Federal Register publication date')]:
  add('cook.pdf','FERC preliminary permit applications','15423-000','DeepGreen Cook Inlet subsea-compute and tidal energy feasibility study','Alaska','Preliminary hydrokinetic permit application',stat,dt,role,'91 FR 56879; hydrokinetic generation paired with subsea compute. Not permission to build.',issuer='Federal Energy Regulatory Commission')
