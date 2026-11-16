"""Puerto Rico OGPe legacy SIP permit register (Permisos SIP Todos): MIPR Permisos MapServer layer 8.
Searched for data-center terms only; rows are held (no reviewed disposition), so disposition() publishes nothing."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.puerto_rico.common import fetch_layer
LAYER=8;FIELDS=['NombreProy','Dueno']
OUT_FIELDS=''
def download(m,p):fetch_layer(m,p,LAYER,FIELDS)
def disposition(a,num,review):return None
