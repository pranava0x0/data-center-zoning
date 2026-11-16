"""Douglas County (Georgia) Planning and Zoning Commission agendas naming data center requests, from the county's
published agenda PDFs listed in the config's local_docs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt
import lib.net as netfetch
import lib.discovery as collect
from collectors.georgia.evidence_store import M, get, DC, pdfpages, row, slug
def fetch(c,m):
    for k,u in c['local_docs'].items():
        if k not in m.setdefault('local_docs',{}) or netfetch.REFETCH:m['local_docs'][k]=get(u,'pdf');collect.dump(M,m)
def rows(m):
    out=[]
    agendas=[('20241001','Z2024-49',1,'Stream Data Centers','Special use permit request'),('20241001','Z2024-50/ S20214-51',1,'Grind Capitol, LLC','Rezoning and special use permit request'),('20241001','M2024-07/ Z2024-55/ S2024-56',2,'TC Atlanta Development, Inc.','Future land use amendment, rezoning and special use request'),('20250204','M2024-07/ Z2024-55/ S2024-56',1,'TC Atlanta Development, Inc.','Future land use amendment, rezoning and special use request'),('20260203','S2025-13',1,'Big Power Developments 5, LLC','Special use permit request'),('20240206','M2024-02/ Z2024-07/ S2024-08',1,'Anamaria Meanes','Future land use amendment, rezoning and special use request')]
    for d,n,pg,name,k in agendas:
        ref=m['local_docs']['douglas'+d];t=pdfpages(ref['sha256'])[pg-1];chunk=t.split(n,1)[1][:720]
        if not DC.search(chunk) or name not in chunk:raise ValueError('Agenda assertion '+n)
        day=dt.datetime.strptime(d,'%Y%m%d').date().isoformat();out.append(row('Douglas County Planning and Zoning agendas','douglas-'+slug(n)+'-'+d,'Douglas County',n,name,k,'Request on agenda',day,'scheduled meeting date',ref,'Agenda p. '+str(pg)+'; '+n,county='Douglas County',identity_evidence=DC.search(chunk).group()))
    return out
