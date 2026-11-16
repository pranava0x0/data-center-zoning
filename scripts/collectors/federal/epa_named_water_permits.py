"""Extract explicitly named data-center water permits, preserving who actually issued them.
Default pass is state-issued (ST6) only. No county is inferred from a mailing city.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, collections, csv, io, json, re, zipfile
from pathlib import Path
import lib.discovery as c
from lib.epa_icis import digest, iso, URL, DICTIONARY
D=c.R/'data/national';RAW=c.R/'cache/history/ms/epa-national.tmp.zip'
NAME=re.compile(r'\b(?:data[ -]*cent(?:er|re)s?|server farm)\b',re.I)
def tables(z,n):
    with z.open(n+'.csv') as raw, io.TextIOWrapper(raw,encoding='cp1252',errors='replace',newline='') as f:
        yield from csv.DictReader((s.replace(chr(0),'') for s in f))
def extract():
    sha=digest(RAW);pin=c.read(c.R/'cache/history/ms/epa-source.json',{})['sha256']
    if sha!=pin:raise ValueError('EPA source package hash changed')
    with zipfile.ZipFile(RAW) as z:
        fs=collections.defaultdict(list)
        for r in tables(z,'ICIS_FACILITIES'):
            if NAME.search(r['FACILITY_NAME']):fs[r['NPDES_ID']].append(r)
        # Admit only facility name matches. A permittee alone is not sufficient.
        pp=[p for p in tables(z,'ICIS_PERMITS') if p['AGENCY_TYPE_CODE']=='ST6' and p['EXTERNAL_PERMIT_NMBR'] in fs]
        rows=[dict(facilities=fs[p['EXTERNAL_PERMIT_NMBR']],permit=p) for p in pp]
        c.dump(c.R/'cache/national/water-state-candidates.json',dict(source=URL,sha256=sha,rows=rows))
        print(len(fs),'explicitly named facility IDs;',len(pp),'state-agency versions')
SUPPORT=re.compile(r'offsite|off.site|substation|laydown|deferred roadway|pipeline|\btug lines\b|portable batch|redi.mix|transmission line|transmission connect|road improvements?| data center connect\b|access (?:rd|road)|concrete|batch plant',re.I)
DS='State-issued water permits reported to EPA'
def publish():
    source=c.read(c.R/'cache/national/water-state-candidates.json',{});rows=source['rows']
    with (D/'jurisdictions.csv').open() as f:co={g['state']+g['geoid'][2:]:g['name'] for g in csv.DictReader(f) if g['layer']=='counties'}
    # Source-specific collectors take precedence. Do not publish a second event series
    # for an instrument represented by a local or state primary source.
    names={r['state']:r['name'] for r in csv.DictReader((D/'priority.csv').open())};known=set()
    with (c.R/'data/history/series.csv').open() as f:
        for s in csv.DictReader(f):
            if s['series'].startswith(('wtr_','fed_','edate_')):continue
            for r in c.read(series_path(s['series']),[]):
                for v in re.findall(r'\b[A-Z]{2}[A-Z0-9]{7}\b',str(r.get('record_no') or '').upper()):
                    known.add((s['state'],v))
    out=collections.defaultdict(list);held=[];states=collections.Counter()
    for item in rows:
        p=item['permit'];fac=item['facilities'];f=fac[0];st=f['STATE_CODE'];num=p['EXTERNAL_PERMIT_NMBR'];ver=p['VERSION_NMBR'];states[st]+=1
        county=co.get(f['COUNTY_CODE']);why=None
        if p['AGENCY_TYPE_CODE']!='ST6':raise ValueError('Non-state issuer')
        if (st,num) in known:why='Already in a primary register'
        elif SUPPORT.search(f['FACILITY_NAME']):why='Supporting infrastructure or supplier; site identity needs separate evidence'
        elif {tuple(x[k] for k in ('STATE_CODE','COUNTY_CODE','FACILITY_NAME')) for x in fac}!={(st,f['COUNTY_CODE'],f['FACILITY_NAME'])} or not num.startswith(st):why='Conflicting facility identity or state'
        elif not p['ISSUE_DATE'] and not p['EFFECTIVE_DATE']:why='Neither issuance nor effectiveness dated'
        if why:held.append([st,num,ver,why]);continue
        date=iso(p['ISSUE_DATE'] or p['EFFECTIVE_DATE'])
        if date>'2026-11-15':held.append([st,num,ver,'After cutoff']);continue
        typ={'GPC':'NPDES general permit coverage','NPD':'Individual NPDES discharge permit'}[p['PERMIT_TYPE_CODE']]
        status={'EFF':'Effective','TRM':'Terminated','ADC':'Administratively continued','EXP':'Expired'}[p['PERMIT_STATUS_CODE']]
        det=dict(location_precision='County provided by agency' if county else 'State only; county not established',agency_type='ST6',reported_issuer=p['ISSUING_AGENCY'],facility_name=f['FACILITY_NAME'],reported_city=f['CITY'],master_permit=p['MASTER_EXTERNAL_PERMIT_NMBR'],version=ver,status_code=p['PERMIT_STATUS_CODE'],dictionary=DICTIONARY,program='NPDES',facility_id=f['FACILITY_UIN'],**{k.lower():iso(p[k]) for k in ('ISSUE_DATE','EFFECTIVE_DATE','EXPIRATION_DATE','TERMINATION_DATE','RETIREMENT_DATE')})
        out[st].append(dict(state=st,id='wtr-'+num+'-'+p['ACTIVITY_ID']+'-'+ver,dataset=DS,record_no=num,jurisdiction=county or names[st],county=county or '',project=f['FACILITY_NAME'],kind=typ,status=status,date=date,date_role='Issue date' if p['ISSUE_DATE'] else 'Effective date',url='https://echo.epa.gov/effluent-charts#/'+num,source_url=URL,source_sha256=source['sha256'],locator='ICIS_PERMITS.csv '+num+' activity '+p['ACTIVITY_ID']+' version '+ver,details=det))
    for s in csv.DictReader((c.R/'data/history/series.csv').open()):
        if s['series'].startswith('wtr_') and s['state'] not in out:raise ValueError('Remove obsolete empty state supplement from the register before releasing: '+s['series'])
    for st,rr in out.items():c.dump(series_path('wtr_'+st.lower()),rr)
    c.dump(D/'water_holds.json',held);c.dump(D/'water_totals.json',{'source':URL,'sha256':source['sha256'],'candidate_versions':dict(states),'admitted':{s:len(r) for s,r in out.items()},'states_with_no_candidates':[r['state'] for r in csv.DictReader((D/'priority.csv').open()) if not states[r['state']]],'held':len(held)})
    print(sum(map(len,out.values())),'published;',len(held),'held;',len(out),'states.')
def classify(r,cutoff,perm,no,app,obs,*,federal=False):
    from lib.status import details,iso as dt
    d=details(r);ver=int(d['version']);reg=r['state']+(':epa-direct-npdes' if federal else ':state-npdes');t=dt(d.get('termination_date'));exp=dt(d.get('expiration_date'));eff=dt(d.get('effective_date'));ret=dt(d.get('retirement_date'))
    if d.get('agency_type')!=('EP6' if federal else 'ST6') or (federal and d.get('reported_issuer')!='U.S. EPA'):return no('Issuing agency does not match the permit series.','unknown')
    if (t and t<=cutoff) or (ret and ret<=cutoff):return perm(reg,'historical','Agency gives an end date for this version.',t if t and t<=cutoff else ret,version=ver)
    if r['status']=='Expired' and exp and exp<=cutoff:return perm(reg,'historical','Agency lists this permit as expired.',exp,version=ver)
    if r['status']=='Effective' and eff and eff<=cutoff and exp and cutoff<=exp:return perm(reg,'active','Reported effective during its dated permit term.',eff,version=ver)
    if r['status']=='Administratively continued' and eff and eff<=cutoff:return perm(reg,'unconfirmed','Continuation reported without a dated end or confirmation at the reporting cutoff.',eff,version=ver)
    return perm(reg,'unconfirmed','Issued or effective date reported; current validity is not established.',dt(r['date']),version=ver)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--extract',action='store_true');a=ap.parse_args()
    if a.extract:extract()
    publish()
