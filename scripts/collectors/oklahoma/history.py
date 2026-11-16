"""Oklahoma permit history, one module per issuing source: Oklahoma DEQ consolidated data-center register
(deq_data_center_register), its air-permit applications (deq_air_permit_applications) and final instruments
(deq_final_instruments), the Tulsa Metropolitan Area Planning Commission staff report (tulsa_planning_commission),
the Stillwater project page (captured only), and the geo ranking. Shared manifest and build step are in common.py.
--fetch re-downloads; --ocr rebuilds the cover-page OCR."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse
from lib.files import j
from collectors.oklahoma.common import M, build
from collectors.oklahoma import census_pnnl_rankings as geo, deq_data_center_register as register, deq_final_instruments, tulsa_planning_commission as tulsa, stillwater_data_center_project as stillwater
def stage(m):
    geo.download(m)
    register.stage(m);tulsa.download(m);stillwater.download(m)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--ocr',action='store_true');a=p.parse_args();m=j(M) if M.exists() else {}
    if a.fetch:stage(m);register.download(m)
    if a.ocr:deq_final_instruments.ocr(m)
    build(m,geo,register,tulsa)
