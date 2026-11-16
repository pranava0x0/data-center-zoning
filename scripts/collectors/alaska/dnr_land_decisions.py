"""Alaska Department of Natural Resources (Division of Mining, Land and Water): state land lease and land-use permit
decisions, from the State of Alaska Online Public Notices and their attached decision documents."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.alaska.evidence_store import A, adder, pdf
BASE='https://aws.state.ak.us/OnlinePublicNotices/Notices/'
S={'stak.html.gz':BASE+'View.aspx?id=225835','duck.html.gz':BASE+'View.aspx?id=217467'}
for k,v in [('stakfinal','165095'),('stakpre','165096'),('stakentry','165098'),('duck','151373')]:S[k+'.pdf']=BASE+'Attachment.aspx?id='+v
def download():
 for n,u in S.items():A.fetch(n,u)
def rows(out):
 add=adder(out)
 ds='Alaska DNR project decisions';s=pdf('stakfinal.pdf');assert 'will be issued after this FFD goes into effect' in s;stak='STAK Energy commercial gas-powered data center';borough='North Slope Borough';info=dict(issuer='Alaska Department of Natural Resources',county=borough)
 for file,dt,kind,stat,role in [('stakpre.pdf','2025-11-21','State land lease application','Application submitted','Date applicant submitted application'),('stakpre.pdf','2026-05-12','Preliminary best interest finding','Preliminary decision','Director decision date'),('stakpre.pdf','2026-06-15','Public comments','Deadline','Preliminary decision comment deadline'),('stakfinal.pdf','2026-11-10','50-year negotiated lease offer','Final finding and decision','Final decision date; not a signed lease'),('stakentry.pdf',None,'Entry authorization attachment','Proposed entry authorization','Date of execution not shown; final decision says issuance will follow')]:
  add(file,ds,'ADL 422741',stak,borough,kind,stat,dt,role,'DNR ADL 422741, '+('entry form and final decision p. 3' if file=='stakentry.pdf' else 'decision p. 1'),**info)
 for dt,stat,role in [('2024-11-05','Application received','Date state received application'),('2024-11-15','Public notice','Notice publication'),('2024-11-29','Comment deadline','Comments deadline')]:
  add('duck.html.gz',ds,'LAS 35307','TA Infrastructure — Satellite Drilling Island bitcoin data center pilot',borough,'Land use permit application',stat,dt,role,'State public notice; attached application LAS 35307; original proposed term not an issued term',issuer=info['issuer'],county=borough)
