"""Town of Eatonville: council agendas and development-agreement items for the HostDime project (Municode meeting
documents, archived in data/history/florida/extra.json)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from lib.files import j
from lib.text import htmltext
from collectors.florida.common import ST, R, fc, collect
import datetime as dt, re
def download_extras():
    path=collector_data('florida','extra.json')
    if path.exists():return
    codes={'20260901':'5cc05f3d22c94e3a9921ec730be886ec','20250204':'0d52d3feca134c6ca4017df43f0e45c6','20241217':'2367c6dfeafa4031b4e7b824bbf613ad','20231219':'eee85cd3aa0f4023bb662a6405cdd735','20260707':'18ea706721f246eeb06a4e6f326d1ce9'}
    collect.dump(path,{k:ST.get('https://meetings.municode.com/adaHtmlDocument/index?cc=EATNVLLEFL&ip=True&me='+v,'html') for k,v in codes.items()})
def download(c,m):download_extras()
def rows():
    out=[]
    for k,ref in j(collector_data('florida','extra.json')).items():
        t=htmltext(ST.read(ref));q=re.search(r'\bHost\s*Dime\b',t,re.I)
        if not q:raise ValueError('Wrong meeting')
        label={'20260901':'Review of proposed HostDime amendment 3','20250204':'Consideration of HostDime amendment 2','20241217':'Workshop on HostDime amendment 2','20231219':'Consideration of HostDime amendment 1 and right-of-way reimbursement','20260707':'HostDime construction update and discussion of Resolution 2026-32'}[k]
        day=dt.datetime.strptime(k,'%Y%m%d').date().isoformat()
        out.append(fc('Town of Eatonville council agendas','eatonville-'+k,'Resolution 2026-32' if k=='20260707' else 'HostDime development agreement',label,'Eatonville','Council agenda / development agreement','On agenda',day,'scheduled meeting date',ref,'Town council '+day+'; HostDime agenda item',basis='Agenda; a scheduled approval item is not proof of a vote.'))
    return out
