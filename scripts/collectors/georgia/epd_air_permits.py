"""Georgia Environmental Protection Division (EPD) Issued Air Permits register (air.gaepd.org), with the permit
narratives and instruments linked from each register row."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
import datetime as dt
import re
import lib.net as netfetch
from urllib.parse import urlencode, urljoin
import lib.discovery as collect
from collectors.georgia.evidence_store import R, M, DC, get, j, htmlref, links, pdfpages, docmatch, row, slug, text
AIR='https://air.gaepd.org'
def air_rows(h):
    for tr in re.findall(r'<tr\b.*?</tr>',h,re.I|re.S):
        if 'data-label="Facility ID"' not in tr:continue
        d={k:text(v) for k,v in re.findall(r'<(?:th|td)\b[^>]*data-label="([^"]+)"[^>]*>(.*?)</(?:th|td)>',tr,re.S|re.I)};ls=links(tr)
        url=next((urljoin(AIR,u) for u,t in ls if t==d.get('Permit') and '/Permits/View/' in u),None)
        nr=next((urljoin(AIR,u) for u,t in ls if t=='Narrative'),None)
        yield dict(fid=d['Facility ID'],name=d['Facility Name'],num=d['Permit'],day=dt.datetime.strptime(d['Issuance Date'].replace('‑','-'),'%d-%b-%Y').date().isoformat(),kind=d['Permit Type'],url=url,narrative=nr)
def fetch(c,m):
    for key,p in c['air_search'].items():
        if key not in m.setdefault('air_queries',{}) or netfetch.REFETCH:
            r=get(AIR+'/Permits/Search?'+urlencode(p),'html');h=htmlref(r)
            if 'SearchResults' not in h:raise ValueError('unexpected EPD response')
            pages=[r];seen={r['url']}
            while True:
                nxt=next((urljoin(AIR,u).split('#')[0] for u,t in links(h) if t.lower()=='next'),None)
                if not nxt:break
                if nxt in seen or len(pages)>=100:raise ValueError('pagination loop')
                seen.add(nxt);rp=get(nxt,'html');pages.append(rp);h=htmlref(rp)
            m['air_queries'][key]=pages;collect.dump(M,m)
def fetch_proofs(m):
    byfac={}
    for r in [ref for rs in m['air_queries'].values() for ref in (rs if isinstance(rs,list) else [rs])]:
        for a in air_rows(htmlref(r)):byfac.setdefault(a['fid'],{})[a['num']]=a
    for k,dd in [('air_docs',{n:next((a['narrative'] for a in sorted(v.values(),key=lambda a:a['day'],reverse=True) if a['narrative']),None) or next((a['url'] for a in v.values() if a['url']),None) for n,v in byfac.items()})]:
        for n,u in sorted(dd.items()):
            if not u or n in m.setdefault(k,{}):continue
            try:m[k][n]=get(u,'pdf')
            except (OSError,ValueError) as e:m[k][n]={'url':u,'error':str(e)}
            collect.dump(M,m)
        print(k,len(dd),flush=True)
PERM=collector_data('georgia','permit_files.json')
def permitfiles(m):
    p=j(PERM) if PERM.exists() else {}
    pool={a['num']:a for rs in m['air_queries'].values() for r in (rs if isinstance(rs,list) else [rs]) for a in air_rows(htmlref(r))}
    for n,a in sorted(pool.items()):
        if n in p:continue
        x={}
        for k in ['narrative','url']:
            u=a[k]
            if u:
                try:x[k]=get(u,'pdf')
                except (ValueError,OSError) as e:x[k]={'url':u,'error':str(e)}
        p[n]=x;collect.dump(PERM,p)
def rows(m,co):
    files=j(PERM);holds=[];out=[];pool={}
    for rs in m['air_queries'].values():
        for r in rs if isinstance(rs,list) else [rs]:
            for a in air_rows(htmlref(r)):
                if a['num'] in pool and pool[a['num']][0]!=a:raise ValueError('Conflicting EPD row '+a['num'])
                pool[a['num']]=a,r
    if set(pool)!=set(files):raise ValueError('Per-permit capture incomplete')
    for n,(a,r) in sorted(pool.items()):
        docs=files[n]; doclist=[v for k in ('narrative','url') if (v:=docs.get(k)) and 'sha256' in v]
        matched=next(((v,hit) for v in doclist if (hit:=docmatch(v))),None)
        namehit=DC.search(a['name'])
        if not (namehit or matched):
            holds.append(dict(group='EPD',key=n,title=a['name'],reason='No explicit data-center use in the register name or the first seven pages of either linked instrument.'));continue
        ref=docs.get('url',{});ref=ref if 'sha256' in ref else r
        params=dict(facility_id=a['fid'],permit_type=a['kind'],register_url=r['url'],register_sha256=r['sha256'],identity_basis='register facility name' if namehit else 'same permit file')
        if matched:
            v,(pg,ev)=matched;params.update(identity_source=v['url'],identity_sha256=v['sha256'],identity_page=pg,identity_evidence=ev)
        if namehit and not matched:params['identity_evidence']=a['name']
        county=co.get(a['fid'].split('-')[0])
        for v in doclist:
            if county and any(re.search(r'\b'+re.escape(county)+r'\b',t,re.I) for t in pdfpages(v['sha256'])[:2]):
                params.update(county=county,county_source=v['url']);break
        x=row('Georgia EPD issued air permits','epd-air-'+slug(n),params.get('county','Georgia'),n,a['name'],a['kind']+' air permit','Issued',a['day'],'issuance date',ref,'Issued Air Permits register; permit '+n+'; AIRS '+a['fid'],**params);x['source_url']=r['url'];out.append(x)
    return out,holds,pool
