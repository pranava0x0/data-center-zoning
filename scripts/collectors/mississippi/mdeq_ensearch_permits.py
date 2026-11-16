"""Mississippi Department of Environmental Quality (MDEQ) enSearch facility permit registers for the data center sites
below (air, stormwater, pretreatment), read from the archived enSearch pages in cache/ms. Identity proofs for each
site are the cited announcements and MDEQ documents. Offline only: there is no live download in this collector."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from lib.paths import CACHE
from lib.epa_icis import digest, iso
D=CACHE/'ms'
MDA='https://mississippi.org/news/amazon-continues-mississippi-expansion-announcing-plans-to-invest-a-total-of-25-billion-across-the-magnolia-state/'
MZX='https://www.mdeq.ms.gov/wp-content/uploads/2026/04/Signed-Minutes-of-the-March-2026-Permit-Board-Meeting.pdf'
VICK='https://opcgis.deq.state.ms.us/enOnline/get_doc.aspx?dt=pdf&id=1853771'
EN='https://opcgis.deq.state.ms.us/ensearchonline/ai_info.aspx?ai='
# Numeric allowlists prevent assigning former owners' entire facility histories to new campuses.
SITES={
86219:('Amazon Data Services, Madison Mega Site','Madison','Canton',MDA,['1720-00098']),
86979:('Amazon Data Services, JAN200','Madison','Ridgeland',MDA,['1720-00099']),
87959:('Compass Datacenters JAN I','Lauderdale','Meridian',EN+'87959',['1460-00133']),
88836:('ADP Rankin Data Hub, Data Center','Rankin','Brandon',EN+'88836',['MSR109556']),
89490:('Amazon Data Services, MCEDA JAN 100, phases II and III','Madison','Canton',MDA,['MSR109638']),
54959:('Amazon Data Services, Project Atlas JAN 200 Phase II','Madison','Ridgeland',MDA,['MSR109935']),
90111:('Alston Construction, Project Delphi (Project Atlas)','Hinds','Clinton',MDA,['MSR109732']),
12592:('MZX Tech, Stanton Road power supply facility','DeSoto','Southaven',MZX,['0680-00119','MSR109658','MSP092491']),
90524:('MZX Tech, Project Tulane at 2400 Stateline Road West','DeSoto','Southaven','https://opc.deq.state.ms.us/get_doc.aspx?dt=pdf&id=1837563',['MSR109819']),
90292:('Eutaw Construction, JAN 220 (Project Atlas)','Warren','Vicksburg',VICK,['MSR109762'])}
PROOFS={n:v[3] for v in SITES.values() for n in v[-1]}
PROOFS.update(MSR109366='https://opcgis.deq.state.ms.us/ensearchonline/get_doc.aspx?dt=finalp&id=1747891',MSR109367='https://opcgis.deq.state.ms.us/ensearchonline/get_doc.aspx?dt=finalp&id=1784357')
def rows():
    for ai,(project,county,city,proof,nums) in SITES.items():
        path=D/f'ensearch-{ai}.txt';t=path.read_text()
        if not re.search(r'(?im)^'+str(ai)+r'\s+\|',t) or city.lower()+', ms' not in t.lower() or ' | '+county.lower()+' ' not in t.lower():raise ValueError('MS geographic check: '+str(ai))
        records={};active={};sections=re.split(r'^## ',t,flags=re.M)[1:]
        for sec in sections:
            title,*lines=sec.splitlines()
            for line in lines:
                cols=[s.strip() for s in line.split('|')]
                if title.startswith('Active ') and len(cols)>=3 and cols[1] in nums:
                    typ,num,dt=cols[:3];active[num,iso(dt)]=(typ,title)
                if title.startswith('Current Status') and len(cols)>=5 and cols[2] in nums:
                    medium,typ,num,dt,status=cols[:5];records[(num,iso(dt),status)]=(medium+' - '+typ,title)
        for (num,day),(typ,title) in active.items():
            if not any(n==num and d==day and s in ('Permit Issued','Coverage Issued','Coverage Terminated') for n,d,s in records):
                records[(num,day,'Listed under '+title)]=(typ,title)
        for (n,day,status),(kind,title) in sorted(records.items()):
            if n.startswith('MSR'):kind='Construction stormwater: '+kind
            if n.startswith('MSP'):kind='Wastewater pretreatment: '+kind
            if day>'2026-11-15':continue
            det={'county':county+' County','issuer':'Mississippi Department of Environmental Quality','ai':str(ai),'identity_source':proof,'source_locality':city,'register_section':title,'active_section_same_day':(n,day) in active,'scope':'Supporting power generation, not data-hall permit' if ai==12592 else 'Project or construction phase'}
            role='issue date' if status.startswith('Listed under') or status.endswith(' Issued') else 'status date'
            yield dict(id=f'ms-mdeq-{ai}-{n}-{day}-'+re.sub('[^a-z0-9]+','-',status.lower()).strip('-'),state='MS',dataset='Mississippi DEQ enSearch facility permits',jurisdiction=city,project=project,record_no=n,kind=kind,status=status,date=day,date_role=role,url=EN+str(ai),source_url=EN+str(ai),source_sha256=digest(path),locator=f'AI {ai}; {title}; permit {n}',details=det)
