"""Indiana Department of Homeland Security, Building Plan Review: Project Activity report register (construction design
release applications and releases), screened for data center projects."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import calendar, datetime as dt, io, json, re
from urllib.parse import urlencode
from pypdf import PdfReader
import lib.discovery as collect
from collectors.indiana.evidence_store import R, M, DETAILS, get, read, txt, j, parse_date, netfetch
ROOT='https://oas.dhs.in.gov/reports/rwservlet?dfbsepnhtml&report=plan_design_release_for_web.rdf&'
def reports(h):
    if 'Submission&nbsp;Summary' not in h:raise ValueError('not a submission summary: '+txt(h)[-230:])
    sections=re.split('Project&nbsp;Number:',h,flags=re.I)[1:]
    last_partial={}
    for pos,section in enumerate(sections):
        cells=[txt(x) for x in re.findall('<td\\b[^>]*>(.*?)</td>',section,re.S|re.I)];cells=[x for x in cells if x]
        if 'Project Details' not in cells and pos+1<len(sections) and re.search(r'color="#ff0000"><b>'+re.escape(cells[0])+r'</b>',sections[pos+1]) and 'p_form_id=' not in section and 'p_release_id=' not in section:
            last_partial[cells[0]]=cells[2];continue
        if cells[1]!='County :' or 'Project Details' not in cells:raise ValueError('unexpected project columns')
        i=cells.index('Project Details'); nm=cells[i+2];use=' '.join(cells[4:i]); links=collect.HTML();links.feed(section)
        yield cells[0],(last_partial[cells[0]] if cells[2]=='Project Details' else cells[2]),use,nm,links.links
def windows(c):
    for y in range(int(c['start_file_date'][:4]),int(c['cutoff'][:4])+1):
        for n in range(1,13):
            first=dt.date(y,n,1);end=min(dt.date(y,n,calendar.monthrange(y,n)[1]),dt.date.fromisoformat(c['cutoff']))
            first=max(first,dt.date.fromisoformat(c['start_file_date']))
            if first<=end:yield dict(area='New Carlisle monthly mailing city',county=71,city='NEW CARLISLE',start=first.isoformat(),end=end.isoformat())
    yield from c['address_screens']
def datefmt(x):return dt.date.fromisoformat(x).strftime('%m/%d/%Y')
def download(c,m):
    for w in windows(c):
        q={'P_FROM_DATE_FILED':datefmt(w['start']),'P_TO_DATE_FILED':datefmt(w['end']),'P_county':str(w['county']).zfill(2)}
        if 'city' in w:q['P_city']=w['city']
        if 'street_no' in w:q['P_st_number']=w['street_no']
        url=ROOT+urlencode(q)
        if url in m['queries'] and 'error' not in m['queries'][url] and not netfetch.REFETCH:continue
        if url in m['queries'] and m['queries'][url].get('ref'):
            try:
                old=m['queries'][url]; n=len(list(reports(read(old['ref']).decode('utf8','replace')))); old.pop('error');old['screened_projects']=n;collect.dump(M,m);continue
            except ValueError:pass
        try:
            ref=get(url,'html');h=read(ref).decode('utf8','replace');n=len(list(reports(h)))
            rr=dict(**w,ref=ref,screened_projects=n)
        except Exception as e:
            rr=dict(**w,error=str(e))
            if 'ref' in locals() and ref['url']==url:rr['ref']=ref
        m['queries'][url]=rr;collect.dump(M,m);print(w['area'],w['start'],rr.get('screened_projects',rr.get('error')),flush=True)
DC=re.compile(r'\b(?:data\s*(?:cent(?:er|re)|ctr)s?|server\s+farms?)\b',re.I)
def candidates(m):
    result={}
    for w in list(m['queries'].values())+list(m.get('cases',{}).values()):
        if 'error' in w:continue
        for no,county,use,name,links in reports(read(w['ref']).decode('utf8','replace')):
            if not re.fullmatch(r'\d+',no):raise ValueError(no)
            p=result.setdefault(no,dict(county=county,use=use,name=name,links={},source=w['ref'],areas=[]));p['areas'].append(w['area'])
            if p['county']!=county or p['name']!=name:raise ValueError('Project identity changed: '+no)
            for u,t in links:
                mat=re.search(r'p_(form|release)_id=(\d+)',u)
                if mat and 'dfbsepnpdf' in u:p['links'][mat.groups()]=(u,t,w['ref'])
    return result
def formfetch(m):
    out=j(DETAILS) if DETAILS.exists() else {}
    for no,p in sorted(candidates(m).items()):
        if no in out:continue
        if not (DC.search(p['name']+' '+p['use']) or re.search(r'\b(?:IEC|EKI|AWS|SBN|Orion|Zodiac|Math Science)',p['name'],re.I)):continue
        fs=[(t,u) for (kind,_),(u,t,_) in p['links'].items() if kind=='form']
        fs.sort(key=lambda a:('Form STD' not in a[0],a[1]))
        if not fs:continue
        t,u=fs[0]
        try:out[no]=get(u,'pdf')
        except Exception as e:out[no]={'url':u,'error':str(e)}
        collect.dump(DETAILS,out)
FORM_CHECKS={'443702':'stored or handled DATA CENTER', '447700':'New data center building.', '451903':'New data center buiding.', '455489':'Existing academica building w/ an academic data center.'}
def promoted(no,p):return bool(DC.search(p['name']+' '+p['use']) or no in FORM_CHECKS)
def casefetch(m):
    for n,p in sorted(candidates(m).items()):
        if not promoted(n,p) or n in m.setdefault('cases',{}):continue
        u=ROOT+urlencode(dict(P_sbc_number=n))
        try:
            ref=get(u,'html');res=list(reports(read(ref).decode('utf8','replace')))
            if len(res)!=1 or res[0][0]!=n:raise ValueError('case detail verifier failed')
            m['cases'][n]=dict(area='Individual SBC project',ref=ref)
        except Exception as e:m['cases'][n]=dict(area='Individual SBC project',error=str(e))
        collect.dump(M,m)
def loc(form,no):
    if not form or 'error' in form:return {}
    pp=PdfReader(io.BytesIO(read(form))).pages[0];layout=pp.extract_text(extraction_mode='layout');flat=' '.join(layout.split())
    if no not in flat:return {}
    for line in layout.splitlines():
        m=re.search(r'^\s*(.*?)\s{2,}IN\s+\d{5}(?:-\d{4})?\s+(.+?)\s{2,}limits\?\s+(Yes|No)\b',line,re.I)
        if m:return dict(reported_city=m[1].title(),application_county=m[2].strip(),inside_reported_city=m[3].lower()=='yes',location_evidence='Project Location: Is project in city limits?',location_source=form['url'],location_source_sha256=form['sha256'])
    return {}
def cty(k):return {'ST JOSEPH':'St. Joseph County','LAPORTE':'La Porte County'}.get(k.upper(),k.title()+' County')
def rows(c,m,add):
    """Records plus the held list and screened-project map the coverage file reports."""
    forms=j(DETAILS) if DETAILS.exists() else {};projs=candidates(m);held=[]
    for no,p in sorted(projs.items()):
        if not promoted(no,p):
            held.append(dict(project_number=no,name=p['name'],facility_use=p['use'],reason='No explicit data center/ctr or server farm in register project name or facility use',areas=sorted(set(p['areas']))))
            continue
        g=loc(forms.get(no),no);county=cty(p['county'])
        if no in FORM_CHECKS:
            r=forms[no];pg=PdfReader(io.BytesIO(read(r))).pages[0];tx=' '.join(pg.extract_text(extraction_mode='layout').split())
            if FORM_CHECKS[no].casefold() not in tx.casefold():raise ValueError('Application use citation mismatch '+no)
            g.update(use_evidence=FORM_CHECKS[no],use_source=r['url'],use_source_sha256=r['sha256'])
        if 'application_county' in g and re.sub('[^a-z]','',g['application_county'].lower())!=re.sub('[^a-z]','',p['county'].lower()):raise ValueError('Conflicting counties '+no)
        city=g.get('reported_city') if g.get('inside_reported_city') else None
        for (k,num),(u,t,ref) in sorted(p['links'].items()):
            if k=='form':
                mt=re.search(r'Form\s+(\S+)\s+filed on\s+(\d+/\d+/\d+)',t,re.I)
                if not mt:raise ValueError('Unknown form event: '+t)
                form_type,d=mt.groups();status='filed';role='form filed';kind='Construction design release application';extra={'form_type':form_type}
            else:
                mt=re.search(r'(\d+/\d+/\d+)\s*:\s*(.*?)\s*\(report for',t,re.I)
                if not mt:raise ValueError('Unknown release event: '+t)
                d,status=mt.groups();role='release date';kind='Construction design release';extra={'release_type':status}
            add('dhs-'+k+'-'+num,'Indiana DHS Project Activity',num,p['name'],kind,status,parse_date(d),role,u,'SBC '+no+' / '+k+' ID '+num,ref,county,dict(sbc_project_number=no,agency='Indiana Department of Homeland Security, Building Plan Review',source_facility_use=p['use'],published_link_text=t,**extra,**g),city)
    return held,projs
