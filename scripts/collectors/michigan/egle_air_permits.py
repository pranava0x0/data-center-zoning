"""Michigan EGLE Air Quality Division: permits to install (PTI 112-16, 112-16A, 91-16), the legacy Active PTIs by
Company registry, and the SRN P0709 compliance inspection report. Issuer: Michigan Department of Environment, Great Lakes, and Energy."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt
from lib.text import slug
from collectors.michigan.evidence_store import fetch_keys
KEYS=('legacy','switch_report','ptiorig','ptinew','ptisecond')
def download(m):fetch_keys(m,KEYS)
def rows(m,txt,add):
    assert 'P0709' in txt('switch_report',1) and 'VP of Data Center Operations' in txt('switch_report',1)
    for k,n,day,pg in [('ptiorig','112-16','2016-11-28',None),('ptinew','112-16A','2023-05-31',148),('ptisecond','91-16','2016-10-07',210)]:
        if pg and (n not in txt('legacy',pg) or 'P0709' not in txt('legacy',pg)):raise ValueError('Legacy PTI registry mismatch')
        if 'P0709' not in txt(k,1) or dt.date.fromisoformat(day).strftime('%B %d, %Y').replace(' 0',' ') not in txt(k,1):raise ValueError('instrument date/identity')
        add(k,1,n,'pti-'+slug(n),'Michigan air permits to install','Kent County',n,'SUPERNAP / MI GRR data center','Air permit to install','Approved',day,'permit approval date','Cover page; permit '+n+'; SRN P0709',county='Kent County',facility_id='P0709',identity_source=m['switch_report']['url'],identity_page=1,legacy_register_page=pg)
    add('switch_report',1,'ACTIVITY REPORT: Scheduled Inspection','supernap-inspection-2020','Michigan EGLE air compliance inspections','Kent County','P070954698','SUPERNAP Grand Rapids','Air compliance inspection','Compliance','2020-08-04','inspection date','Page 1, dated activity and compliance status',county='Kent County')
