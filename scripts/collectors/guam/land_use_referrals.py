"""Offline extraction of dated Guam agency referrals in the commission's case packet."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R
import io
from pypdf import PdfReader
from lib.archive import Store
from lib.files import j
import lib.discovery as collect
S=Store('GU')
A=[('dpr','2021-24A/B','2021-10-18','Guam Department of Parks and Recreation','Conditional-use and height-variance referral','No objection',56,'to mitigate the adverse effects on historic properties','State Historic Preservation review and mitigation coordination.'),
   ('doag','2021-24B','2021-12-09','Guam Department of Agriculture','Height-variance referral','In support with conditions',55,'must be submitted with building permit for DOAG review','Bird-strike, erosion and flooding mitigation; not issuance of a building permit.'),
   ('gwa','2021-24B','2022-04-25','Guam Waterworks Authority','Height-variance referral recorded in agency summary','In favor with conditions',54,'GWA is in favor of the approval of the application with conditions','Pages 59–61 attach the agency letter; page 60 requires early utility coordination and demand calculations. Date is ARC summary date, not letter signature.'),
   ('gepa','2021-24B','2022-04-25','Guam Environmental Protection Agency','Height-variance referral recorded in agency summary','Concerns with conditions',54,'GEPA submits concerns related to the proposal with conditions','Agency concerns as recorded by ARC; not an environmental permit.')]
def build():
 m=j(collector_data('territories','gu_supp_sources.json'))['minutes'];pdf=PdfReader(io.BytesIO(S.read(m)));out=[]
 for key,case,d,issuer,kind,status,page,quote,detail in A:
  assert quote in ' '.join(pdf.pages[page-1].extract_text().split());out.append(dict(id='gu-arc-'+key+'-'+d,state='GU',dataset='Guam interagency land-use referrals',jurisdiction='Tamuning',record_no=case,project='Alupang Cable Landing Station and Data Center (TeleGuam Holdings dba GTA)',kind=kind,status=status,date=d,date_role='ARC agency-position summary date' if key in ('gwa','gepa') else 'agency memorandum date',url=m['url']+'#page='+str(page),source_url=m['url'],locator=f'Guam Land Use Commission May 12, 2022 packet; PDF page {page}; application {case}',details=dict(issuer=issuer,case_file=case,source_sha256=m['sha256'],evidence=quote,scope=detail)))
 collect.dump(series_path('guref_gu'),out);print(len(out),'agency referrals')
if __name__=='__main__':build()
