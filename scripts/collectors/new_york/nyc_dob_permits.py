"""New York City Department of Buildings (NYC Open Data): job filings (BIS, DOB NOW), BIS permit issuance, DOB NOW
approved permits and the electrical job register, filtered to data-center descriptions."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from collectors.new_york.source_store import D,CITY,EL,NOW,NJ,BIS,BP,NY_FLD,BOROS,fetch_series,get,put,read,url,iso,dataurl,eq,matched,uniq,mk
def download():
    D.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(fetch_series,[NOW,NJ,BIS,EL]))
    jobs=sorted({v['job__'] for v in read(BIS)['rows'] if matched(v.get('job_description',''))});allrows=[];urls=[]
    for i in range(0,len(jobs),70):
        keys=jobs[i:i+70]
        if not all(v.isdigit() for v in keys):raise ValueError('Bad job ID')
        where="job__ in ("+','.join("'"+v+"'" for v in keys)+')';u=url(CITY,BP,**{'$where':where,'$select':NY_FLD[BP],'$order':':id','$limit':50000});rows=get(u)
        if len(rows)>=50000:raise ValueError('Capped permit join')
        allrows.extend(rows);urls.append(u)
    put(BP,dict(count=len(allrows),urls=urls,rows=allrows));print(BP,len(allrows))
def rows():
    out=[];jmap={}
    for ds in (BIS,NJ):
        jobs=defaultdict(list)
        for r in read(ds)['rows']:
            if matched(r.get('job_description')):jobs[(r.get('job__') or r['job_filing_number'],r.get('doc__') or '')].append(r)
        for (j,doc),rr in jobs.items():
            if len({(v['borough'].upper(),v.get('bin__') or v.get('bin'),iso(v.get('pre__filing_date') or v.get('filing_date'))) for v in rr})!=1:raise ValueError('Conflicting DOB job identity')
            last=max(rr,key=lambda a:iso(a.get('latest_action_date') or a.get('current_status_date')) or '');r=last;n=j+('-'+doc if doc else '');b=r['borough'].upper();day=iso(r.get('pre__filing_date') or r.get('filing_date'))
            description=' / '.join(sorted({v['job_description'] for v in rr}));h=r.get('house__') or r.get('house_no') or '';addr=(h+' '+r.get('street_name','')).strip()
            q=eq('job__',j)+' AND '+eq('doc__',doc) if ds==BIS else eq('job_filing_number',j)
            u=dataurl(CITY,ds,q);jmap[j,doc]=(r,description,u)
            out.append(mk('NYC DOB building job filings','job-'+ds+'-'+n,'Building job application',r.get('job_status_descrp') or r['filing_status'],n,day,'filing date',u,'Job/document '+n,description,'New York',BOROS[b],D/(ds+'.json.gz'),issuer='New York City Department of Buildings',source_series=ds,borough=b,bin=r.get('bin__') or r.get('bin'),address=addr,latest_status_date=iso(r.get('latest_action_date') or r.get('current_status_date')),raw_match_rows=len(rr),identity_basis='Explicit job description (including alterations to rooms in existing facilities).'))
    for r in read(BP)['rows']:
        j=r['job__'];doc=r['job_doc___'];h=jmap.get((j,doc))
        if not h or r['bin__']!=h[0]['bin__'] or r['borough'].upper()!=h[0]['borough'].upper():continue
        jrec,desc,ju=h;typ=r.get('permit_type');ser=r.get('permit_si_no')
        if not (typ and ser and r.get('issuance_date')):continue
        n=j+'-'+doc+'-'+typ;u=dataurl(CITY,BP,eq('permit_si_no',ser));b=r['borough'].upper()
        out.append(mk('NYC BIS permit issuance','bis-'+ser,'Building permit / '+str(r.get('work_type') or typ),r.get('permit_status') or 'Not reported',n,iso(r['issuance_date']),'issue date',u,'permit_si_no '+ser+'; underlying DOB permit '+n,desc,'New York',BOROS[b],D/(BP+'.json.gz'),issuer='New York City Department of Buildings',source_series=BP,linked_job_url=ju,permit_sequence=r.get('permit_sequence__'),permit_type=typ,work_type=r.get('work_type'),filing_status=r.get('filing_status'),borough=b,bin=r['bin__'],address=r.get('house__','')+' '+r['street_name'],expiration_date=iso(r.get('expiration_date')),identity_basis='Exact job number + document number + BIN + borough joined to explicitly matching job narrative.'))
    modern=defaultdict(list)
    for m in uniq(read(NOW)['rows']):modern[(m['work_permit'],m['sequence_number'])].append(m)
    for group in modern.values():
        check={json.dumps({k:v for k,v in m.items() if k!='work_type'},sort_keys=True) for m in group}
        if len(check)!=1:raise ValueError('Contradictory same-sequence modern permit')
        r=dict(group[0]);r['work_type']=' / '.join(sorted({m['work_type'] for m in group}))
        if not matched(r.get('job_description')) or not r.get('issued_date'):continue
        n=r['work_permit'];seq=r['sequence_number'];b=r['borough'].upper();u=dataurl(CITY,NOW,eq('work_permit',n)+' AND '+eq('sequence_number',seq))
        out.append(mk('NYC DOB NOW approved building permits','now-'+n+'-'+seq,'Building permit / '+r['work_type'],r['permit_status'],n,iso(r['issued_date']),'issue date',u,'work_permit '+n+'; sequence '+seq,r['job_description'],'New York',BOROS[b],D/(NOW+'.json.gz'),issuer='New York City Department of Buildings',source_series=NOW,job_number=r['job_filing_number'],address=r.get('house_no','')+' '+r['street_name'],borough=b,bin=r.get('bin'),sequence=seq,filing_reason=r.get('filing_reason'),expiration_date=iso(r.get('expired_date')),identity_basis='Explicit permit description.'))
    for r in uniq(read(EL)['rows']):
        if not matched(r.get('job_description')):continue
        n=r['job_filing_number'];d=iso(r.get('permit_issued_date'));b=r['borough'].upper();u=dataurl(CITY,EL,eq('job_filing_number',n))
        out.append(mk('NYC DOB electrical job register','elec-'+n,'Electrical permit filing',r['filing_status'],n,d or iso(r['filing_date']),'reported permit issue date' if d else 'filing date',u,'job_filing_number '+n,r['job_description'],'New York',BOROS[b],D/(EL+'.json.gz'),issuer='New York City Department of Buildings',source_series=EL,borough=b,bin=r.get('bin'),address=r.get('house_number','')+' '+r['street_name'],job_status=r.get('job_status'),job_number=r['job_number'],filing_type=r['filing_type'],identity_basis='Electrical register supplies a filing ID; no separately identified permit number.'))
    return [r for r in out if r]
