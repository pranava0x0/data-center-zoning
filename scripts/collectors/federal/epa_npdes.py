"""Replay the nationwide EPA-issued NPDES search. --extract reads the original national ZIP.
Existing state project casebooks win over this supplement on identical permit and version.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, collections, csv, json, re, zipfile
import lib.discovery as c
from collectors.federal.epa_named_water_permits import D,RAW,NAME,SUPPORT,tables
from lib.epa_icis import URL, DICTIONARY, digest, iso
from pipeline.national_gate import run as gate
DS='U.S. EPA water discharge permits'
CACHE=c.R/'cache/national/water-federal-candidates.json'
def existing():
    rows=[]
    for s in csv.DictReader((c.R/'data/history/series.csv').open()):
        if s['series'].startswith(('fed_','edate_')):continue
        for r in c.read(series_path(s['series']),[]):
            if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{7}',str(r['record_no'])) and ('echo.epa.gov' in (r.get('source_url') or '') or 'echo.epa.gov' in r['url']):
                rows.append(r)
    return rows
def extract():
    gate(True);sha=digest(RAW)
    if sha!=c.read(c.R/'cache/history/ms/epa-source.json',{})['sha256']:raise ValueError('National ICIS file changed')
    known={r['record_no'] for r in existing()}
    with zipfile.ZipFile(RAW) as z:
        fs=collections.defaultdict(list)
        for r in tables(z,'ICIS_FACILITIES'):
            if NAME.search(r['FACILITY_NAME']) or r['NPDES_ID'] in known:fs[r['NPDES_ID']].append(r)
        counts=collections.Counter();rows=[]
        for p in tables(z,'ICIS_PERMITS'):
            n=p['EXTERNAL_PERMIT_NMBR']
            if n not in fs:continue
            counts[(p['AGENCY_TYPE_CODE'],p['ISSUING_AGENCY'])]+=1
            if p['AGENCY_TYPE_CODE'] not in ('EP6','OF6'):continue
            rows.append(dict(facilities=fs[n],permit=p))
    c.dump(CACHE,dict(sha256=sha,url=URL,rows=rows,issuers=[[a,b,n] for (a,b),n in sorted(counts.items())]))
    print('Candidate versions:',len(rows),[(x[0],x[2]) for x in c.read(CACHE,{})['issuers'] if x[0] in ('OF6','EP6')])
def publish():
    data=c.read(CACHE,{});known=collections.defaultdict(list);links={};out=collections.defaultdict(list);held=[]
    names={r['state']:r for r in csv.DictReader((D/'priority.csv').open())}
    geo={g['geoid']:g for g in csv.DictReader((D/'jurisdictions.csv').open())}
    for r in existing():known[(r['record_no'],str(r.get('details',{}).get('version','')))].append(r)
    for e in data['rows']:
        p=e['permit'];fs=e['facilities'];f=fs[0];n=p['EXTERNAL_PERMIT_NMBR'];v=p['VERSION_NMBR'];st=f['STATE_CODE'];key=n,v
        if p['AGENCY_TYPE_CODE']!='EP6' or p['ISSUING_AGENCY']!='U.S. EPA':
            held.append([n,v,'Issuing agency not confirmed as EPA']);continue
        ctx={'issuer':'U.S. Environmental Protection Agency','program':'NPDES','authority_code':'EP6','npdes_id':n,'version':v,'activity_id':p['ACTIVITY_ID'],'source_url':URL,'source_sha256':data['sha256'],'dictionary':DICTIONARY}
        if key in known:
            for r in known[key]:links[r['id']]=ctx
            continue
        if n=='NMR1004BJ' or SUPPORT.search(f['FACILITY_NAME']):
            held.append([n,v,'Combined solar or other supporting project; site authorization needs independent confirmation']);continue
        if len({(x['FACILITY_NAME'],x['STATE_CODE'],x['COUNTY_CODE']) for x in fs})!=1 or not NAME.search(f['FACILITY_NAME']) or not n.startswith(st):
            held.append([n,v,'Ambiguous site or state']);continue
        if p['PERMIT_TYPE_CODE'] not in ('GPC','NPD') or p['PERMIT_STATUS_CODE'] not in ('EFF','TRM','ADC','EXP') or not (p['ISSUE_DATE'] or p['EFFECTIVE_DATE']):
            held.append([n,v,'No supported dated issuance or coverage']);continue
        date=iso(p['ISSUE_DATE'] or p['EFFECTIVE_DATE'])
        if date>'2026-11-15':held.append([n,v,'Beyond cutoff']);continue
        countycode=f['COUNTY_CODE'];co=geo.get(names[st]['geoid']+countycode[2:],{}).get('name','') if countycode.startswith(st) else ''
        if st=='GU' and co=='Guam':co=''
        typ='Construction stormwater permit coverage' if p['MASTER_EXTERNAL_PERMIT_NMBR'] in {'MAR100000','IDR100000','OKR10I000','GUR100000'} else {'NPD':'Individual NPDES discharge permit','GPC':'NPDES general permit coverage'}[p['PERMIT_TYPE_CODE']]
        loc=national_point(f,st,geo)
        if co and loc['county'] and co!=loc['county']:raise ValueError('County mismatch: '+n)
        co=co or loc['county']
        det=dict(federal_issuer=ctx['issuer'],federal_program='NPDES',agency_type='EP6',reported_issuer=p['ISSUING_AGENCY'],version=v,status_code=p['PERMIT_STATUS_CODE'],master_permit=p['MASTER_EXTERNAL_PERMIT_NMBR'],dictionary=DICTIONARY,location_method=loc['method'],location_sources=loc['sources'],reported_locality=f['CITY'],**{k.lower():iso(p[k]) for k in ('ISSUE_DATE','EFFECTIVE_DATE','EXPIRATION_DATE','TERMINATION_DATE','RETIREMENT_DATE')})
        out[st].append(dict(id='fed-epa-'+n.lower()+'-'+p['ACTIVITY_ID']+'-'+v,state=st,dataset=DS,record_no=n,jurisdiction=loc['locality'] or co or names[st]['name'],county=co,project=f['FACILITY_NAME'],kind=typ,status={'EFF':'Effective','TRM':'Terminated','ADC':'Administratively continued','EXP':'Expired'}[p['PERMIT_STATUS_CODE']],date=date,date_role='Issue date' if p['ISSUE_DATE'] else 'Effective date',url='https://echo.epa.gov/effluent-charts#/'+n,source_url=URL,source_sha256=data['sha256'],locator='ICIS_PERMITS.csv · '+n+' · activity '+p['ACTIVITY_ID']+' · version '+v,details=det))
    for st,rows in out.items():c.dump(series_path('fed_'+st.lower()),rows)
    c.dump(D/'federal_links.json',links)
    c.dump(D/'federal_npdes_summary.json',dict(archive=URL,sha256=data['sha256'],candidate_versions=len(data['rows']),linked_existing=len(links),added={st:len(a) for st,a in out.items()},held=held,scope='Permit number and version matched in the national archive. Federal attribution requires both EP6 and U.S. EPA. Named-site search plus exact IDs independently verified in state casebooks; aliases may be missing.'))
    print('Direct EPA:',len(links),'existing,',sum(map(len,out.values())),'new,',len(held),'held')
def national_point(f,st,geo):
    # Generalized boundaries for screening only. Require an independent agreement with the
    # register address name for municipalities. A statistical place does not issue permits.
    from lib.url_archive import Archive
    from lib.geo import places, contains
    x,y=float(f['GEOCODE_LONGITUDE']),float(f['GEOCODE_LATITUDE'])
    base=c.read(D/'federal_geometry.json',{});result=dict(county='',locality='',method='EPA facility point and Census polygons; municipality requires matching address locality.',sources=[])
    for role,url in base.get(st,{}).items():
        table=list(places(Archive('federal_geo', owner='federal', name='geo_sources.json').get(url)[0]))
        hit=[g for g,(x0,y0,x1,y1),rs in table if x0<x<x1 and y0<y<y1 and contains(x,y,rs) and g['GEOID'] in geo and geo[g['GEOID']]['state']==st]
        if len(hit)!=1:continue
        g=geo[hit[0]['GEOID']];name=g['name']
        if role=='county' and name!='Guam':result['county']=name;result['sources'].append(url)
        elif role=='locality' and g['layer'] in ('place','territory subdivisions') and re.sub(r' (municipality|city|town|village)$','',name,flags=re.I).casefold()==f['CITY'].casefold():result['locality']=name;result['sources'].append(url)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');a=p.parse_args()
    if a.extract:extract()
    publish()
