"""City of Hilliard Planning and Zoning Commission minutes (June and July 2022 PDFs)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.ohio.common import get, add_document
KEYS=('hilliard_jun', 'hilliard_jul')
DATASET='Municipal planning decisions'
def download(c,m):
    for k in KEYS:m['docs'][k]=get(c['documents'][k],'pdf')
def add_record(add,r,ref):add_document(add,r,ref,DATASET,None)
