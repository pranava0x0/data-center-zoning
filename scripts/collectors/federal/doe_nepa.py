"""Reconstruct seven civilian DOE NEPA determinations and three site-specific land milestones.

Run offline by default. --fetch permits adding original bytes missing from the source archive.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path, series_paths
import argparse
from collections import defaultdict
from datetime import date
from urllib.parse import urljoin
from lib.url_archive import Archive
from collectors.federal.decisions import ENV, DEN
import lib.discovery as c

LAND='Department of Energy land and developer milestones'
BASE='https://www.energy.gov/nepa/articles/'
OH_FACT='https://www.energy.gov/articles/fact-sheet-department-energy-ensuring-affordable-energy-access-ohio-while-powering-future'
KY_SELECT='https://www.energy.gov/articles/energy-department-announces-partnership-expand-reliable-affordable-energy-access-and-power'
GEO={
 'CA':('https://www.energy.gov/sites/default/files/2026-03/ea-1975-sa-03-2023-12.pdf','unincorporated portion of San Mateo County','DOE/EA-1975-SA-03, §1.1, SLAC campus location'),
 'IL':('https://www.energy.gov/nepa/ea-1866-modernization-planning-argonne-national-laboratory-illinois','Argonne National Laboratory in DuPage County','DOE/EA-1866 introduction; location only'),
 'ID':('https://ioem.idaho.gov/wp-content/uploads/2020/05/idaho-ng911-esinet-recommendations-report-20200507-final.pdf','Engineering Research Office Building (EROB), Idaho Falls','State of Idaho report, printed p. 13, Bonneville county group; location only'),
}
PROJECT={
 'OH':('Pike County','Pike County','Portsmouth AI and cloud campus — Batch 1, near Piketon'),
 'KY':('McCracken County','McCracken County','Paducah data-center campus — Parcel B, near Kevil'),
 'CA':('San Mateo County','San Mateo County','Stanford Research Computer Facility at SLAC'),
 'ID':('Idaho Falls','Bonneville County','Idaho National Laboratory high-performance computing data center upgrade'),
 'IL':('DuPage County','DuPage County','Argonne Enterprise Data Center')
}
# ID, slug suffix, state, date, activity actually reviewed, applied class, locator, scope, original text anchors
CASES=[
 ('CX-270875','4511a-086-lease-real-property-batch-1-property-portsmouth-gaseous-diffusion','OH','2025-11-17','proposed land lease','B1.24','Signed form p. 1, 451.1a-086','DOE reviewed the proposed transfer by lease of the 189-acre Batch 1 property. The AI campus association is confirmed later by CX-270956 on the same parcel. This determination neither executes a lease nor reviews campus construction.',['proposes to lease 189 acres','Batch 1 Property','2025.11.17','Property transfers']),
 ('CX-270956','environmental-site-assessment-esa-batch-1-leased-property-portsmouth','OH','2026-04-29','site assessment','B3.1','Signed form p. 1, 451.1a-090','The phased lease requires assessment of the Batch 1 property to inform future feasibility, permitting, design and construction decisions. This environmental decision covers the assessment only.',['has leased approximately 189 acres','AI/Cloud Campus','will conduct and complete assessment activities','2026.04.29']),
 ('CX-270971','lease-real-property-leasing-parcel-b-paducah-gaseous-diffusion-plant','KY','2026-05-04','proposed land lease','B1.24','Signed form p. 1, 451.1a-087','DOE reviewed the proposed transfer by lease of 785-acre Parcel B. A later DOE assessment identifies the lessee of the same parcel. This decision covers transfer, not construction or lease execution.',['transfer of real property by lease','Leasing Parcel B','785 acres','2026.05.04']),
 ('CX-271104','site-characterization-and-environmental-monitoring-parcel-b-paducah-gaseous','KY','2026-11-02','site assessment','B3.1','Signed form p. 1, 451.1a-099','The action covers a Phase I records review and non-intrusive visit. A Phase II involving sampling is conditional on the Phase I findings. The decision does not authorize campus construction.',['has executed a lease agreement','785 acres','non-intrusive','If determined to be required','2026.11.02']),
 ('CX-008184','categorical-exclusion-determination','CA','2012-05-02','proposed new data-center building','B1.15','SS-SC-12-03, p. 1 scope, p. 3 determination','DOE applied the support-building exclusion to proposed construction of a 21,500-square-foot research computer facility with 3 MW of potential data-center capacity. This is environmental review, not evidence of a local building permit or operation.',['21,500 square feet','3 MW of data center potential','5/2/2012','Signature on File']),
 ('CX-012317','categorical-exclusion-determination','ID','2014-06-16','existing data-center cooling upgrade','B1.31','DOE-ID-INL-14-014, p. 1 scope, p. 2 approval','DOE reviewed installation of additional cooling equipment in an existing data center for a proposed newer computer. The 400 kW is additional heat load, not new electrical capacity or a new building.',['upgrade the existing EROB HPC Data Center','400 kW of additional heat load','DOE-ID-INL-14-014','6/16/2014']),
 ('CX-013962','categorical-exclusion-determination','IL','2015-07-15','proposed new data-center building','B1.15','DOE case record, dated July 15; ASO-CX-317, transmittal p. 1, project description p. 2','DOE reviewed the proposed 12,000-square-foot one-story Argonne Enterprise Data Center. The attached July 20 transmittal communicates the decision; DOE lists July 15 as the determination date. Changes in scope may require further review.',['Argonne Enterprise Data Center','no further NEPA review is required','12,000 s.f. data center','JUL 2 0 2015']),
]
CXR='Categorical exclusion determined'
def classify(r,cutoff,perm,no,app,obs):
    if r['dataset']==ENV:return no('DOE categorical exclusion for the specified activity; no site permit issued.','decision')
    if r['dataset']==LAND and r['status'] in {'Developer selected','Lease reported by DOE','Executed lease documented by DOE'}:
        return no('DOE developer selection or real-property lease record, not issuance of a regulatory permit.','decision')
    return None

def run(fetch=False):
    archive=Archive('doe_more',fetch,owner='federal/doe_nepa');cache={};state_rows=defaultdict(list);refs={}
    def source(url,*needles):
        if url not in cache:
            b,h=archive.get(url);fmt='application/pdf' if b.startswith(b'%PDF') else 'text/html'
            if fmt=='application/pdf':
                # The signed modern DOE forms place the proposed action and signature in AcroForm
                # appearances; preserve their text rather than using only static page content.
                import fitz
                with fitz.open(stream=b,filetype='pdf') as doc:txt=' '.join(p.get_text() for p in doc)
                links=[]
            else:_,txt,links=c.parse(b,fmt,url)
            cache[url]=(h,c.norm(txt),links)
        h,t,ls=cache[url]
        for s in needles:
            if c.norm(s) not in t:raise ValueError(f'Missing evidence {s!r}: {url}')
        return h,ls
    def add(state,key,record_no,register,kind,status,day,role,url,locator,scope,**details):
        place,county,project=PROJECT[state]
        if date.fromisoformat(day)>date(2026,11,15):raise ValueError('Outside snapshot cutoff')
        h,_=source(url)
        state_rows[state].append(dict(id='fed-doe-'+key,state=state,jurisdiction=place,county=county,dataset=register,record_no=record_no,project=project,kind=kind,status=status,date=day,date_role=role,url=url,source_url=url,source_sha256=h,locator=locator,details=dict(federal_issuer=DEN,scope=scope,**details)))
    for record,tail,st,day,activity,cat,loc,scope,anchors in CASES:
        page=BASE+record.lower()+'-'+tail;dt=date.fromisoformat(day);stamp=dt.strftime('%B')+' '+str(dt.day)+', '+str(dt.year)
        ph,links=source(page,record,stamp)
        pdfs={urljoin(page,href) for href,_ in links if href.lower().endswith('.pdf')}
        if len(pdfs)!=1:raise ValueError('Unexpected DOE document list: '+page)
        pdf=pdfs.pop();h,_=source(pdf,*anchors);refs[record]=(pdf,h)
        details=dict(agency_case_page=page,agency_case_sha256=ph,activity_reviewed=activity,exclusion_class=cat)
        if st in GEO:
            u,s,why=GEO[st];gh,_=source(u,s);details.update(location_source=u,location_sha256=gh,location_locator=why)
        else:
            details.update(location_source=pdf,location_sha256=h,location_locator='City/county/state field on form; recorded at county level without assuming parcel is inside named municipality.')
        if record in ('CX-270875','CX-270971'):
            details['parcel_crosscheck']='CX-270956' if st=='OH' else 'CX-271104'
        add(st,record.lower(),record,ENV,'NEPA categorical exclusion — '+activity,CXR,day,'DOE determination date',pdf,loc,scope,**details)
    # Separate published milestones. The record_no is a local documentary label, never an invented DOE lease ID.
    ky=source(KY_SELECT,'July 29, 2026','Brookfield was selected','data center campus','subject to approval by the Kentucky Public Service Commission')[0]
    add('KY','paducah-selection','Parcel B — developer selection',LAND,'Federal campus developer selection','Developer selected','2026-07-29','DOE selection announcement date',KY_SELECT,'DOE release, final two paragraphs','DOE announced Brookfield as campus developer and NextEra as energy infrastructure developer. Selection does not prove lease execution, state approval, or construction. The separate power-service agreement remained subject to state commission approval.',record_number_type='descriptive label; no DOE lease number supplied')
    certified,cert_hash=refs['CX-271104']
    add('KY','paducah-lease','Parcel B — Brookfield lease',LAND,'Federal land lease reported as executed','Executed lease documented by DOE','2026-11-02','DOE document date; not lease execution date',certified,'CX-271104 p. 1, opening sentence of proposed action; 451.1a-099','DOE confirms that it had executed a lease with Brookfield Artificial Intelligence Infrastructure General Partner LLC for approximately 785 acres. November 2 is a signed source date; the lease signature day is not given.',execution_date=None,lease_area_acres_approx=785,record_number_type='descriptive label; no DOE lease number supplied',campus_crosscheck=KY_SELECT,campus_source_sha256=ky)
    source(OH_FACT,'March 20, 2026','leasing federal land','in Pike County, Ohio','SB Energy-affiliated entity')
    certified,cert_hash=refs['CX-270956']
    add('OH','portsmouth-lease','Batch 1 — Portsmouth DC lease',LAND,'Federal land lease publicly reported','Lease reported by DOE','2026-03-20','DOE lease announcement date; not execution date',OH_FACT,'DOE fact sheet, first section; confirmatory CX-270956 p. 1','DOE described leasing federal land to an SB Energy affiliate. The April 29 signed form confirms Pike County Portsmouth DC LLC had leased approximately 189 acres. This is one lease observation; neither source supplies the lease signature day.',execution_date=None,lease_area_acres_approx=189,record_number_type='descriptive label; no DOE lease number supplied',lease_confirmation=certified,confirmation_sha256=cert_hash,confirmation_date='2026-04-29')
    rows=[r for rr in state_rows.values() for r in rr]
    if len({r['id'] for r in rows})!=10 or sum(r['dataset']==ENV for r in rows)!=7:raise ValueError('Missing, duplicate or unexpected DOE action')
    existing={r['record_no'] for p in [q for q in series_paths('land_') if q.exists()] for r in c.read(p,[]) if r['dataset']==ENV}
    if set(refs)&existing:raise ValueError('Duplicate DOE case in the earlier source')
    from collectors.federal.decisions import classify as existing_cx
    for r in rows:
        no=lambda reason,action:('non_permit',action); forbidden=lambda *args:(_ for _ in ()).throw(ValueError('Incorrect issuance '+r['id']))
        fn=existing_cx if r['dataset']==ENV else classify
        assert fn(r,date(2026,11,15),forbidden,no,forbidden,forbidden)==('non_permit','decision')
    for st,rr in state_rows.items():c.dump(series_path('doe_'+st.lower()),sorted(rr,key=lambda r:(r['date'],r['id'])))
    return {st:len(rr) for st,rr in sorted(state_rows.items())}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');print(run(p.parse_args().fetch))
