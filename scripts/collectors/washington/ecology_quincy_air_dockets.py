"""Replay the Washington Ecology Quincy permit docket. Adjacent project headings must never share an order number.
Single source, so not split: Washington State Department of Ecology air construction dockets for Quincy data centers."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, re, html, collections, datetime
from urllib.parse import urljoin
from lib.url_archive import Archive
import lib.discovery as c
U='https://ecology.wa.gov/air-climate/air-quality/data-centers';DS='Washington Ecology Quincy air construction dockets'
def txt(s):return ' '.join(html.unescape(re.sub('<[^>]+>',' ',s)).split())
ORDER=re.compile(r'\b\d{2}AQ[-–]E\d{3,4}\b',re.I)
def run(fetch):
 a=Archive('wastate',fetch,owner='washington');b,sha=a.get(U);parts=re.split(r'<button\b[^>]*>(.*?)</button>',b.decode(),flags=re.I|re.S);out=[];held=[]
 for i in range(1,len(parts),2):
    title=txt(parts[i]);parts2=re.split(r'\s+[-–]\s+',title,maxsplit=1)
    if len(parts2)!=2 or parts2[0]!='Quincy':continue
    project=parts2[1];doc=parts[i+1].split('</section>',1)[0];hdrs=[]
    for m in re.finditer(r'<(?:strong|h[3-6])\b[^>]*>(.*?)</(?:strong|h[3-6])>|<li>\s*(Air quality permit documents for permit number[^<]+)',doc,re.S|re.I):
        head=txt(m[1] or m[2])
        if 'permit' in head.lower():hdrs.append((m.start(),head))
    for m in re.finditer(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>([^<]*)',doc,re.S|re.I):
        lab=txt(m[2]);tail=txt(m[3]);u=urljoin(U,html.unescape(m[1]))
        if 'application' in lab.lower() and 'construction' in lab.lower():kind='Air permit application';status='Application listed'
        elif re.search('approv(?:al|e) order',lab,re.I):kind='Air construction approval order';status='Issued'
        else:continue
        head=next((v for pos,v in reversed(hdrs) if pos<m.start()),'');num=ORDER.search(lab) or ORDER.search(head)
        d=re.search(r'\b(\d{1,2}/\d{1,2}/(?:\d{4}|\d{2}))\b',tail+' '+lab)
        if not (num and d):
            held.append([title,lab,tail,'No project-scoped order number or exact day']);continue
        val=d[1];date=datetime.datetime.strptime(val,'%m/%d/%Y' if len(val.split('/')[-1])==4 else '%m/%d/%y').date().isoformat()
        if date>'2026-11-15':continue
        if kind.endswith('order') and 'rescinded' in (head+' '+tail).lower():status='Rescinded'
        n=num[0].upper().replace('–','-');docid=c.digest((title+n+date+kind+u).encode())[:16]
        out.append(dict(id='wa-ecy-'+docid,state='WA',dataset=DS,record_no=n,jurisdiction='Quincy',county='Grant County',project=project+' · Quincy',kind=kind,status=status,date=date,date_role='Approval order date' if kind.endswith('order') else 'Application document date',url=u,source_url=U,source_sha256=sha,locator=title+' · '+head+' · '+lab+' ('+val+')',details=dict(agency='Washington State Department of Ecology',heading=head,document_label=lab,document_url=u,docket_url=U)))
 if len(set(r['id'] for r in out))!=len(out):raise ValueError('Duplicate Washington docket event')
 c.dump(series_path('wa'),out);c.dump(c.R/'data/national/wa_unmatched.json',held);print(len(out),'dated events;',len(held),'held;',collections.Counter(r['status'] for r in out))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
