"""Replay FERC's actual orders for an identified data-center interconnection. Offline by default."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse
from lib.url_archive import Archive
import lib.discovery as c
ORDER='https://www.ferc.gov/sites/default/files/2024-11/20241101-3061_ER24-2172-000.pdf'
BRIEF='https://www.ferc.gov/sites/default/files/2025-10/25-60019_DocumentsSusquehanna.pdf'
GEO='https://www.nrc.gov/facilities-safety/facility-finder/reactors/susq1'
REG='FERC interconnection decisions'
def run(fetch=False):
 a=Archive('federal_power',fetch,owner='federal/ferc_orders')
 def read(u,anchors):
    b,sha=a.get(u);t=c.norm(c.parse(b,'application/pdf' if b.startswith(b'%PDF') else 'text/html',u)[1])
    for s in anchors:
        if c.norm(s) not in t:raise ValueError(s+' missing in '+u)
    return sha
 one=read(ORDER,['November 1, 2024','300 megawatts (MW) to 480 MW','data center','ORDER REJECTING AMENDMENTS','Luzerne County, Pennsylvania'])
 two=read(BRIEF,['191 FERC','Apr. 10, 2025','Rehearing Order','data center'])
 common=dict(state='PA',dataset=REG,jurisdiction='Luzerne County',county='Luzerne County',project='Susquehanna data center power agreement')
 rows=[]
 for suffix,num,url,sha,day,kind,status,pages,note in [
 ('amendment','ER24-2172-000',ORDER,one,'2024-11-01','Grid interconnection amendment','Rejected','189 FERC ¶ 61,078, order ¶¶ 1–2 and ordering paragraph','The proposed agreement would raise power supplied to the adjacent data center from 300 to 480 MW. FERC rejected this filing; the order did not revoke the existing agreement or decide local zoning.'),
 ('rehearing','ER24-2172-002',BRIEF,two,'2025-04-10','Grid interconnection rehearing','Rehearing order issued','FERC appellate brief, printed pp. 9 and 15–16; 191 FERC ¶ 61,025','FERC addressed rehearing of the 2024 rejection. This date is the order date cited in the agency brief, not its October filing date. No construction permit or current operating limit is inferred.')]:
    rows.append(dict(**common,id='fed-susquehanna-'+suffix,record_no=num,url=url,source_url=url,source_sha256=sha,date=day,date_role='FERC order date',kind=kind,status=status,locator=pages,details=dict(federal_issuer='Federal Energy Regulatory Commission',scope=note,location_evidence=ORDER,location_sha256=one,location_locator='Order p. 4, ¶ 6; generating station county',additional_location_reference=GEO,location_scope='Site of the generating station in the interconnection agreement; not a determination of campus parcel boundaries.')))
 c.dump(series_path('fpower_pa'),rows);print('Two FERC decisions; no new instrument counted.')
def classify(r,cutoff,perm,no,app,obs):return no('Federal power agreement proceeding; neither order issued a site permit.','decision')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
