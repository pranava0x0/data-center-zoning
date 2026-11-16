"""Chandler and Goodyear Accela Citizen Access project records, discovered through documented seed links in
data/history/arizona/accela_seeds.json and screened for data centers. Issuers: City of Chandler and City of Goodyear."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from collectors.arizona.common import *
def download(save,queries,reuse_details=False):
    seeds=js((collector_data('arizona','accela_seeds.json')).read_bytes())
    def detail(url):
        key='accela-'+hashlib.sha256(url.encode()).hexdigest()[:16]+'.html.gz'
        data,final=netfetch.get(url,timeout=45,with_url=True)
        return key,final,data
    # Individual public records discovered through documented seed links. No sign-in or captcha solving.
    for url in seeds:
        key='accela-'+hashlib.sha256(url.encode()).hexdigest()[:16]+'.html.gz'
        if reuse_details:
            data=gzip.decompress((C/key).read_bytes());save(key,url,data)
        else:
            key,final,b=detail(url);save(key,final,b);time.sleep(2)
    queries['accela']=len(seeds)
def rows(b):
    add=b.add;reject=b.reject;m=b.m
    for n in sorted(m):
        if not n.startswith('accela-'):continue
        h=lib.text.Fields();h.feed(gzip.decompress((C/n).read_bytes()).decode(errors='replace'));v=h.parts
        i=next(i for i,vv in enumerate(v) if vv in ('Case','Record') and v[i+2]==':');no,kind,status=v[i+1],v[i+3],v[i+5]
        def after(s):return v[v.index(s)+1] if s in v else ''
        title=after('Project Description:');scope=after('Detailed Scope of Work:');desc=title+' '+scope;hit=match(desc) or re.search(r'\bDATACTR\b',desc,re.I)
        if not hit:reject.append(['accela',no,'Project scope does not explicitly identify a data center or data hall']);continue
        loc='Goodyear' if '/GOODYEAR/' in m[n]['url'] else 'Chandler';url=m[n]['url']
        add('accela',n,no,title or no,kind,status,None,'Date not stated',loc,url,'Record Details, Project Description, Detailed Scope of Work; '+no,dict(issuer='City of '+loc,scope=scope,matched_text=hit.group()),key=loc+'-'+no)
