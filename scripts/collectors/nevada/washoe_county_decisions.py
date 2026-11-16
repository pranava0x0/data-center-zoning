"""Washoe County (Nevada): Board of County Commissioners and Planning Commission records for the Apple Sunol substation
and data center, plus the Northern Nevada Public Health air-permit notice."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.text
from collectors.nevada.common import read, pages, plain, fetch_sources
NAMES=('washoe-2015.pdf','washoe-2023.pdf','washoe-minutes.pdf','washoe-notice.html')
def download(m,stats):fetch_sources(m,NAMES)
def rows(add):
 wc={'county':'Washoe County','issuer':'Washoe County'}
 n='washoe-2015.pdf';s=pages(n)[0];assert all(x in s for x in ['SW11-003','large data center','SW15-001','7-0'])
 for no,desc,dt in [('SW11-003','large data center facility','2011-07-20'),('SW15-001','substation, switching yard and transmission lines','2015-02-03')]:
  add(n,n,no,'Apple / '+desc,'Special use permit','Approved',dt,'County decision date','Washoe County','p. 1, Previous Action / Background; '+no,wc)
 n='washoe-2023.pdf';s=pages(n)[4]
 for no,kind,status,dt,anchor in [('WSUP18-0010','Special use permit','Approved','2018-07-03','On July 3, 2018'),('WBLD23-102070','Building permit application','Submitted','2023-06-27','On June 27, 2023'),('WAC23-0012','Amendment of conditions','Submitted','2023-08-08','On August 8, 2023')]:
  assert no in s and anchor in s
  add(n,n,no,'Apple / Sunol substation',kind,status,dt,'Approval date' if status=='Approved' else 'Application date','Washoe County','p. 5, Background, '+no,dict(**wc,land_use_permit='WSUP18-0010'))
 n='washoe-minutes.pdf';s=pages(n)[12];assert all(v in s for v in ['WAC23-0012','vote of 6 for, 0','October 16, 2023'])
 add(n,n,'WAC23-0012','Apple / Sunol substation','Amendment of conditions','Approved with amended conditions','2023-10-16','Planning Commission vote date','Washoe County','p. 13, item 8C motion and vote',dict(**wc,land_use_permit='WSUP18-0010'))
 n='washoe-notice.html';s=plain(read(n).decode());assert 'June 13, 2025.' in s and 'Synthetic Minor Source Permit to Operate' in s
 add(n,n,'Apple notice 2025-06-13','Apple Inc.','Synthetic minor air permit modification notice','Proposed action','2025-06-13','Public notice date','Washoe County','June 13, 2025: notice and request for comment',dict(county='Washoe County',issuer='Northern Nevada Public Health'))
