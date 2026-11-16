"""Page through the Cook County assessor's own permit cards. The situs and applicant are different fields."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, re, html
from datetime import datetime
from urllib.parse import urljoin,urlsplit
from html.parser import HTMLParser
from lib.url_archive import Archive
import lib.discovery as c
FIRST='https://assessorpropertydetails.cookcountyil.gov/datalets/datalet.aspx?LMparent=896&UseSearch=no&jur=016&mode=permit_ck_cc&pin=08224030160000&taxyr=2025'
RES='https://files.illinoiscomptroller.gov/LocGovTIF/FY2023/01616532/23TIF01616532Busse_Elmurst_RPA_5.pdf'
class Card(HTMLParser):
 def __init__(self):
    super().__init__();self.key=None;self.texts=[];self.field=None;self.values={};self.arrows=[]
 def handle_starttag(self,tag,attrs):
    d=dict(attrs);cl=d.get('class','')
    if tag=='td' and cl in ('DataletSideHeading','DataletData'):self.field=cl;self.texts=[]
    if tag=='a' and cl=='NavArrows':self.arrows.append(d['href'])
 def handle_data(self,text):
    if self.field:self.texts.append(text)
 def handle_endtag(self,tag):
    if tag=='td' and self.field:
        v=' '.join(''.join(self.texts).split())
        if self.field=='DataletSideHeading':self.key=v
        elif self.key:self.values[self.key]=v
        self.field=None
def collect_cards(fetch=False):
 a=Archive('elkgrove',fetch,owner='illinois/elk_grove_village_cook_assessor');url=FIRST;positive=[];audit=[];n=1
 while True:
    b,h=a.get(url);p=Card();p.feed(b.decode('utf8',errors='replace'));q=p.values
    t=c.parse(b,'text/html',url)[1];m=re.search(r'Permit Information\s+(\d+) of (\d+)',t);assert m and int(m[1])==n and 'Parcel #: 08224030160000' in t
    # Only rows whose named applicant ties the work to the data center, not other tenants on this parcel.
    building='DATA HALL' in q.get('Permit Description','').upper()
    campus=building or bool(re.search(r'PRIME DATA CENT(?:ER|RE)',q.get('Applicant Name',''),re.I))
    permit=q['MUNI Permit Number'];raw=q['Issue Date'];valid=bool(permit and raw and raw not in ('N/A','-'))
    audit.append(dict(card=n,permit=permit,issue_date=raw,applicant=q.get('Applicant Name'),status=q.get('Permit Status'),description=q.get('Permit Description'),source=url,sha256=h,eligible=campus and valid))
    if campus and valid:
        day=datetime.strptime(raw,'%m/%d/%Y').date().isoformat()
        if day<='2026-11-15':
            positive.append(dict(id='elk-cook-'+q['Permit No.'],state='IL',jurisdiction='Elk Grove Village',county='Cook County',dataset='Cook County assessor municipal permit register',record_no=permit,project='Data hall — 1501 E Midway Court' if building else 'Prime Data Centers — Midway Court',kind=q['Permit Description'] or q['Primary Job Description'],status=q['Permit Status'],date=day,date_role='issue date field in assessor record',url=url,source_url=url,source_sha256=h,locator='Parcel 08224030160000, assessor permit '+q['Permit No.']+', municipal permit '+permit,details=dict(scope='Cook County reports the municipal permit number and issue date against 1501 E Midway Court. The field labeled Permit Status is reproduced as reported; this property-tax record does not confirm present permit validity.',tax_parcel='08224030160000',assessor_permit_no=q['Permit No.'],site_address='1501 E Midway Ct',mailing_address=q.get('Mailing Address'),work_description=q.get('Permit Description'),original_status=q['Permit Status'])))
    if n==int(m[2]):break
    n+=1;urls=[urljoin(url,x) for x in p.arrows if re.search(r'[?&]card='+str(n)+r'(?:&|$)',x)];assert len(urls)==1 and urlsplit(urls[0]).hostname==urlsplit(FIRST).hostname;url=urls[0]
 assert len(audit)==len(set(x['source'] for x in audit))
 c.dump(c.R/'data/national/cook_county_permit_audit.json',audit)
 raw,h=a.get(RES);txt=c.norm(c.parse(raw,'application/pdf',RES)[1]);assert 'resolution no. 53- 21' in txt and 'ayes: 5 nays: 0' in txt and 'september 2021' in txt and 'prime data centers' in txt
 positive.append(dict(id='elk-2021-resolution',state='IL',jurisdiction='Elk Grove Village',county='Cook County',dataset='Elk Grove Village redevelopment resolutions',record_no='53-21',project='Prime Data Centers — Busse–Elmhurst',kind='Development agreement',status='Approved',date='2021-09-14',date_role='resolution adoption date',url=RES+'#page=1',source_url=RES,source_sha256=h,locator='Resolution 53-21, p. 1, September 14, 2021',details=dict(scope='The village board authorized the mayor and clerk to execute a purchase and redevelopment agreement. The vote was 5–0 with one member absent. This was not a construction permit.')))
 c.dump(series_path('elkgrove_il'),positive);print(n,'parcel records read;',len(positive),'dated rows including redevelopment resolution')
def classify(r,cutoff,perm,no,app,obs):
 if r['dataset']=='Elk Grove Village redevelopment resolutions':return no('Redevelopment agreement, not construction approval.','decision')
 if r['status']=='C – CLOSED':return perm('IL:ELKGROVE:ASSESSOR','unconfirmed','Assessor lists a municipal permit number and issue date. Its closed assessment record does not establish current permit validity.',datetime.strptime(r['date'],'%Y-%m-%d').date())
 return no('The assessment register reports pending or recheck. No confirmation from the municipal issuing office.','observation')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');collect_cards(p.parse_args().fetch)
