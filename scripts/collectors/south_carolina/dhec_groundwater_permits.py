"""Berkeley County groundwater withdrawal permit 08IN015 and request for final review 19-RFR-48 (Maguro
Enterprises / Google), from the approved December 12, 2019 board minutes. Issuer: South Carolina Department of
Health and Environmental Control (DHEC; groundwater permitting is now with DES)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import json
S={'waterboard.pdf':'https://dph.sc.gov/sites/scdph/files/media/document/Board%20Minutes/2019-12-12-Minutes.pdf'}
def download(A):
 for n,url in S.items():A.fetch(n,url)
def rows(A):
 # Manually inspected image on page 9. Pin approved transcription to the original PDF digest.
 record=json.loads((collector_data('south_carolina','visual.json')).read_text());n='waterboard.pdf';assert record['sha256']==A.files[n]['sha256']
 cfg=dict(state='SC',dataset='South Carolina DHEC groundwater review',jurisdiction='Berkeley County',project='Maguro Enterprises (Google) — Berkeley County',url=S[n]+'#page=9',source_url=S[n],locator='Approved December 12, 2019 board minutes, item 10, pp. 9–10; 19-RFR-48',details={'county':'Berkeley County','issuer':'South Carolina Department of Health and Environmental Control','water_source_id':'08IN015G01','archive':'cache/history/sc/'+n,'archive_sha256':record['sha256'],'evidence':record['anchor']})
 return [dict(**cfg,id='sc-berkeley-groundwater-08in015',record_no='08IN015',kind='Groundwater withdrawal permit',status='Groundwater Withdrawal Permit',date=None,date_role='Issue date not stated in board minutes',),
  dict(**cfg,id='sc-berkeley-19-rfr-48',record_no='19-RFR-48',kind='Consent agreement on review of groundwater withdrawal permit',status='Request for Final Review withdrawn',date='2019-12-12',date_role='Board meeting date; not permit issuance date')]
