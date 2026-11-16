"""Tulsa Metropolitan Area Planning Commission (TMAPC): staff report for Z-7851, the Project Anthem rezoning request."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import io
from pypdf import PdfReader
from collectors.oklahoma.common import ST, capture
KEYS=('tulsa',)
def download(m):capture(m,KEYS)
def rows(m,out):
    r=m['tulsa'];t=' '.join(PdfReader(io.BytesIO(ST.read(r))).pages[1].extract_text().split())
    if 'staff recommends denial of the application' not in t:raise ValueError('Tulsa recommendation changed')
    out['Z-7851']=dict(id='ok-tulsa-z-7851',state='OK',dataset='Tulsa Metropolitan Area Planning Commission staff reviews',jurisdiction='Tulsa',record_no='Z-7851',project='Project Anthem data center campus',kind='AG to IL rezoning request',status='Staff recommends denial',date='2026-03-18',date_role='hearing date printed on staff report',url=r['url'],source_url=r['url'],locator='Z-7851 staff report, pp. 1–2; related CPA-128',details=dict(source_sha256=r['sha256'],evidence='staff recommends denial of the application',scope='Staff recommendation only; cover also says continued from 3/18/2026.'))
