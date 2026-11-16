"""Shreveport-Caddo Metropolitan Planning Commission hearing decision and Shreveport City Council appeal vote on case 25-127-C."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import fitz
from collectors.louisiana.deq_quarterly_reports import CACHE
from collectors.louisiana.row_builder import row
MPC='https://www.shreveportcaddompc.com/home/showpublisheddocument/17998/639004623366070000'
NEWS='https://louisianapublicnotice.com/notices/576942'
def rows():
    rows=[]
    for ident,ds,city,county,no,site,kind,status,dt,role,u,loc,fn,markers,agency in [
        ('shreveport-mpc','Shreveport land use decisions','Shreveport','Caddo Parish','25-127-C','Bohler Engineering / Franks Investment Company, 7300 block Greenwood Road','Special use permit and site plan','DENIED','2025-12-03','commission hearing decision date',MPC,'MPC annotated hearing agenda, item 12; case 25-127-C','la-shreveport-25-127.txt',['25-127-C','BOHLER ENGINEERING','DENIED'],'Shreveport-Caddo Metropolitan Planning Commission'),
        ('shreveport-appeal','Shreveport land use decisions','Shreveport','Caddo Parish','25-127-C','Bohler Engineering / Franks Investment Company, 7300 block Greenwood Road','Special use permit and site plan appeal','Motion approved','2025-12-18','council vote date',NEWS,'City Council proceedings, December 18, appeal case 25-127-C (municipal minutes republished in legal notices); 7 ayes, 0 nays','shreveport-published-minutes.html',['December 18, 2025','Case No. 25-127-C','Motion by Councilwoman Bowman'],'Shreveport City Council')]:
        p=CACHE/fn
        t=' '.join(pg.get_text() for pg in fitz.open(p)) if p.suffix=='.pdf' else p.read_text()
        if not all(' '.join(m.lower().split()) in ' '.join(t.lower().split()) for m in markers):raise ValueError('Case evidence changed: '+ident)
        rows.append(row(ds,ident,city,county,no,site,kind,status,dt,role,u,loc,p,issuer=agency))
    return rows
