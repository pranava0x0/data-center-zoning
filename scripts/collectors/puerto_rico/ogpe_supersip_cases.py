"""Puerto Rico OGPe (Oficina de Gerencia de Permisos) SuperSIP case register: MIPR Permisos MapServer layer 2.
download() searches the layer; disposition() turns one reviewed, approved register row into a published record."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.puerto_rico.common import fetch_layer, dateof
LAYER=2;FIELDS=['NomProy']
OUT_FIELDS='Caso,Siglas,NomProy,Estado,Municipio,Agencia,Radicado,F_Estado,Tramite'
OG='Puerto Rico OGPe SuperSIP case register'
KINDS={'PCO':'Permiso de Construcción','PCOC':'Permiso de Construcción Consolidado','PGE':'Permiso para Generadores de Electricidad','PCT':'Permiso de Corteza Terrestre','PU':'Permiso Único','DEC':'Determinación de Cumplimiento Ambiental vía Exclusión Categórica','PCE':'Pre-Consulta - Edificabilidad','PCD':'Pre-Consulta - Departamento de Evaluación de Cumplimiento Ambiental','PCM':'Pre-Consulta - Medioambiente','SRI':'Solicitud de Recomendación - Infraestructura','SRS':'Solicitud de Recomendación - Salud y Seguridad'}
def download(m,p):fetch_layer(m,p,LAYER,FIELDS)
def disposition(a,num,review):
 if num and num.split('-')[1] in review['approved_project_prefix']:
  prefix=num.split('-')[1];assert (a['NomProy'] or '').startswith(review['approved_project_prefix'][prefix]);s=a['Estado'];code=a['Siglas']
  # Agency registration status and dated project use must both be positive. No permit is inferred from an "inactive" or "archived" file.
  if s=='PERMIT_APPROVED' and code in KINDS or s=='EXPIRED' and code=='PU' or s=='PERMIT_CLOSED' and code=='SRI':
   d=dateof(a['F_Estado']);typ=KINDS[code];jur=a['Municipio'];project=review['approved_project_prefix'][prefix];role='register status date (F_Estado)';extra=dict(issuer=a['Agencia'],procedure_code=code,source_project_text=a['NomProy'][:425],filed=dateof(a['Radicado']),project_prefix=prefix,issuer_level='territorial',decision_evidence='Official case register disposition; signed instrument not archived.')
   return OG,d,s,typ,jur,project,role,extra
