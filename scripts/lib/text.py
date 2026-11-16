"""HTML/PDF text extraction and date parsing shared by collectors."""
import html, re
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser


def isodate(s):
    if s in ('',None):return None
    if isinstance(s,(int,float)):
        dt=datetime.fromtimestamp(s/1000,timezone.utc).date().isoformat()
        return None if dt=='1900-01-01' else dt
    if re.match(r'^\d{4}-',s):return datetime.fromisoformat(s).date().isoformat()
    for fmt in ('%m/%d/%y','%m/%d/%Y'):
        try:return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:pass
    raise ValueError('Unrecognized date: '+s)
class Fields(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,d):
        if d.strip():self.parts.append(' '.join(d.split()))
def slug(s):return re.sub(r'[^a-z0-9]+','-',str(s).lower()).strip('-')
def htmltext(b):return ' '.join(unescape(re.sub(r'<[^>]+>',' ',b.decode('utf-8','replace'))).split())
def plain(s):return ' '.join(html.unescape(re.sub(r'<[^>]*>',' ',s)).split())
def strip(s):return ' '.join(html.unescape(re.sub('<[^>]*>',' ',s)).split())
def tr(s):return re.findall(r'<tr\b[^>]*>(.*?)</tr>',s,re.S|re.I)
def ms(v):return datetime.fromtimestamp(v/1000,tz=timezone.utc).date().isoformat() if v else None
class TableParser(HTMLParser):
    """Return each table as separate rows, preserving text and links per cell."""
    def __init__(self):super().__init__(convert_charrefs=True);self.tables=[];self.depth=0;self.tab=None;self.row=None;self.cell=None;self.text=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if self.skip:return
        if tag=='table':
            self.depth+=1
            if self.depth==1:self.tab=[];self.tables.append(self.tab)
        elif self.depth==1:
            if tag=='tr':self.row=[];self.tab.append(self.row)
            elif tag in ('td','th') and self.row is not None:
                self.cell={'text':[],'links':[]};self.row.append(self.cell)
            elif tag=='a' and self.cell is not None:
                u=dict(attrs).get('href')
                if u:self.cell['links'].append(u)
            elif tag in ('br','p','div') and self.cell is not None:self.cell['text'].append(' ')
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag=='table' and self.depth:self.depth-=1
        if self.depth==1:
            if tag in ('td','th'):self.cell=None
            if tag=='tr':self.row=None;self.cell=None
    def handle_data(self,d):
        if self.skip:return
        self.text.append(d)
        if self.depth==1 and self.cell is not None:self.cell['text'].append(d)
def date(v,local=False):
    if v in (None,'',0):return None
    if isinstance(v,(float,int)):
        # Phoenix GIS timestamps contain actual local times; midnight issue/status dates have a +7h UTC shift.
        tz=timezone(timedelta(hours=-7)) if local else timezone.utc
        return datetime.fromtimestamp(v/1000,tz).date().isoformat()
    return isodate(v)
