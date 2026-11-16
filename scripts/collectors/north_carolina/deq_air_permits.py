"""North Carolina DEQ Division of Air Quality: statewide active air permit register (all_permitted.xlsx) and the
Amazon/Duke air permit public hearing notice. Issuer: NC DEQ Division of Air Quality."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import io
from concurrent.futures import ThreadPoolExecutor
import openpyxl
from lib.text import plain
from collectors.north_carolina.evidence_store import A, iso, add
SRC={'air.xlsx':'https://files.nc.gov/deq/Air%20Quality/permits/aapa_reports/all_permitted.xlsx','air-index.html.gz':'https://www.deq.nc.gov/about/divisions/air-quality/air-quality-permitting','hamlet.html.gz':'https://www.deq.nc.gov/news/press-releases/2026/08/28/ncdeqs-division-air-quality-requires-additional-monitoring-testing-final-air-quality-permits-amazon','richmond-hearing.html.gz':'https://www.deq.nc.gov/news/events/public-hearing-preliminary-determination-air-quality-permit-applications-amazon-data-services-and'}
def download():
 def get(item):n,u=item;b=A.fetch(n,u);assert len(b)>1000,(u,len(b))
 with ThreadPoolExecutor(3) as ex:list(ex.map(get,SRC.items()))
def rows(events):
 wb=openpyxl.load_workbook(io.BytesIO(A.read('air.xlsx')),read_only=True,data_only=True);it=iter(wb.active.values);assert next(it)[0]=='All Active Air Permits in North Carolina';hdr=next(it);assert hdr[12]=='Permit #'
 sources={'7700104':SRC['hamlet.html.gz'],'7700070':SRC['hamlet.html.gz'],'1800557':'https://www.catawbacountync.gov/site/assets/files/9936/fy24_adopted_budget.pdf','1800599':'https://www.conovernc.gov/192/Developments','1800601':'https://www.catawbacountync.gov/news/joint-statement-on-microsoft-data-center-development-in-catawba-county/','1800602':'https://www.catawbacountync.gov/news/joint-statement-on-microsoft-data-center-development-in-catawba-county/','1400204':'https://www.deq.nc.gov/draft-permit-review-tapaha-dynamics-llc/open'}
 for i,r in enumerate(it,3):
  name,fid=r[0:2]
  if fid not in sources:continue
  assert r[11]=='7374' or fid=='7700070';num=r[12];j=r[7]+' County';d=dict(county=j,issuer='North Carolina DEQ Division of Air Quality',facility_id=fid,facility_city=r[4],sic=r[11],expiration_date=iso(r[16]),issue_date=iso(r[15]),sector_source=sources[fid],archive='cache/history/nc/air.xlsx',archive_sha256=A.files['air.xlsx']['sha256'],role='Dedicated electricity supply' if fid=='7700070' else 'On-site data processing facility')
  add(events,'nc-air-'+num,'NC DEQ active air permit register',num,name,j,r[14]+' air permit','All Active Air Permits in North Carolina',iso(r[15]),'State register issue date',r[13],SRC['air.xlsx'],'Facility ID '+fid+', workbook row '+str(i),d)
  if fid in ('7700104','7700070'):
   a='richmond-hearing.html.gz';assert 'July 30, 2026' in plain(A.read(a).decode())
   add(events,'nc-hearing-'+num,'NC DEQ air hearing notices',num,name,j,'Air permit application hearing','Public Hearing','2026-07-30','Scheduled public hearing',SRC[a],SRC[a],'Amazon / Duke public hearing July 30; number linked by facility in final register',{**d,'archive':'cache/history/nc/'+a,'archive_sha256':A.files[a]['sha256']})
