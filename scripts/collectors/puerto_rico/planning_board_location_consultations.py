"""Puerto Rico Junta de Planificación (Planning Board) location consultations: MIPR Permisos MapServer layer 20.
download() searches the layer; disposition() turns one reviewed, filed consultation into a published record."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.puerto_rico.common import fetch_layer, dateof
LAYER=20;FIELDS=['NOMBRE_PRO','DESCRIPCIO','NOMBRE_DUE','NOMBRE_P_1']
OUT_FIELDS='NUMERO_CAS,DESCRIPCIO,TIPO_CASO,MUNICIPIO,STATUS,DESCRIPC_1,FECHA_STAT'
JP='Puerto Rico Planning Board location consultations'
def download(m,p):fetch_layer(m,p,LAYER,FIELDS)
def disposition(a,num,review):
 if num in review['jp_cases'] and a['STATUS']=='RAC' and a.get('FECHA_STAT'):
  d=dateof(a['FECHA_STAT']);s=a['DESCRIPC_1'];typ=a['TIPO_CASO'];jur=a['MUNICIPIO'].split(' (')[0].title();project=review['jp_cases'][num];role='register status date (FECHA_STAT)';extra=dict(issuer='Junta de Planificación de Puerto Rico',procedure_code=a['TRAMITE'],source_project_text=a['DESCRIPCIO'],filed=dateof(a['FECHA_RADI']),issuer_level='territorial',decision_evidence='Register describes a clarification; not a construction or use permit.')
  return JP,d,s,typ,jur,project,role,extra
