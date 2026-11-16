"""Atlanta Regional Commission (ARC) Developments of Regional Impact (DRI) review register
(planreviews.atlantaregional.com), with the review reports linked from each entry."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt
import re
from urllib.parse import urlencode
import lib.discovery as collect
import lib.net as netfetch
from collectors.georgia.evidence_store import M, get, htmlref, links, text, pdfpages, docmatch, parsedate, row, slug, DC
ARC='https://planreviews.atlantaregional.com/planreviewsresult.aspx'
def arc_rows(h):
    for frag in re.split(r'<p>\s*<strong>',h,flags=re.I)[1:]:
        title=text(frag.split('</strong>')[0]);fields={k:text(v) for k,v in re.findall(r'(Type|Review Code|Jurisdiction|Date Opened|Status):\s*(.*?)\s*<br\s*/?>',frag,re.I|re.S)}
        if fields.get('Type')!='DRI':continue
        ls=links(frag.split('</ul>',1)[0]);pdf=[(u,t) for u,t in ls if '.pdf' in u.lower()]
        def score(a):
            f=a[1].lower();return 0 if 'final' in f and 'report' in f else 1 if 'final' in f else 2 if 'prelim' in f else 3 if 'report' in f else 4
        best=sorted(pdf,key=score)[0] if pdf else None
        yield dict(title=title,fields=fields,doc=collect.address(best[0].replace('http:','https:',1)) if best else None,document_title=best[1] if best else None)
def fetch(c,m):
    for key in c['arc_terms']:
        if key in m.setdefault('arc_queries',{}):continue
        u=ARC+'?'+urlencode({'fulltext.search.query':key});first=get(u,'html');h=htmlref(first);num=re.search(r'Search Results\s*\((\d+)\)',text(h));pages=[first]
        if not num:raise ValueError('ARC missing result count')
        for i in range(2,(int(num[1])+9)//10+1):pages.append(get(ARC+'?'+urlencode({'revChunk':i,'fulltext.search.query':key}),'html'))
        m['arc_queries'][key]=pages;collect.dump(M,m)
def fetch_proofs(m):
    arc={}
    for rs in m['arc_queries'].values():
        for r in rs:
            for a in arc_rows(htmlref(r)):
                if a['doc']:arc[a['fields']['Review Code']]=a['doc']
    for k,dd in [('arc_docs',arc)]:
        for n,u in sorted(dd.items()):
            if not u or n in m.setdefault(k,{}):continue
            try:m[k][n]=get(u,'pdf')
            except (OSError,ValueError) as e:m[k][n]={'url':u,'error':str(e)}
            collect.dump(M,m)
        print(k,len(dd),flush=True)
def rows(m,co):
    holds=[];out=[];arc={}
    for rs in m['arc_queries'].values():
        for r in rs:
            for a in arc_rows(htmlref(r)):arc[a['fields']['Review Code']]=a,r
    for n,(a,r) in sorted(arc.items()):
        f=a['fields'];doc=m['arc_docs'].get(n,{}); wrong_case=n.isnumeric() and (q:=re.search(r'\bDRI\s*#?\s*(\d{4})',a['document_title'] or '',re.I)) and q[1]!=n
        if wrong_case:doc={};a=dict(a,document_title=None)
        hit=docmatch(doc)
        if not DC.search(a['title']) and not hit:
            holds.append(dict(group='ARC',key=n,title=a['title'],reason='No report with explicit data-center scope or explicit case title.'));continue
        ref=doc if 'sha256' in doc else r;t=pdfpages(doc['sha256'])[0] if 'sha256' in doc else '';od=parsedate(f['Date Opened']);role='regional review opened';day=od
        q=re.search(r'\bDATE\s*:\s*([a-z.]+\s+\d{1,2},?\s+\d{4})',t,re.I)
        d=parsedate(q[1]) if q else None
        if 'final' in (a['document_title'] or '').lower() and d and od and d>=od:day=d;role='regional finding date'
        params=dict(opened=od,document_title=a['document_title'],register_url=r['url'],register_sha256=r['sha256'])
        if wrong_case:params['document_exclusion']='Linked document names a different DRI number; only the register was used.'
        if d and od and d<od:params['report_date_precedes_opening']=d
        if hit:params.update(identity_page=hit[0],identity_evidence=hit[1])
        juris=f['Jurisdiction']
        if ' County' in juris and juris in co.values():params['county']=juris
        x=row('Atlanta Regional Commission DRI reviews','arc-'+slug(n),juris,n,a['title'],'Development of Regional Impact review',f['Status'],day,role,ref,'ARC review code '+n+'; '+(a['document_title'] or 'search register'),**params);x['source_url']=r['url'];out.append(x)
    return out,holds,arc
