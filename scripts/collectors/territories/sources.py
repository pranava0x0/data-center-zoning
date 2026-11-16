"""Discover territorial municipal offices from official directories, retaining unjoined records."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, re, csv, json, unicodedata
from urllib.parse import urljoin,urlsplit
import lib.discovery as c
from lib.url_archive import Archive
D=c.R/'data/national'
refs={'PR':'https://pr.gov/gobierno-2/directorio-municipios','GU':'https://mcog.guam.gov/directory','MP':'https://opd.gov.mp/directory.html','AS':'https://www.americansamoa.gov/_files/ugd/4bfff9_bba88c7d53cc48a9af8f2473d4431bd8.pdf','VI':'https://dpnr.vi.gov/coastal-zone-management/what-we-do/coastal-zone-permitting/'}
def norm(t):return ''.join(ch for ch in unicodedata.normalize('NFKD',t.lower()) if ch.isascii() and ch.isalnum())
def run(fetch):
 a=Archive('territorial',fetch,owner='territories',name='territorial_sources.json');gov=[];log=[]
 rows=list(csv.DictReader((D/'jurisdictions.csv').open()))
 for st,u in refs.items():
    try:b,h=a.get(u)
    except Exception as e:
        if not fetch:raise
        log.append([st,u,'Could not retrieve',str(e)[:150]]);continue
    fmt,text,links=c.parse(b,'application/pdf' if b[:4]==b'%PDF' else 'text/html',u);log.append([st,u,fmt,h])
    if st=='PR':
        for g in rows:
            if g['state']!=st or g['layer']!='counties':continue
            n=g['name'].removesuffix(' Municipio');matches=[urljoin(u,l) for l,t in links if norm(l.split('/')[-1])==norm(n) and ('municip' in l)]
            gov.append(dict(state=st,geoid=g['geoid'],name=n+' municipal government',url=matches[0] if matches else u,scope='Municipal directory listing' if matches else 'Territorial directory; individual page not joined'))
    else:gov.append(dict(state=st,geoid='',name={'MP':'Municipal mayors and government offices','GU':'Village mayors and vice mayors','AS':'Village councils and Office of Local Government','VI':'Department of Planning and Natural Resources'}[st],url=u,scope='Government directory or agency source; no permit decision inferred'))
 c.dump(D/'territory_directories.json',gov);c.dump(D/'territory_directory_checks.json',log)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--fetch',action='store_true');run(ap.parse_args().fetch)
