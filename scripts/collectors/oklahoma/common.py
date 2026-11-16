"""Oklahoma helpers shared by the source modules: the evidence store, manifest and output paths, the config-driven
capture step, the issuer-table parser, the CSV reader, and the build step that combines every issuer's records."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path, R
import lib.net as netfetch
from lib.archive import Store
from lib.files import j
from lib.text import htmltext, slug
import lib.discovery as collect, re, io, datetime as dt, collections, argparse
from urllib.parse import urljoin
from pypdf import PdfReader
ST=Store('OK');M=collector_data('oklahoma','manifest.json');O=series_path('ok');C=collector_data('oklahoma','config.json')
def capture(m,keys):
    for k,v in j(C).items():
        if k not in keys:continue
        if k not in m or netfetch.REFETCH:m[k]=ST.get(v['url'],v['ext']);collect.dump(M,m)
from html.parser import HTMLParser
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.arr=[];self.tab=None;self.row=None;self.cell=None
    def handle_starttag(self,t,attrs):
        if t=='table':self.tab=[];self.arr.append(self.tab)
        elif t=='tr' and self.tab is not None:self.row=[];self.tab.append(self.row)
        elif t in ('th','td') and self.row is not None:self.cell=[[],[]];self.row.append(self.cell)
        elif t=='a' and self.cell is not None:self.cell[1].append(dict(attrs).get('href',''))
    def handle_data(self,s):
        if self.cell is not None:self.cell[0].append(s)
    def handle_endtag(self,t):
        if t in ('th','td'):self.cell=None
        elif t=='tr':self.row=None
        elif t=='table':self.tab=None
def tables(b):
    p=Tables();p.feed(b.decode('utf8','replace'))
    return [[ [(' '.join(' '.join(v).split()),u) for v,u in row] for row in tab] for tab in p.arr]
def csv_rows(m,k):
    import csv
    return list(csv.DictReader(io.StringIO(ST.read(m[k]).decode('utf-8-sig','replace'))))
def build(m,geo,register,tulsa):
    """geo: ranking module; register/tulsa: issuer modules whose rows() add records to `out` (and `holds`)."""
    oo=j(collector_data('oklahoma','ocr.json'));geo.rankings(m);out={};holds=[]
    nrows=register.rows(m,out,holds,oo)
    tulsa.rows(m,out)
    collect.dump(O,sorted(out.values(),key=lambda a:a['id']));collect.dump(collector_data('oklahoma','review.json'),holds);collect.dump(collector_data('oklahoma','coverage.json'),dict(register_rows=nrows-2,records=len(out),datasets=dict(collections.Counter(x['dataset'] for x in out.values())),undated=sum(x['date'] is None for x in out.values()),holds=holds))
