"""Verify local provisions against the original municipal or county PDF referred by COMPASS."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json
import fitz
import lib.discovery as c
D=c.R/'data/national'
TOWNS={'4845384':('TX','McAllen','city'),'1352192':('GA','Monroe','city'),'13137':('GA','Habersham County','county')}
def run():
 rows=[];index=c.read(c.INDEX,{})
 for src in c.read(D/'compass_followup_matches.json',[]):
    g=src['referred_geoids']
    if g not in TOWNS:continue
    st,name,level=TOWNS[g];check=c.R/src['archive'];sha=src['sha256'];url=src['url']
    b=(check.parents[1]/'files'/(sha+'.pdf')).read_bytes();assert c.digest(b)==sha
    pdf=fitz.open(stream=b,filetype='pdf');pages=[' '.join(p.get_text().split()) for p in pdf]
    def add(slug,topic,title,summary,page,anchor,loc,**extra):
        assert c.norm(anchor) in c.norm(pages[page-1]),slug
        rows.append(dict(id=st.lower()+'-'+slug,state=st,jurisdiction=name,geoid=g,level=level,topic=topic,reader_title=title,summary=summary,status='adopted',authority=name,scope='data-center-specific',url=url,evidence=anchor,source_page=page,locator=loc,**extra))
    if g=='4845384':
        w=pdf[43].get_text('words');tag=next(t for t in w if t[4]=='Data');mark=[t for t in w if t[4] in ('C','P') and abs(t[1]-tag[1])<2];assert len(mark)==1 and mark[0][4]=='C'
        hdr=next(t for t in w if t[4]=='I-2');assert abs((hdr[0]+hdr[2]-mark[0][0]-mark[0][2])/2)<6
        assert 'C = Conditional Use' in pages[43]
        add('mcallen-industrial-approval','conditional use','McAllen requires conditional use approval in I-2','The city lists data centers as a conditional use in its I-2 industrial district. No other district is marked for data centers in this table.',44,'Infrastructure Data Center C','February 9, 2026 code, Article 3.1 use table, printed p. 40',district='I-2')
        add('mcallen-parking','parking','One parking space per 1,000 square feet','McAllen sets the parking minimum in the same table that lists its data center zoning requirements.',44,'Data Center C 1/1,000 SF','Article 3.1 use table, printed p. 40, minimum parking ratios')
    if g=='1352192':
        add('monroe-home-distance','setback','Keep data center buildings 500 feet from homes','The 500-foot distance is measured to a residential structure. The city also requires a 100-foot buffer around the site, with dense vegetation and measures that reduce noise.',66,'to any residential structure','Zoning ordinance, use-table note (34), p. 66')
        add('monroe-outreach','conditional use','Hold two public meetings before applying','The applicant must hold at least two meetings at least six months before filing for conditional use approval and notify all property owners within 500 feet. The application must include proof of the meetings and a list of owners contacted.',66,'no less than 6 months prior','Zoning ordinance, use-table note (34), p. 66')
    if g=='13137':
        add('habersham-special-use','conditional use','County approval is required even for an in-house data center','A data center within the county’s zoning jurisdiction needs a special use permit from the Board of Commissioners. This includes a center inside another business that serves only the owner, occupies at most 10% of its footprint and has no separate building.',96,'via issuance of a special use permit','§4.2.10.3(A), p. 96')
        add('habersham-lot','site design','Five acres for a data center; 20 for its power plant','The county sets separate minimum lot sizes for the data center and for a data center power plant.',96,'No data center shall be erected on any lot less than five acres','§4.2.10.3(B)(1), p. 96')
        add('habersham-residences','setback','Keep buildings 1,000 feet from residences and residential lots','The county applies this distance to data centers and their power plants. Other property lines and public road rights-of-way require at least 60 feet or 1.25 times the structure’s height, whichever is greater.',96,'from all residentially zoned lots and existing residences','§4.2.10.3(B)(3), p. 96')
        add('habersham-sound','noise','An independent engineer must measure baseline sound','Before construction or operation, the owner must commission readings at eight locations around the site and give the planning department the report within 30 days of completion.',97,'performed by a third-party acoustic engineer','§4.2.10.3(B)(5)(a), pp. 96–97')
    t=c.CACHE/(sha+'.txt');key=c.address(url)
    if key in index and index[key]['sha256']!=sha:raise ValueError('Different archived edition: '+url)
    if not t.exists():t.write_text('\n'.join(f'[Page {i}]\n{p}' for i,p in enumerate(pages,1)))
    (c.CACHE/(sha+'.bin')).write_bytes(b)
    links=c.CACHE/(sha+'.links.json')
    if not links.exists():c.dump(links,[])
    index[key]=dict(url=url,resolved=url,fetched_at=c.read(check,{})['checked'],adapter='pdf',sha256=sha,text_sha256=c.digest(t.read_bytes()),bytes=len(b))
 assert len(rows)==8
 c.dump(c.INDEX,index)
 from ordinances.codebooks.measures import add as add_measures
 add_measures(rows);c.dump(D/'second_codebook_rules.json',rows);print(len(rows),'reviewed land-use provisions')
if __name__=='__main__':run()
