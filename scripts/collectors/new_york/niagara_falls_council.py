"""Screen the Niagara Falls council's dated official minutes links for project-specific land-use actions."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import lib.net as netfetch
from urllib.request import urlopen
from urllib.parse import quote
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime as dt, sys, re, html, json, fitz
from collectors.new_york.source_store import D
U='https://www.niagarafallsny.gov/government/city_council.php'
def fetch():
    b=netfetch.get(U,timeout=22);(D/'niagara-index.html').write_bytes(b)
    todo=[]
    for row in re.split(r'<tr\b',b.decode(),flags=re.I):
        d=re.search(r'agenda-date">([0-9/]+)',row)
        if not d:continue
        day=dt.datetime.strptime(d[1],'%m/%d/%Y').date().isoformat()
        if not '2023-01-01'<=day<='2026-11-15':continue
        a=re.search(r'class="minutes_doc".*?href="([^"]+)"[^>]+>\s*Minutes\s*<',row.split('</tr>')[0],re.S|re.I)
        if not a:continue
        url=quote(html.unescape(a[1]),safe=':/?=&%,()+')
        todo.append((day,url))
    def pull(item):
        day,url=item;fname='niagara-'+day+'-'+__import__('hashlib').sha1(url.encode()).hexdigest()[:7]+'.pdf';p=D/fname
        try:
            if not p.exists():
                b=netfetch.get(url,timeout=20,limit=9*1024**2)
                if not b.startswith(b'%PDF'):raise ValueError('non-PDF or exceeds 9 MiB limit')
                p.write_bytes(b)
            doc=fitz.open(p);lines=[(i+1,pg.get_text()) for i,pg in enumerate(doc)]
            hits=[]
            for i,text in lines:
                for m in re.finditer(r'(?i)north\s*east data|block\s*fusion|data cent(?:er|re)|5380 frontier|2450 buffalo|US data tech|digital asset mining',text):
                    hits.append((i,' '.join(text[max(0,m.start()-105):m.end()+240].split())))
            return dict(date=day,url=url,file=fname,pages=len(lines),no_text_pages=sum(not s.strip() for _,s in lines),hits=hits)
        except Exception as e:return dict(date=day,url=url,hold=str(e))
    with ThreadPoolExecutor(max_workers=3) as pool:out=list(pool.map(pull,todo))
    (D/'niagara-index.json').write_text(json.dumps(out,indent=2)+'\n');print(len(out),sum(bool(x.get('hits')) for x in out))
if __name__=='__main__':fetch()
