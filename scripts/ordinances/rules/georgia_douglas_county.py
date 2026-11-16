"""Replay four county code provisions using a pinned county PDF and spatial table check."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import os, argparse, datetime
from urllib.request import Request,urlopen
import lib.discovery as c
D=c.R/'cache/douglas_ga';FILE=D/'ordinance.pdf';RULES=c.R/'data/national/douglas_ga_rules.json'
URL='https://www.douglascountyga.gov/DocumentCenter/View/14894/Douglas-County-Unified-Development-Code_Updates-through-August-2026'
PIN='c3712649ae6ccedefdace0c0e64701bc1f3c51a18aa98c26936e744f48fd345c'
CAP=40*1024*1024

def run(refresh=False):
    import fitz
    D.mkdir(parents=True,exist_ok=True)
    if refresh:
        c.policy(URL)
        with urlopen(Request(URL,headers={'User-Agent':c.AGENT}),timeout=60) as resp:b=resp.read(CAP+1)
        if c.digest(b)!=PIN:raise ValueError('Publication changed: review its districts, conditions and pagination before replacing the pin')
        FILE.write_bytes(b)
    b=FILE.read_bytes()
    if c.digest(b)!=PIN:raise ValueError('County code digest mismatch')
    with fitz.open(stream=b,filetype='pdf') as doc:
        pages={n:doc[n-1].get_text() for n in (34,101,277)}
        words=doc[100].get_text('words')
        if len(doc)!=782 or not any(w[4]=='518210' and 460<w[1]<470 for w in words):raise ValueError('Table page/row changed')
        columns={w[4]:(w[0]+w[2])/2 for w in words if 244<w[1]<246}
        selected=[min(columns,key=lambda k:abs(columns[k]-(w[0]+w[2])/2)) for w in words if w[4]=='S' and 425<w[1]<435]
        if selected!=['OI','LI','LI-R','HI']:raise ValueError('Use table grid changed')
    common=dict(state='GA',jurisdiction='Douglas County',level='county',geoid='13097',authority='Douglas County Board of Commissioners',scope='data center specific',status='adopted',url=URL)
    def rule(slug,topic,summary,locator,evidence,**kwargs):
        return dict(common,id='ga-douglas-'+slug,topic=topic,summary=summary,locator=locator,evidence=evidence,**kwargs)
    emit=[
        rule('special-use','special_use_permit','In unincorporated Douglas County, the principal use covering computing infrastructure, data processing and web hosting (NAICS 518210) needs special use approval in OI, LI, LI-R and HI. The other district cells on this row are blank; the legend identifies a blank as not allowed. The row does not allow this use by right.', '§105(a), PDF p. 34; Table 2.2, NAICS 518210, printed p. 44 of 76 (PDF p. 101), including legend','Use Requires Special Use Approval',district='OI, LI, LI-R, HI'),
        rule('application-materials','site_plan','In unincorporated Douglas County, covered facilities must submit schedules for project buildout and utilities, plus a master site plan identifying required parcel divisions and combinations. These materials accompany any application for zoning action, special use, variance, land disturbance or building permits. The director may request further information under §1206.', '§352(a)–(b), PDF p. 277','all required subdivision and recombination of parcels'),
        rule('residential-adjacency','residential_setback','A covered facility in unincorporated Douglas County cannot occupy a parcel that shares a boundary with land either zoned for residential use or actually used for housing.', '§352(c)(1), PDF p. 277','shares a common property line'),
        rule('residential-buffer','buffer','In unincorporated Douglas County, covered facilities within 200 feet of residentially zoned or residentially used land need a 100-foot undisturbed buffer. Measure as specified from the nearest property line. The director may reduce the buffer if design and screening adequately integrate the building into the site. This discretion applies to the buffer, not the separate shared-boundary prohibition.', '§352(c)(2) and (2)(a), PDF p. 277','a reduction in the undisturbed buffer',thresholds=[dict(metric='undisturbed buffer',operator='required',value=100,unit='feet',context='Within 200 feet of residential land; director may approve a reduction.'),dict(metric='residential proximity',operator='within',value=200,unit='feet',context='Triggers 100-foot buffer; see nearest property line measurement in §352(c)(2).')])
    ]
    text='\n'.join(f'[Page {n}]\n{v}' for n,v in pages.items())
    assert 'unincorporated areas of douglas county' in c.norm(pages[34])
    assert all(c.norm(x['evidence']) in c.norm(text) for x in emit)
    dest=c.CACHE/(PIN+'.bin')
    if not dest.exists():os.link(FILE,dest)
    assert c.digest(dest.read_bytes())==PIN
    (c.CACHE/(PIN+'.txt')).write_text(text);c.dump(c.CACHE/(PIN+'.links.json'),[])
    date=c.read(D/'reviewed_index.json',{}).get(URL,{}).get('fetched_at') or c.now()
    c.dump(D/'reviewed_index.json',{URL:dict(url=URL,resolved=URL,fetched_at=date,sha256=PIN,text_sha256=c.digest(text.encode()),bytes=len(b),adapter='pdf_page_excerpt',indexed_pages=list(pages))})
    c.dump(D/'table_check.json',dict(source=URL,sha256=PIN,page=101,row='518210',special_use_columns=selected,reviewer='Codex Sol',method='Visually inspected PDF row and legend; verified four S glyphs by column coordinates against district labels. Blank cells not allowed.'))
    c.dump(RULES,emit);print(len(emit),'reviewed Douglas County rules')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--refresh',action='store_true');run(p.parse_args().refresh)
