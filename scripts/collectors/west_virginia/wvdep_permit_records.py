"""West Virginia DEP application, public hearing and enforcement record replay.
Single issuer, so not split: West Virginia Department of Environmental Protection (Monarch Cloud Campus notices, enforcement
order, NSR air application register)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R, D
import lib.files, lib.net, lib.terms, lib.text, lib.geo
import argparse, re, json
from collections import Counter
from datetime import datetime
import fitz
from lib.text import plain
from lib.archive import NamedArchive as Archive
A=Archive('WV');BASE='https://dep.wv.gov';p='Public-Comment-Period-and-Public-Participation-Opportunities-for-Monarch-Cloud-Campus';S={'monarch.html.gz':BASE+'/news/Pages/'+p+'.aspx','enforcement.html.gz':BASE+'/news/Pages/WVDEP-Issues-Enforcement-Order-Following-Stormwater-Violations-at-Monarch-Cloud-Campus-Construction-Site.aspx','eval.pdf':BASE+'/news/SiteAssets/Pages/'+p+'/Preliminary%20Determination%20R14-0042.pdf','nsr.html.gz':BASE+'/daq/permitting/Pages/NSR-Permit-Applications.aspx','cumulus.pdf':'https://apps.dep.wv.gov/Documents/DAQ/NSRPermits/079-00208/Draft/079-00208APP.pdf'}
def refresh():
 A.geom()
 for n,u in S.items():A.fetch(n,u)
 A.seal()
def build():
 A.verify();out=[];project='Monarch Cloud Campus — Point Pleasant';j='Mason County'
 def add(n,no,title,county,kind,status,date,role,loc):
  out.append(dict(id='wv-dep-'+str(len(out)),state='WV',dataset='West Virginia DEP project files',jurisdiction=county,record_no=no,project=title,kind=kind,status=status,date=date,date_role=role,url=S[n],source_url=S[n],locator=loc,details={'issuer':'West Virginia Department of Environmental Protection','county':county,'archive':'cache/history/wv/'+n,'archive_sha256':A.files[n]['sha256']}))
 s=plain(A.read('monarch.html.gz').decode());e=plain(A.read('enforcement.html.gz').decode());reg=plain(A.read('nsr.html.gz').decode());assert all(t in s for t in ['R14-0042','SWP-26-0002','SWP-26-0003','October 26, 2026','November 13, 2026']);assert 'issued a unilateral enforcement order' in e and '7/14/2026' in e
 a='R14-0042';n='eval.pdf';doc=fitz.open(A.c/n);ss=' '.join(doc[2].get_text().split()).replace('\u200b','');assert 'April 20, 2026' in ss and 'May 26, 2026' in ss
 for role,raw in [('Application received','April 20, 2026'),('Revised information received','May 26, 2026'),('Applicant advertisement date','April 24, 2026')]:
  add(n,a,project,j,'Major source construction application',role,datetime.strptime(raw,'%B %d, %Y').date().isoformat(),role,'Preliminary determination p. 3, background information; facility 053-00136')
 n='monarch.html.gz'
 for k in ['SWP-26-0002','SWP-26-0003',a]:
  add(n,k,project,j,'State waters application' if k!=a else 'Power plant air application','Public comment notice','2026-09-29','Agency publication date','Agency notice of pending decisions on air and two separate State Waters applications')
  if k!=a:add(n,k,project,j,'State waters public meeting','Scheduled','2026-10-26','Noticed meeting date','State Waters workshop and public meeting section; attendance not inferred')
 for dt,k,stat in [('2026-10-20','Air permit public meeting','Scheduled'),('2026-10-29','Air permit virtual hearing','Scheduled'),('2026-11-13','Air permit comment period','Deadline')]:add(n,a,project,j,k,stat,dt,'Noticed participation date','Air Quality Permit section; application not issued')
 add('enforcement.html.gz','Monarch stormwater order (number not stated)',project,j,'Construction stormwater enforcement','Unilateral enforcement order issued','2026-07-14','Publication date announcing order; signature date not disclosed','Press release: stop land disturbance in separate drainage area and repair controls; not a revocation')
 n='cumulus.pdf';assert 'data center in Buffalo, Putnam County' in ' '.join(fitz.open(A.c/n)[3].get_text().split());assert re.search(r'R13-3782.{0,190}Application: Received 07/22/2026',reg)
 add(n,'R13-3782','Cumulus Group LLC — Buffalo data center','Putnam County','Air construction application','Application received','2026-07-22','Agency register received date','State NSR applications, facility 079-00208; application PDF p. 4 identifies sector');out[-1]['source_url']=S['nsr.html.gz']
 lib.files.dump(series_path('wv'),out);lib.files.dump(collector_data('west_virginia','validation.json'),dict(events=len(out),datasets=dict(Counter(x['dataset'] for x in out)),geography=A.rank()));print(len(out),'WV events')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');args=p.parse_args()
 if args.refresh:refresh()
 build()
