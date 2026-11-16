"""Ohio EPA eDocument public portal: selected air and water permit PDFs (the ohio_air and ohio_water documents)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.ohio.common import get, add_document
KEYS=('ohio_air', 'ohio_water')
DATASET='Ohio EPA selected air and water permits'
def download(c,m):
    for k in KEYS:m['docs'][k]=get(c['documents'][k],'pdf')
def add_record(add,r,ref):add_document(add,r,ref,DATASET,'Licking County' if r['doc']=='ohio_water' else None)
