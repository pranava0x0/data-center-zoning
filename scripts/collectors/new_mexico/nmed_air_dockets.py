"""New Mexico Environment Department air-quality public notices and permit dockets (Greater Kudu, Project Jupiter microgrids)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import io, re
from html import unescape
from pypdf import PdfReader
import lib.discovery as c, collectors.new_mexico.sources as n
def rows(a,emit):
    def norm(t):return ' '.join(t.casefold().split())
    idx,h=a.get(n.INDEX);s=idx.decode()
    def section(start):
        return unescape(re.sub(r'<[^>]+>',' ',s.split('<h2>'+start,1)[1].split('<h2>',1)[0]))
    def confirm(txt,anchors):
        for anchor in anchors:
            if norm(anchor) not in norm(txt):raise ValueError('Missing agency evidence: '+anchor)
    def pdfhead(url,num=1):
        b,h=a.get(url);pdf=PdfReader(io.BytesIO(b));return ' '.join(x.extract_text() or '' for x in pdf.pages[:num]),h
    t,pin=pdfhead(n.LETTER,2)
    confirm(t,['37303','March 18, 2024','administratively complete on April 11, 2024','Greater Kudu'])
    def docket(no,proj,place,county,status,day,role,url,pin,loc,**details):
        emit('New Mexico Environment Department air proceedings',no,place,county,proj,'Air quality permit review',status,day,role,url,pin,loc,**details)
    kw=('7026M6','Greater Kudu data center','Los Lunas','Valencia County')
    docket(*kw,'Application received','2024-03-18','Application received',n.LETTER,pin,'Page 1 · received date')
    docket(*kw,'Application complete','2024-04-11','Completeness decision',n.LETTER,pin,'Page 1 · Completeness Determination')
    t,k=pdfhead(n.KUDU);confirm(t,['within the Village of Los Lunas','preliminary intent','7026M6'])
    confirm(section('Greater Kudu'),['(Posted 4-15-24)'])
    docket(*kw,'Preliminary determination','2024-04-15','Notice posted',n.KUDU,k,'NMED legal notice; posting date in Valencia County docket',posting_source=n.INDEX)
    t,pin=pdfhead(n.JUP_LOC,2);confirm(t,['nearby data center','two applications submitted on November 17, 2025','in Doña Ana County','April 27, 2026'])
    for no,side in [('10732','East'),('10734','West')]:
        block=section('Acoma, LLC '+side)
        confirm(block,['Application Withdrawn 4/27/2026',no,'3/24/2026'])
        args=(no,'Project Jupiter: '+side.lower()+' microgrid','Doña Ana County','Doña Ana County')
        link=n.INDEX
        docket(*args,'Application submitted','2025-11-17','Application submitted',n.JUP_LOC,pin,'Transmittal, page 2 · earlier two Acoma microgrid applications',docket_source=link)
        docket(*args,'Hearing determination posted','2026-03-24','Notice posted',link,h,'Acoma '+side+' · determination to hold hearing (posted date)')
        docket(*args,'Application withdrawn','2026-04-27','Withdrawal date',link,h,'Acoma '+side+' Microgrid · withdrawal in section heading')
    b,ph=a.get(n.JUP);t=c.parse(b,'text/html',n.JUP)[1]
    args=('10883','Project Jupiter: YGI microgrid','Doña Ana County','Doña Ana County')
    for anchor,day,role,status in [('received 4/27/26','2026-04-27','Application received','Application received'),('Completion Letter 5.27.2026','2026-05-27','Letter date','Application completeness letter'),('DRAFT as of 7.29.26','2026-07-29','Draft date','Draft air permit')]:
        confirm(t,[anchor]);docket(*args,status,day,role,n.JUP,ph,'10883 · '+anchor,project_location_source=n.JUP_LOC)
