"""Typed conditions from reviewed pages; keep the unit, comparator and exceptions with each number."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import fitz
import lib.discovery as c
# Exact page anchors, including numerical expressions, are checked against the pinned PDF.
MEASURES={
'tx-mcallen-parking':[('minimum_parking', '>=',1,'space / 1,000 ft2','Minimum requirement on the data center row of the I-2 use table.',44,'Data Center C 1/1,000 SF')],
'ga-monroe-home-distance':[('residential_setback','>=',500,'ft','Data center building to residential structure.',66,'five-hundred feet (500'),('perimeter_buffer','>=',100,'ft','Dense vegetation and sound abatement required.',66,'one-hundred-foot (100')],
'ga-monroe-outreach':[('outreach_meetings','>=',2,'meetings','Public meetings before the conditional use application.',66,'minimum of two (2) public outreach'),('meeting_lead_time','>=',6,'months','Before filing the conditional use application.',66,'no less than 6 months'),('owner_notice_radius','within',500,'ft','Notify owners within this distance of the site.',66,'property owners within five-hundred feet (500')],
'ga-habersham-lot':[('minimum_data_center_lot','>=',5,'acres','Applies to the data center.',96,'No data center shall be erected on any lot less than five acres'),('minimum_power_plant_lot','>=',20,'acres','Applies to a data center power plant.',96,'lot less than twenty acres')],
'ga-habersham-residences':[('residential_setback','>=',1000,'ft','To residentially zoned lots and existing residences.',96,'one thousand (1,000) feet from all residentially zoned lots'),('other_setback_floor','>=',60,'ft','Property lines and public road rights-of-way: the greater of 60 feet or 1.25 times structure height.',96,'at least sixty (60) feet')],
'ga-habersham-sound':[('measurement_locations','=',8,'locations','Around the site boundary; existing baseline sound study.',97,'eight (8) locations'),('report_deadline','<=',30,'days','From completion of the study to delivery to the planning department.',97,'within thirty (30) days of completion')],
}
def add(rows):
 ix=c.read(c.INDEX,{});out=[]
 for r in rows:
    if r['id'] not in MEASURES:continue
    sha=ix[c.address(r['url'])]['sha256'];b=(c.CACHE/(sha+'.bin')).read_bytes();assert c.digest(b)==sha
    pdf=fitz.open(stream=b,filetype='pdf');typed=[]
    for metric,op,v,unit,ctx,page,anchor in MEASURES[r['id']]:
        assert c.norm(anchor) in c.norm(pdf[page-1].get_text()),(r['id'],metric)
        t=dict(metric=metric,operator=op,value=v,unit=unit,context=ctx);typed.append(t);out.append(dict(rule_id=r['id'],page=page,sha256=sha,url=r['url'],anchor=anchor,**t))
    r['thresholds']=typed
 assert {r['rule_id'] for r in out}==set(MEASURES)
 c.dump(c.OUT/'codebook_typed_measures.json',out)
