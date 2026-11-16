"""Verify pinned New York public decision extracts and emit source-linked project actions."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import json, fitz
from collectors.new_york.source_store import D,ROOT,mk,iso
NORTH='https://cms3.revize.com/revize/niagarafallsny/Documents/Government/'
SOM='https://www.somersetny.gov/planning-board/minutes/planning-board-meeting-minutes-10'
OPS={
 'nf-seqra':('2023-07-26','2023-35','Environmental review determination','positive declaration','July 26 vote sheet item 27, 3–2; follow-up finding in April 9, 2025 Planning Board packet','niagara-20230726-review.txt',NORTH+'City%20Council/Agenda/2023.7.26.MTG_.VOTE_.pdf',['Seqra determination of significance','Digital Asset','5380 Frontier']),
 'nf-recommend':('2025-06-25','SBL 160.14-1-1.2','Zoning overlay recommendation','Motion to approve the recommendation','June 25 official Planning Board minutes, item 1. Recommendation only; not final rezoning.','niagara-20250625-review.txt',NORTH+'Department/Planning%20And%20Environmental/Planning%20Board/2025/PB%20Packet%2020250728_Redacted.pdf',['5380 Frontier Avenue','Motion to approve the recommendation']),
 'nf-eis':('2025-07-23','2025-07-23 agenda item 20','Environmental impact statement decision','THE MOTION WAS ADOPTED','July 23 council vote sheet, item 20; five yeas. Final EIS, not final zoning.','niagara-20250723-review.txt',NORTH+'City%20Council/2025/0723/0%20-%20VOTE%20SHEET%20for%20REGULAR%20MTG%207.23.25.pdf',['ISSUING A FINAL','5380 FRONTIER','THE MOTION WAS ADOPTED']),
}
def records():
    items=[]
    def push(slug,d,n,kind,status,locator,fn,u,terms,ds,place,co,project,issuer,role):
        p=D/fn
        if p.suffix=='.pdf':
            with fitz.open(p) as doc:t=doc[0].get_text()
        else:t=p.read_text()
        t=' '.join(t.lower().split())
        if not all(z.lower() in t for z in terms):raise ValueError('Case evidence changed: '+slug)
        items.append(mk(ds,slug,kind,status,n,d,role,u,locator,project,place,co,p,issuer=issuer,archive_file=str(p.relative_to(ROOT)),verified_markers=terms))
    for slug,values in OPS.items():push(slug,*values,'Niagara Falls project decisions','Niagara Falls','Niagara County','North East Data LLC / Blockfusion, 5380 Frontier Avenue (data center and digital asset mining facility)','Niagara Falls Planning Board' if 'recommend' in slug else 'Niagara Falls City Council','local board vote date')
    for slug,k,s,terms in [('coastal','Coastal consistency determination','ADOPTED',['COASTAL CONSISTENCY RESOLUTION','ADOPTED']),('seqr','Environmental review determination','Negative Declaration',['SEQR NEGATIVE DECLARATION RESOLUTION','Negative Declaration']),('sup','Conditional special use permit and site plan decision','ADOPTED',['SPECIAL USE and SITE PLAN RESOLUTION','hereby grants a Special Use Permit'])]:
        push('somerset-'+slug,'2025-09-04','SBL 8.00-1-1.11 / CB3 / '+slug,k,s,'September 4 minutes, '+k+'; CB3 battery UPS accessory to AI campus; grant subject to terms, not a building permit.','somerset-20250904-review.txt',SOM,terms,'Somerset Planning Board project decisions','Somerset','Niagara County','Wulf Compute / Lake Mariner Data, CB3 battery UPS, 7725 Lake Road','Town of Somerset Planning Board','planning board vote date')
    for n,d in [(1,'10/01/2020'),(2,'06/23/2025')]:
        fn='339240049300001_r0_2.pdf';push('orangetown-mod-'+str(n),iso(d),'3-3924-00493/00001','State facility air permit modification','Modification effective','Cover p. 1; Mod '+str(n)+' is a revision of the existing permit.',fn,'https://extapps.dec.ny.gov/data/dar/afs/permits/'+fn,['Mod '+str(n)+' Effective Date: '+d],'New York DEC air permit modifications','Orangeburg','Rockland County','Orangetown Data Center','New York State Department of Environmental Conservation','modification effective date')
    return items
if __name__=='__main__':(collector_data('new_york','cases.json')).write_text(json.dumps(records(),indent=2)+'\n')
