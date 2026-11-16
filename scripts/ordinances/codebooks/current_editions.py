"""Check the current local code link, not only the edition returned by the COMPASS workbook."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, csv, json
from urllib.parse import urljoin
import fitz
import lib.discovery as c
PUL='https://www.pulaskicounty.org/documents/planning-zoning/ordinances/udo-september-2026.pdf'
GRE='https://www.greenecountyva.gov/DocumentCenter/View/290/Zoning-Ordinance-PDF-1192026'
FRA='https://franklincountyva.gov/DocumentCenter/View/4312'
TARGETS=[('51155','https://www.pulaskicounty.org/planning-zoning.html','Unified Development Ordinance',PUL),
('51079','https://www.greenecountyva.gov/184/Ordinances','Zoning Ordinance (PDF)',GRE),
('51067','https://franklincountyva.gov/342/Zoning-Ordinance','REP: Regional Enterprise Park District',FRA)]
def run():
 idx=c.read(c.INDEX,{});matches=c.read(c.R/'data/national/compass_followup_matches.json',[]);versions=[];rules=[]
 for gid,page,label,url in TARGETS:
    upstream=[r for r in matches if r['referred_geoids']==gid];assert upstream
    ref=idx[c.address(page)];links=c.read(c.CACHE/(ref['sha256']+'.links.json'),[]);assert url in {urljoin(page,l) for l,t in links if t.startswith(label)}
    info=idx[c.address(url)];b=(c.CACHE/(info['sha256']+'.bin')).read_bytes()
    assert c.digest(b)==info['sha256'];pdf=fitz.open(stream=b,filetype='pdf')
    versions.append(dict(geoid=gid,upstream=[{'url':r['url'],'sha256':r['sha256']} for r in upstream],current_index=page,current_index_sha256=ref['sha256'],current_code=url,current_sha256=info['sha256'],link_text=label))
    def add(id,name,topic,title,summary,n,anchor,loc,**extra):
        assert c.norm(anchor) in c.norm(pdf[n-1].get_text()),id
        rules.append(dict(id=id,state='VA',jurisdiction=name,level='county',geoid=gid,topic=topic,reader_title=title,summary=summary,authority=name,scope='data-center-specific',url=url,corroborating_url=page,locator=loc,source_page=n,evidence=anchor,status='adopted',**extra))
    if gid=='51155':
        # In an untagged PDF, extracting "P P P P" alone loses the column identities.
        words=pdf[57].get_text('words');hdr=next(w for w in words if w[4]=='PID');line=next(w for w in words if w[4]=='Center' and w[1]>hdr[1])
        headers=[w for w in words if abs(w[1]-hdr[1])<2];marks=[w for w in words if w[4]=='P' and abs(w[1]-line[1])<2]
        cols=[min(headers,key=lambda h:abs(h[0]-m[0]))[4] for m in marks];assert cols==['LI','I','PID','AO*'],cols
        assert 'permitted by-right' in pdf[48].get_text() and 'underlying zone districts' in ' '.join(pdf[32].get_text().split())
        add('va-pulaski-industry','Pulaski County','by right','Industrial districts allow data centers by right','A data center is a permitted use in the Light Industrial, Industrial and Planned Industrial districts. The table also marks the Airport Overlay; check the underlying zone and airport standards. Other permits can still be required.',58,'Data Center','September 2026 ordinance, Table 4.1, pp. 49 and 58; §4.17(B), p. 33',district='LI, I and PID; AO overlay')
    if gid=='51079':
        add('va-greene-hosted-computing','Greene County','definition','What Greene County calls a data center','The county definition covers large computer systems that store and process data for off-site users. It lists generators, batteries, cooling and fire suppression as typical support equipment. The definition alone does not establish allowed locations.',165,'storage and processing for off-site users','November 9, 2026 edition, definition of DATA CENTER, p. 165')
    if gid=='51067':
        assert '25-411. Permitted uses' in pdf[0].get_text()
        add('va-franklin-enterprise-park','Franklin County','permitted use','Data centers are allowed in the Regional Enterprise Park district','Franklin County lists data centers alongside call centers and offices in its Regional Enterprise Park district. This answers the land-use question for that district; it does not issue a permit for an individual building.',2,'Data center.','Regional Enterprise Park district, §25-411, pp. 1–2',district='Regional Enterprise Park (REP)')
 c.dump(c.R/'data/national/current_book_versions.json',versions);c.dump(c.R/'data/national/current_book_rules.json',rules);print(len(rules),'published-edition provisions; county index and exact passages checked')
if __name__=='__main__':run()
