"""Publish only pinned and reviewed ordinance provisions from the alternative-name screen. Offline."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import os
import fitz
import lib.discovery as c
D=c.R/'data/national'; WORK=c.R/'cache/alternate_published_rules'
# Legal name, level, geographic ID, edition/definition anchors. All page numbers are physical PDF pages.
BOOKS={
'3bbd3a4aa3d7e1703f8794cea783922c99cf45288df750da9a39eaacebbc5e7c':('randolph','Randolph County','county','37151',[(1,'Adopted and Published'),(22,'physical or virtual servers'),(476,'Amended Section 621 to add additional regulations for Data Processing Facility')]),
'3f59247374e90ef044c92dc50a299a0755f56cb0640055f72e51695de484be71':('brown','Brown County','county','46013',[(2,'remote storage, management, processing or distribution of electronic data'),(206,'CHAPTER 4.38 DATA CENTERS')]),
'd3fee7979108e94b3956ffe0e376d304dc8d43cde8c60671b168f3543f39f0f0':('saluda','Saluda','city','3758920',[(1,'AS AMENDED AND RESTATED'),(44,'Amended 12/9/24'),(87,'remote storage, processing, or distribution of large amounts of data')]),
'b2fef48a92eec7ff858e98e77c7690bfa23c93656a5b1d11d0235747b53193ff':('mancelona','Mancelona','village','2650620',[(1,'Amended Through: 12.27.2024'),(63,'C: COMMERCIAL DISTRICT'),(68,'LIGHT INDUSTRIAL & WAREHOUSING DISTRICT'),(180,'utilizing a mainframe computer'),(180,'does not include general business offices')]),
'6468ddc7d665cd55d2faf9e70aa5fe6ecc24c0093af90d425be688cb6af232b3':('pitt','Pitt County','county','37147',[(218,'located on one or more acres of land'),(218,'accessory or incidental to another primary use'),(262,'January 11, 2022')]),
'3fc877da0fc59223a6225ef3494d2e496d791c166f9e58edabf26370c8d10cba':('springdale','Springdale','town','4568425',[(1,'ZONING ORDINANCE'),(113,'April 6, 2026'),(113,'operation of computer hardware')])
}
# For each summary the first of the strings is the short published quotation. Other anchors are review-only.
CLAIMS={
'randolph':[
('district','use permission','Art. 600 §621, Data Processing Facility, PDF p. 207',[(207,'Zoning Districts: HI-CD')],'Randolph County places its defined server-based data processing facility use in HI-CD (Heavy Industrial Conditional District). This is conditional district zoning, not by-right industrial use.'),
('setback','setback','Art. 600 §621, Site Considerations, PDF p. 207',[(207,'All outdoor equipment'),(207,'at least 1,000 feet')],'Outdoor equipment must be at least 1,000 feet from existing residences and listed sensitive uses, including schools, daycares, churches, hospitals, camps, parks and community or recreation centers.'),
('water','cooling water','Art. 600 §621, Required Plans (g), PDF pp. 207–208',[(207,'closed-loop water or a liquid cooling system'),(208,'estimated daily water usage')],'A licensed professional engineer must certify the proposed closed-loop water or liquid cooling system will minimize water use. For liquid cooling, the certification must identify daily usage and the water source.'),
('power','backup generation','Art. 600 §621, Required Plans (i)–(j), PDF p. 208',[(208,'routine testing up to four hours a month'),(208,'prior to the final Certificate of Occupancy')],'The facility must connect to the existing grid before final occupancy certification. On-site generation is limited to grid emergencies and routine testing totaling at most four hours per month.')],
'brown':[
('permits','conditional use','Title 4 §4.3802, PDF p. 206',[(206,'requires a Conditional Use Permit'),(206,'Brown County Building Permit'),(206,'Heavy Industrial (H-I) District and Agricultural Preservation District')],'In county zoning jurisdiction, installation, construction and modifications beyond routine maintenance require both a conditional use permit and county building permit. The section names only Heavy Industrial (H-I) and Agricultural Preservation (AG-P) and references a petition.'),
('distance','setback','Title 4 §§4.3803(1), 4.3805(1), PDF pp. 206–207',[(206,'Separation from Sensitive Properties'),(206,'75 dBA'),(207,'written waiver')],'The default separation from listed sensitive properties is one mile measured property line to property line. A stamped design showing noise below 75 dBA at the nearest data-center property line may support a reduction, never below half a mile. A written waiver in this range entails a noise mitigation plan.'),
('utility','utility capacity','Title 4 §4.3804(1)(A)–(C), PDF p. 207',[(207,'Off-grid systems shall be exempt'),(207,'applicable supply lines and substation')],'Before a grid-connected facility can receive a permit, its operator must provide utility approval and verification of available capacity, adequately sized infrastructure and no interference or voltage fluctuations. The requirement exempts off-grid systems.')],
'saluda':[
('district','conditional use','Zoning Ordinance, C-3 use-specific requirements, (2)(B), PDF p. 43; definition p. 87',[(43,'with a Special Use Permit'),(43,'only be allowed in the C3 Commercial District')],'Facilities that house systems used to store, process or distribute data remotely are allowed only in Saluda’s C-3 Commercial district, with a special use permit.'),
('application','site plan','Zoning Ordinance, C-3 (2)(B)(i), PDF p. 43',[(43,'A study prepared by an acoustical engineer'),(43,'A site plan showing the proposed location')],'The application must include a project narrative, a site plan locating equipment, access and screening, and an acoustical engineer’s study of anticipated sound and mitigation.'),
('power','utility capacity','Zoning Ordinance, C-3 (2)(B)(ii)(c), PDF p. 43',[(43,'Off-grid systems shall be exempt'),(43,'approved by the electrical utility provider')],'Before installing a grid-connected system, the operator must supply evidence that the utility approved the installation. The requirement exempts off-grid systems.')],
'mancelona':[
('district','by right','Zoning Ordinance §§3.7.2, 3.8.2 and 14.6, PDF pp. 65, 69 and 180',[(65,'Data Processing Facilities'),(69,'Data Processing Facilities'),(180,'does not include general business offices')],'The village lists qualifying data processing facilities by right in Commercial (C) and Light Industrial & Warehousing (LIW). Its definition covers digital records managed using a mainframe and excludes general offices, computer sales and personal/business services.'),
('parking','parking','Zoning Ordinance §§3.7.2 and 3.8.2, MAXIMUM PARKING column, PDF pp. 65, 69',[(65,'MAXIMUM PARKING'),(69,'MAXIMUM PARKING')],'The use tables for Commercial and Light Industrial & Warehousing specify a parking maximum of four spaces per 1,000 square feet for a data processing facility.')],
'pitt':[
('separation','setback','Ordinance 14 §8(UUUU)(2)–(3), PDF p. 160; §15 definition, p. 218',[(160,'one-quarter mile (1,320 feet)'),(160,'fifty feet from the boundary'),(218,'one or more acres')],'For large-scale data processing facilities as defined, all equipment and structures must be at least 50 feet from the site-plan facility boundary and 1,320 feet from any church, school or residence. Maximum height is 35 feet, excluding transmission lines and utility poles.'),
('application','site plan','Ordinance 14 §8(UUUU)(4), PDF p. 160; §15 definition, p. 218',[(160,'A study prepared by an acoustical engineer'),(160,'the perimeter of the facility')],'The large-scale facility application requires a narrative, layout showing churches, schools or homes within a quarter-mile of the perimeter, an acoustic-engineering study and owner/operator signatures. The county may request other reasonably necessary documentation.')],
'springdale':[
('office','use classification','Zoning Ordinance, commercial use types, paragraph U (Office), PDF p. 113',[(113,'Also includes electronic data storage centers'),(113,'storage and/or routing of electronic data')],'Springdale classifies an electronic data storage center under Office. Its definition expressly covers the operation of computer hardware and equipment that processes, stores or routes electronic data. This row does not infer district permission for every office or every type of data center.')]
}
HOLD={'481de97':'Draft file sets a June adoption date, but official notice dates adoption July 21 and effectiveness August 28. Do not transfer draft standards without the final text.',
'ba77603':'Consolidated New Franklin document leaves adoption date, effective date and ordinance number blank; not published here.',
'a34e148':'Grundy County FINAL DRAFT has blank ordinance number and adoption fields.',
'6c5d599':'Traditional hosting is covered, but a separate 2026 hyperscale moratorium and subsequent drafts complicate scope; reconcile enacted versions before publishing.',
'd830f3e':'Contents page references both mining and data processing; no operative language established by the hit.',
'd1c1396':'Matrix label expressly includes data centers; final adoption and table edition not independently established in this pass.',
'7ad3ee8':'Telecommunications hotel terminology requires service/hosting distinction and operative district checks.',
'ac80277':'Isolated source/table term: do not generalize to contemporary hosting without definition.',
'b15059d':'Additional candidate: technical definition and later district amendments require their own full check.',
'4784145':'Additional candidate: check technology scope, later amendments and district columns before publication.',
'be5bc62':'Additional candidate: definition and district permission need a current-edition check.'}
def norm(s):return c.norm(s)
def run():
    scan=c.read(D/'alternative_code_terms.json',{});idx={};out=[];audit=[]
    for item in scan['documents']:
        sha=item['sha256'];st,geo,url=item['referrals'][0];prefix=sha[:7]
        if sha not in BOOKS:
            reason='Outside requested follow-up states.' if st in {'TX','VA','GA'} else HOLD.get(prefix,'Not promoted: broad office/computing terminology or unverified scope, edition or zoning columns; requires further review.')
            audit.append(dict(sha256=sha,state=st,url=url,disposition='not promoted',reason=reason));continue
        slug,jur,level,expected,proof=BOOKS[sha]
        if expected!=geo:raise ValueError('issuer changed '+jur)
        candidates=[q for q in (c.R/'cache/codebooks',c.R/'cache/compass_code_sources') if (q/'files'/(sha+'.pdf')).exists()]
        original=candidates[0]/'files'/(sha+'.pdf');raw=original.read_bytes()
        if c.digest(raw)!=sha:raise ValueError('source hash failed: '+jur)
        recs=[c.read(q/'checks'/(c.digest(url.encode())+'.json'),{}) for q in candidates];record=next(r for r in recs if r.get('sha256')==sha)
        with fitz.open(original) as doc:
            pages=[p.get_text() for p in doc]
            def check(checks):
                for n,v in checks:
                    if norm(v) not in norm(pages[n-1]):raise ValueError(f'{jur}, p. {n}: {v}')
            check(proof)
            def fields(n,term):
                p=doc[n-1];rr=p.search_for(term)
                if len(rr)!=1:raise ValueError(f'Ambiguous original row {jur} p. {n}')
                return [(round(w[0]),w[4]) for w in p.get_text('words') if abs(w[1]-rr[0].y0)<1.5]
            if slug=='mancelona':
                for n in (65,69):
                    f=fields(n,'Data Processing Facilities')
                    assert ' '.join(w for x,w in f if 290<x<350)=='By Right'
                    assert ' '.join(w for x,w in f if x>420)=='4 / 1,000 square feet'
            if slug=='pitt':
                f=fields(53,'Data Processing Facility');assert [(x,w) for x,w in f if x>320]==[(335,'CD'),(615,'CD'),(655,'CD'),(698,'D'),(738,'D')]
                check([(160,'Must be approved as a Conditional Zoning District')])
            for suffix,topic,loc,anchors,summary in CLAIMS[slug]:
                check(anchors);out.append(dict(id='alt-'+slug+'-'+suffix,state=st,jurisdiction=jur,level=level,geoid=geo,topic=topic,scope='data center specific',summary=summary,status='adopted',locator=loc,url=url,authority=(jur if level=='county' else level.capitalize()+' of '+jur),evidence=anchors[0][1],effective_date=None))
        c.CACHE.mkdir(parents=True,exist_ok=True);dst=c.CACHE/(sha+'.bin')
        if not dst.exists():
            try:os.link(original,dst)
            except OSError:dst.write_bytes(raw)
        if c.digest(dst.read_bytes())!=sha:raise ValueError('SourceStore raw hash')
        tx=c.CACHE/(sha+'.txt')
        if not tx.exists():tx.write_text('\n'.join(f'[Page {i}]\n'+p for i,p in enumerate(pages,1)))
        txt=tx.read_text()
        if any(norm(x['evidence']) not in norm(txt) for x in out if x['url']==url):raise ValueError('Staged evidence missing: '+url)
        lk=c.CACHE/(sha+'.links.json')
        if not lk.exists():c.dump(lk,[])
        key=c.address(url);idx[key]=dict(url=key,resolved=record.get('resolved') or url,sha256=sha,text_sha256=c.digest(tx.read_bytes()),bytes=len(raw),fetched_at=record['checked'],adapter='pdf')
        audit.append(dict(sha256=sha,state=st,url=url,disposition='published selected provisions',accepted=len(CLAIMS[slug]),definition_and_edition_pages=sorted({n for n,_ in proof})))
    if len(idx)!=len(BOOKS) or len({r['id'] for r in out})!=len(out):raise ValueError('Incomplete or duplicate release')
    c.dump(WORK/'reviewed_index.json',idx);c.dump(D/'alternate_published_rules.json',out);c.dump(D/'alternate_published_review.json',dict(snapshot='2026-11-15',source_scan_sha256=c.digest((D/'alternative_code_terms.json').read_bytes()),input_documents=len(audit),accepted_documents=len(idx),provisions=len(out),dispositions=audit))
    print(len(audit),'source documents;',len(idx),'accepted;',len(out),'provisions')
if __name__=='__main__':run()
