"""Nevada Division of Environmental Protection (NDEP) air permitting: the Storey County applications table, the Switch
Class I director's review and the NOVVA Class II operating permit."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
import lib.text
from collectors.nevada.common import read, pages, plain, SOURCES, fetch_sources
NAMES=('ndep-air.html','switch.pdf','novva.pdf')
def download(m,stats):fetch_sources(m,NAMES)
def rows(add):
 n='ndep-air.html';source=read(n).decode();tab=re.search(r'<summary[^>]*>Storey</summary>.*?<table\b[^>]*>(.*?)</table>',source,re.S);assert tab and 'Official Date of Submittal' in tab[1]
 assert 'A2569' in pages('novva.pdf')[0] and 'NOVVA DATA CENTERS' in pages('novva.pdf')[0] and 'EXPIRES ON: Date' in pages('novva.pdf')[21]
 for tr in re.findall(r'<tr>(.*?)</tr>',tab[1],re.S):
  cells=[plain(td) for td in re.findall(r'<td[^>]*>(.*?)</td>',tr,re.S)]
  if not cells:continue
  dt,fin,permit,clas,case,name,kind,notice=cells
  if fin not in {'A2569','A1896A'}:continue
  add(n,n,case,name,kind,'Submitted',lib.text.isodate(dt),'Official Date of Submittal','Storey County','Storey > Air Case '+case,dict(county='Storey County',issuer='Nevada Division of Environmental Protection',facility_id=fin,permit_number=permit,permit_class=clas,identity_source=SOURCES['novva.pdf' if fin=='A2569' else 'switch.pdf']))
 n='switch.pdf';s=pages(n)[0];assert all(v in s for v in ['December 23, 2025','preliminary determination','AP7375-3672','A1896A'])
 add(n,n,'AP7375-3672','Switch, Ltd.','Class I air operating permit to construct revision','Preliminary determination','2025-12-23','Director’s review date','Storey County','p. 1, FIN A1896A',dict(county='Storey County',issuer='Nevada Division of Environmental Protection'))
