"""Shelby County, Tennessee: Shelby County Health Department Air Pollution Control permit 01156-01PC (signed permit page, Internet
Archive copy plus corroborating copy) and the Shelby County Planning and Development (Accela) current-projects ArcGIS layer
screened for sector terms. Issuers: Shelby County Health Department; Shelby County Division of Planning and Development."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from collectors.tennessee.evidence_store import D, R, j, read, fetch_layers, fetch_documents
LAYERS=('shelby',);DOCS=('internet_archive','permit_copy')
def download(c,m):fetch_layers(c,m,LAYERS);fetch_documents(c,m,DOCS)
def rows(m,add):
    r=m['docs']['internet_archive'];other=m['docs']['permit_copy'];ocr=j(collector_data('tennessee','air_scan.json'))
    if read(r,True)!=read(other,True) or ocr['sha256']!=r['sha256']:raise ValueError('Signed Shelby document identity mismatch')
    normalized=''.join(' '.join(ocr['lines']).lower().split())
    if not all(w in normalized for w in ('01156-01pc','july2,2025','january2,2027','ctcpropertyllc')):raise ValueError('Signed permit page mismatch')
    add('shelby-air-01156-01pc','Shelby County Health Department air permits','Memphis','01156-01PC','CTC Property LLC / Colossus','Air construction permit','Issued','2025-07-02','issuance date',r['url'],'Signed permit page 1, permit no. 01156-01PC',r,dict(county='Shelby County',agency='Shelby County Health Department – Air Pollution Control',expiration_date='2027-01-02',original_url='https://www.shelbytnhealth.com/DocumentCenter/View/7174/01156-01PC-070225Permit',corroborating_copy=other['url'],address='3231 Paul R Lowry Road, Memphis, TN 38109',scope='Fifteen natural gas-fired turbines, each 16.48 MW. Construction authority only.'))
