"""Recover code publisher referrals from archived government pages; a link is not a law.
Offline replay. Keep the referring page and byte hash; shared links do not confer jurisdiction.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, collections, gzip, html, re
from urllib.parse import urlsplit,urlunsplit
import lib.discovery as c
from ordinances.discovery.screen_local_sites import h,BASE,LOG
from ordinances.discovery.national_local_screen import safe
D=c.R/'data/national';POLICY={'library.municode.com':'Municode','ecode360.com':'General Code','codelibrary.amlegal.com':'American Legal Publishing','codepublishing.com':'Code Publishing','qcode.us':'Quality Code Publishing','en-code-decode.com':'Municipal code publisher','civicweb.net':'Municipal meeting records'}
LINK=re.compile(rb'''(?:href\s*=\s*["']|\b)((?:https?:)?//(?:[\w.-]+\.)?(?:municode\.com|ecode360\.com|amlegal\.com|codepublishing\.com|qcode\.us|civicweb\.net)/[^\s"'<>\\]{0,520})''',re.I)
def main():
 led=list(csv.DictReader((c.OUT/'national_jurisdiction_checks.csv').open()));geos=collections.defaultdict(set);parsed={};out=set()
 for g in led:
    if g['url'] and int(g['pages'] or 0)>0:geos[g['url']].add((g['state'],g['geoid'],g['name'],g['layer']))
 for origin,places in geos.items():
    visit=c.read(LOG/(h(origin.encode())+'.json'),{})
    for p in visit.get('pages',[]):
        sha=p['sha256']
        if sha not in parsed:
            file=BASE/(sha+'.gz');links=set()
            if file.exists():
                raw=gzip.decompress(file.read_bytes())
                for b in LINK.findall(raw):
                    href=html.unescape(b.decode('utf8','replace')).rstrip('.,;)}');href='https:'+href if href.startswith('//') else href
                    try:u=urlsplit(href);host=(u.hostname or '').lower()
                    except ValueError:continue
                    provider=next((v for k,v in POLICY.items() if host==k or host.endswith('.'+k)),None)
                    if not provider or len(u.path)<2 or re.search(r'\.(?:svg|png|gif|js|css|ico)$',u.path,re.I) or 'login' in u.path.lower():continue
                    links.add((provider,urlunsplit(('https',host,u.path,u.query,''))))
            parsed[sha]=links
        for st,gid,name,layer in places:
            for provider,href in parsed[sha]:out.add((st,gid,name,layer,provider,href,p['url'],sha))
 with (D/'local_code_referrals.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow('state geoid government layer provider url referring_page referring_sha256'.split());w.writerows(sorted(out))
 print(len(out),'cited code/meeting referrals;',len({r[1] for r in out}),'geographies;',len({r[0] for r in out}),'states and territories.')
if __name__=='__main__':main()
