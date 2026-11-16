"""Louisiana DEQ quarterly air permit actions (xlsx) and LPDES water permit actions (PDF), every row screened for explicit data
center text; water rows join to EPA ICIS-NPDES by permit number. Files are pulled by deq_quarterly_reports.py."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re, datetime
from collections import Counter
from lib.epa_icis import iso
from lib.records import reconcile
from collectors.louisiana.deq_quarterly_reports import files, INDEX
from collectors.louisiana.row_builder import row, EXPLICIT
import openpyxl, fitz
def rows(ep):
    """Records reconciled with the EPA ICIS-NPDES rows, plus the screening counts the validation file reports."""
    lookup={r['record_no']:r for r in ep};rows=[];stats=Counter()
    for k,u,p in sorted(set(files()),key=lambda v:(v[0],v[1])):
        stats[k+'_files']+=1
        if k=='air':
            w=openpyxl.load_workbook(p,data_only=True,read_only=True)
            for sh in w.worksheets:
                for i,z in enumerate(sh.values,1):
                    if len(z)<7 or not isinstance(z[0],int):continue
                    stats['air_rows_scanned']+=1
                    if not EXPLICIT.search(' '.join(str(v) for v in z)):continue
                    ai,name,county,pk,num,act,dt=z[:7]
                    if not isinstance(dt,datetime.datetime):raise ValueError(z)
                    city=next((e['jurisdiction'] for e in ep if name.upper()==e['project'].upper()),None)
                    rows.append(row('Louisiana DEQ quarterly air actions',f'air-{ai}-{act}',city,county+' Parish',str(num),name,'Air permit: '+pk,'Issue Final Decision',dt.date().isoformat(),'final decision date',u,f'{sh.title} row {i}; AI {ai} / {act}',p,activity_no=act,ai=str(ai),identity_source=INDEX[k],reported_action=pk))
        else:
            for n,page in enumerate(fitz.open(p),1):
                for line in page.get_text(sort=True).splitlines():
                    if not re.match(r'\s*\d+\s+LA\w+',line):continue
                    stats['water_rows_scanned']+=1
                    m=re.match(r'\s*(\d+)\s+(LA\w+)\s+',line);num=m[2]
                    if num not in lookup:
                        if EXPLICIT.search(line):raise ValueError('New explicit quarterly row needs location crosswalk: '+line)
                        continue
                    bits=re.match(r'^(.*?)\s{2,}(.+?)\s+(\w{3}\d{8})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s*$',line[m.end():])
                    if not bits:raise ValueError('Quarterly layout changed '+line)
                    name,action,act,issued,eff,end=bits.groups();e=lookup[num]
                    kind='Construction stormwater NPDES coverage' if num.startswith('LAR10') else 'NPDES discharge coverage'
                    rows.append(row('Louisiana DEQ quarterly LPDES actions',f'water-{m[1]}-{act}-{num}',e['jurisdiction'],e['details']['county'],num,name,kind,action,iso(issued),'issue date',u,f'PDF p. {n}, AI {m[1]}, {num}, {act}',p,ai=m[1],activity_no=act,effective_date=iso(eff),expiration_date=iso(end),identity_source=e['details']['identity_source'],location_source=e['url']))
    rows=reconcile(rows,ep)
    return rows,stats
