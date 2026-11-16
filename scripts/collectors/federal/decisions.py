"""Replay individually located federal decisions. Federal land grants are distinct from NEPA reviews."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, collections, re
from lib.url_archive import Archive
import lib.discovery as c
BLM='https://eplanning.blm.gov/Project-Home/?id=f4dd06fc-446f-f111-ab0d-001dd802f839'
BOARD='https://www.bcnv.org/DocumentCenter/View/17364/2026-0213-Boulder-City-Stay-Granted'
CITY='https://www.bcnv.org/CivicAlerts.aspx?AID=534'
DOE='https://www.energy.gov/sites/default/files/2025-11/CX-034617.pdf'
GRID='https://www.energy.gov/nepa/articles/cx-035792-data-center-flexibility-grid-enhancing-technology'
GPDF='https://www.energy.gov/sites/default/files/2026-07/CX-035792.pdf'
DEN='Department of Energy';LAND='Interior Department land decisions';ENV='Department of Energy NEPA determinations'
def run(fetch=False):
 a=Archive('federal_cases',fetch,owner='federal/decisions');out=collections.defaultdict(list)
 def get(u,*anchors):
    b,h=a.get(u);t=' '.join(c.parse(b,'application/pdf' if b.startswith(b'%PDF') else 'text/html',u)[1].lower().split())
    for needle in anchors:
        if needle.lower() not in t:raise ValueError('Missing evidence '+needle+' at '+u)
    return h
 def row(k,st,loc,co,agency,register,num,title,kind,status,day,role,url,sha,locator,scope,**extra):
    out[st].append(dict(id='fed-case-'+k,state=st,jurisdiction=loc,county=co,dataset=register,record_no=num,project=title,kind=kind,status=status,date=day,date_role=role,url=url,source_url=url,source_sha256=sha,locator=locator,details=dict(federal_issuer=agency,scope=scope,**extra)))
 h=get(BLM,'NVNV106360814','6/26/2026','Clark County','Rights-of-Way');o=get(BOARD,'IBLA 2026-0213','Stay Granted','June 26, 2026','September 1, 2026','BLM approved an amended right-of-way');ch=get(CITY,'City of Boulder City’s jurisdiction')
 common={'state_authority':False,'same_land_case':'NVNV106360814','appeal_dockets':['IBLA 2026-0213','IBLA 2026-0216'],'municipal_location_source':CITY,'municipal_source_sha256':ch}
 row('townsite-grant','NV','Boulder City','Clark County','Bureau of Land Management',LAND,'NVNV106360814','Townsite Data Center','Federal right-of-way amendment','Approved; subsequently stayed','2026-06-26','BLM decision date',BLM,h,'Project Dates and Case File Number; IBLA order p. 1','BLM amended a solar-project right-of-way to allow a data center. The September 1 order stayed that decision.',appeal_order=BOARD,appeal_sha256=o,**common)
 row('townsite-stay','NV','Boulder City','Clark County','Interior Board of Land Appeals',LAND,'NVNV106360814','Townsite Data Center','Stay of federal land grant','Stay granted pending appeal','2026-09-01','Order date',BOARD,o,'IBLA 2026-0213 and 2026-0216, p. 1 and concluding order','The Board stayed the June grant while two appeals proceed. A stay does not cancel the underlying grant or decide the merits.',**common)
 h=get(DOE,'Interim Classified Data Center Project','Aiken/Aiken County/South Carolina','09/22/2025','B1.15 SUPPORT BUILDINGS')
 row('aiken-cx','SC','Aiken County','Aiken County',DEN,ENV,'CX-034617','Savannah River Site data center','Categorical exclusion under NEPA','Categorical exclusion determined','2025-09-22','Determination date',DOE,h,'Determination form p. 1, proposed action and date','DOE determined that the new server facility qualified for a categorical exclusion. This decision does not grant a building or operating permit.')
 h=get(GRID,'April 22, 2026','Virginia (Iron Mountain)','South Carolina (Grace Complex)');p=get(GPDF,'CATEGORICAL EXCLUSION')
 for st,name,site in [('VA','Virginia','Iron Mountain'),('SC','South Carolina','Grace Complex')]:
    row('grid-cx-'+st.lower(),st,name,'',DEN,ENV,'CX-035792',site+' data center microgrid','Categorical exclusion under NEPA','Categorical exclusion determined','2026-04-22','DOE decision date',GRID,h,'CX-035792, project description and determination date','DOE reviewed one project at two existing sites. Each state card describes the same federal environmental decision; neither card is an issued permit.',shared_decision='DOE:CX-035792',determination_form=GPDF,form_sha256=p)
 for st,rr in out.items():c.dump(series_path('land_'+st.lower()),rr)
 print(sum(map(len,out.values())),'geographic filings;',len(out),'states.')
def classify(r,cutoff,perm,no,app,obs):
 if r['dataset']==ENV:return no('NEPA categorical exclusion, not a construction or operating permit.','decision')
 if r['dataset']==LAND:
    from datetime import date
    return perm('NV:blm-row','unconfirmed','The original grant was stayed. No final disposition after the stay has been established.',date.fromisoformat(r['date']))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--fetch',action='store_true');run(a.parse_args().fetch)
