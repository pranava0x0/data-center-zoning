"""Puerto Rico ARPE (Administración de Reglamentos y Permisos) permit register: MIPR Permisos MapServer layer 16.
Searched for data-center terms only; ARPE rows carry no decision status here, so disposition() publishes nothing."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.puerto_rico.common import fetch_layer
LAYER=16;FIELDS=['NOMBRE','DESCRIP','USO','DUEÑO','PROPONENTE']
OUT_FIELDS=''
def download(m,p):fetch_layer(m,p,LAYER,FIELDS)
def disposition(a,num,review):return None
