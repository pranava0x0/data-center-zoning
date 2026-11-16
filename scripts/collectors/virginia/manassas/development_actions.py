"""Replay City of Manassas published development actions; no permit IDs inferred."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, json, re
from datetime import datetime

import lib.discovery as c
R=c.R;C=R/'cache/history/manassas_city';IDX=C/'manifest.json';OUT=series_path('manassascity_va')
DS='City of Manassas development and construction updates'
URL={'2024':'https://cms9files.revize.com/manassasva/Community%20Development/development%20services/Manassas%20Projects%2011-1-24%20final.pdf','2025':'https://cms9files.revize.com/manassasva/Communications/2025%20Press%20Releases/NR%20003%20-%20Brickyard%20Data%20Center.pdf','2026':'https://d3n9y02raazwpg.cloudfront.net/manassascity/22252c2a-e676-11f0-bb28-005056a89546-c100f652-1dcb-4b3e-a5d5-e9ca6c63a770-1768947272.pdf'}
def build():
    idx=c.read(IDX,{});pages={}
    for k,u in URL.items():
        m=idx[k];b=(C/m['file']).read_bytes()
        if m['url']!=u or c.digest(b)!=m['sha256']:raise ValueError('Evidence snapshot differs: '+k)
        pages[k]={int(n):v for n,v in re.findall(r'^L(\d+): ?(.*)$',b.decode(),re.M)}
    def block(k,a,b):
        return ' '.join(pages[k][i] for i in range(a,b+1) if i in pages[k]).strip()
    out=[]
    def add(s,k,project,addr,kind,status,act,span,date_exp=None,month_exp=None,report=None,**detail):
        text=block(k,*span)
        if status not in text:raise ValueError('Missing status '+s)
        date=None;month=None
        if date_exp:
            date=datetime.strptime(re.search(date_exp,text).group(1),'%B %d, %Y').date().isoformat()
        if month_exp:
            month=datetime.strptime(re.search(month_exp,text).group(1),'%B %Y').strftime('%Y-%m')
        if report:
            assert report=='2025-10' and 'October 2024 - October 2025' in block(k,1312,1314);month=report
        out.append(dict(id='va-manassas-city-'+s,state='VA',jurisdiction='City of Manassas',record_no='',dataset=DS,project=project,kind=kind,status=status,date=date,month=month or (date or '')[:7],date_role=act,url=URL[k],source_url=URL[k],source_sha256=idx[k]['sha256'],locator=f"{detail.pop('section')}; public document-reader lines {span[0]}–{span[1]}",details=dict(local_issuer='City of Manassas, Virginia',address_as_reported=addr,geoid='51683',source_snapshot_kind='published document text excerpt',source_snapshot='cache/history/manassas_city/'+idx[k]['file'],report_context={'2024':'October 2023–October 2024 activity report','2025':'City press release issued 2025-05-06','2026':'October 2024–October 2025 activity report, filed with January 23, 2026 council packet'}[k],**detail)))
    p='Digital Realty Data Center (Brickyard)';a='9905 Godwin Drive'
    add('grading','2025',p,a,'Demolition and grading approval','were approved','City-reported approval month',(45,49),month_exp=r'approved in (July 2022)',section='City release NR 003, site history',scope='City confirms both activities were approved in July; neither the number nor individual permit dates are disclosed.')
    add('construction-march','2025',p,a,'Building permit issuance (reported collectively)','issuance of building permits','City-reported issuance month',(45,49),month_exp=r'building permits in\s+(March 2023)',section='City release NR 003, site history',scope='The City reports multiple building permits issued in March. No identities or number given; relationship to the separately reported May permit is unknown.')
    add('permit-may','2024',p,a,'Project permit issuance (type unspecified)','Permit issued','City-reported issuance date',(25,27),date_exp=r'Permit issued (May 31, 2023)',section='Project 12',scope='Project report does not identify permit class or number.')
    add('occupancy','2024',p,a,'Certificate of occupancy','Occupancy granted','City-reported occupancy date',(25,27),date_exp=r'Occupancy granted (May 16, 2024)',section='Project 12',corroboration_url=URL['2025'],scope='Subsequent city release independently identifies a certificate of occupancy in May 2024.')
    add('aws','2026','AWS Data Center','9720 Dean Drive','Project permit issuance (type unspecified)','Permit issued','City-reported issuance date',(1061,1070),date_exp=r'Permit issued (October 3, 2024)',section='Development update, AWS Data Center, packet printed p. 38',scope='Earlier report also mentions a foundation/footing permit but gives no issue date. It is not established that the dated permit is that instrument.')
    add('d2','2026','D2 Tech Park','9482 Technology Drive','Project permit issuance (type unspecified)','Permit issued','City-reported issuance date',(1074,1081),date_exp=r'Permit issued (September 9, 2024)',section='Development update, D2 Tech Park, packet printed p. 39',scope='Dated report describes two data centers. Earlier shell-permits notice used 9496 Technology Drive and has no issue dates; it is not joined to any specific permit.')
    add('airport-review','2026','Airport Data Center','10421 Wakeman Drive','Site plan review status','Site Plan under review','As reported through October 2025; filing/decision date not supplied',(1264,1269),report='2025-10',section='Development update, Airport Data Center, packet printed p. 59',scope='Site plan under review as of the report period, not an approval, permit, or filing date.')
    c.dump(OUT,out);print(len(out),'city history observations')
def classify(r,cutoff,perm,no,app,obs):
    if r['dataset']!=DS:return None
    if r['kind']=='Site plan review status':return no('Status observation only. No site-plan decision or permit identified.','application')
    if r['kind']=='Certificate of occupancy':return no('Occupancy granted; not an additional numbered building permit.','decision')
    return no('City confirms an approval/issuance without a permit number. Preserved as history; the number of distinct permits cannot be determined from this report.','permit_action')
if __name__=='__main__':build()
