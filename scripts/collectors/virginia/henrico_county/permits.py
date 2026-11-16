"""Link monthly reports from Henrico's public catalog to explicit permit records, offline by default."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import argparse, csv, collections, io, re, datetime
from urllib.parse import urlsplit
import openpyxl
import lib.discovery as c
from lib.url_archive import Archive
BASE='https://henrico.gov/public-data/categories/plans-development/';REG='Henrico County monthly issued permits';DAY='2026-11-15'
DC=re.compile(r'\b(?:data[ -]?cent(?:er|re)s?|server farms?)\b',re.I)
def run(fetch):
 a=Archive('henrico',fetch,owner='virginia/henrico_county/permits');seen={};files=[];holds=[];sources={}
 for cat in (BASE,'https://henrico.gov/public-data/tags/permits/'):
    b,h=a.get(cat)
    for u,t in c.parse(b,'text/html',cat)[2]:
        if re.match(r'^(?:building|trade) permits?\s*[-–—]',t,re.I) and urlsplit(u).netloc=='henrico.gov' and '/public-data/' in u:sources[u]=t
 for page,title in sorted(sources.items()):
    b,h=a.get(page);urls=sorted({u for u,t in c.parse(b,'text/html',page)[2] if re.search(r'\.xlsx?$',u,re.I) and urlsplit(u).netloc=='henrico.gov'})
    if len(urls)!=1:files.append(dict(page=page,notice='Expected one spreadsheet; inspect original'));continue
    u=urls[0];b,h=a.get(u)
    if b[:2]!=b'PK':files.append(dict(page=page,url=u,sha256=h,notice='Legacy format; not searched'));continue
    w=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True);count=0;matched=0
    for tab in w:
        rs=iter(tab.values);cols=[str(x or '').strip() for x in next(rs,())]
        if 'Permit Number' not in cols:continue
        for idx,values in enumerate(rs,2):
            d=dict(zip(cols,values));num=str(d.get('Permit Number') or '').strip()
            if not num:continue
            count+=1;fields=['Permit Name','Work Description','Primary Work Scope','Use Designation','Use Type'];txt=' '.join(str(d.get(k) or '') for k in fields);m=DC.search(txt)
            if not m:continue
            dt=d.get('Permit Issue Date') or d.get('Issue Date')
            if not isinstance(dt,(datetime.date,datetime.datetime)) or dt.strftime('%Y-%m-%d')>DAY:
                holds.append(dict(number=num,page=page,reason='No verified issue date before cutoff'));continue
            if re.search(r'\b(?:next to|adjacent to|outside of|near|not a) (?:the |existing )?data[ -]?cent',txt,re.I):holds.append(dict(number=num,page=page,reason='Possibly separate structure'));continue
            status=str(d.get('Permit Status') or 'Issued');name=d.get('Permit Name') or 'Data center — '+num
            kind=d.get('Permit Type') or 'Commercial building permit';day=dt.strftime('%Y-%m-%d')
            row=dict(id='va-henrico-'+num.lower(),state='VA',dataset=REG,record_no=num,jurisdiction='Henrico County',county='Henrico County',project=name,kind=kind,status=status,date=day,date_role='County permit issue date',url=page,source_url=u,source_sha256=h,locator=f'{tab.title} row {idx} · {num}',details=dict(issuer='Henrico County Department of Building Construction and Inspections',original_work_type=d.get('Work Type'),work_description=d.get('Work Description') or d.get('Primary Work Scope'),direct_evidence=m.group(),sheet=tab.title,row=idx))
            if num in seen and (seen[num]['date'],seen[num]['kind'])!=(day,kind):raise ValueError('Conflicting county permit '+num)
            seen[num]=row;matched+=1
    files.append(dict(title=title,page=page,url=u,sha256=h,rows=count,explicit_matches=matched))
 c.dump(series_path('henrico_va'),sorted(seen.values(),key=lambda r:r['id']));c.dump(collector_data('virginia/henrico_county/permits','audit.json'),dict(catalog=BASE,reports=files,held=holds,unique_permits=len(seen),limits='Only individually linked monthly workbooks with project-identifying fields. Trade sheets often lack work descriptions. A mailing address or a technology company name alone cannot identify a permit.'))
 print(len(files),'monthly reports;',sum(r.get('rows',0) for r in files),'rows;',len(seen),'unique documented permits',flush=True)
def classify(r,cutoff,perm,no,app,obs):
 from datetime import date
 s=r['status'].strip().lower()
 return perm('VA:Henrico:'+r['record_no'],'historical' if s in ('closed','expired','cancelled','finaled','complete','completed') else 'unconfirmed','The county lists an issuance date and status of '+r['status']+'. Issuance alone does not establish present validity.',date.fromisoformat(r['date']))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
