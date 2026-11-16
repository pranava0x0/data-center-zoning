"""Look beyond literal data center names in the same national ICIS snapshot.
Company names/industry codes are leads; never publish automatically.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_paths
import argparse, collections, csv, re, zipfile
from collectors.federal.epa_named_water_permits import RAW,tables,NAME,D
from lib.epa_icis import URL, digest
import lib.discovery as c
C=c.R/'cache/national/federal-extended-water.json'
OP=re.compile(r'\b(?:amazon(?: web services| data services)?|aws|meta platforms|facebook|google|alphabet|microsoft|vantage data|digital realty|equinix|cologix|cyrus\s?one|aligned data|switch ltd|qts|quality technology services|iron mountain data|stack infrastructure|ntt global|compass datacenters|cloudhq|edgecore|flexential|coresite|databank|prime data|oracle|apple)\b',re.I)
SITE=re.compile(r'\b(?:data[ -]?halls?|computer cent(?:er|re)|server cent(?:er|re)|comput(?:ing|e) (?:facilit(?:y|ies)|campus|cent(?:er|re))|co[ -]?location (?:facilit(?:y|ies)|cent(?:er|re))|hyperscale|server campus)\b',re.I)
def extract():
 from pipeline.national_gate import run;run(True)
 sha=digest(RAW)
 if sha!=c.read(c.R/'cache/history/ms/epa-source.json',{})['sha256']:raise ValueError('ICIS changed')
 ids=set();rows=[];codes=collections.defaultdict(set);counts=collections.Counter()
 with zipfile.ZipFile(RAW) as z:
    for name,field,allowed in [('NPDES_NAICS','NAICS_CODE',{'518210'}),('NPDES_SICS','SIC_CODE',{'7374'})]:
        for r in tables(z,name):
            if r[field] in allowed:codes[r['NPDES_ID']].add(r[field])
    # Join all EPA-issued permit versions, not just facilities named in a search.
    for p in tables(z,'ICIS_PERMITS'):
        if p['AGENCY_TYPE_CODE']=='EP6' and p['ISSUING_AGENCY']=='U.S. EPA':
            counts['epa_direct_versions']+=1;ids.add(p['EXTERNAL_PERMIT_NMBR'])
    ff={}
    for f in tables(z,'ICIS_FACILITIES'):
        n=f['NPDES_ID']
        if n in ids:ff.setdefault(n,[]).append(f)
    for p in tables(z,'ICIS_PERMITS'):
        n=p['EXTERNAL_PERMIT_NMBR']
        if n not in ff or p['AGENCY_TYPE_CODE']!='EP6' or p['ISSUING_AGENCY']!='U.S. EPA':continue
        label=' '.join(x['FACILITY_NAME'] for x in ff[n]);operator=p['PERMIT_NAME'];why=[]
        if NAME.search(label):why.append('Literal facility name')
        if SITE.search(label):why.append('Additional facility term')
        if NAME.search(operator) or SITE.search(operator):why.append('Explicit term in permittee')
        if OP.search(label+' '+operator):why.append('Operator or brand')
        if n in codes:why.append('Agency industry code')
        if why:rows.append(dict(permit=p,facilities=ff[n],why=why,industry_codes=sorted(codes.get(n,()))))
 counts['epa_direct_ids']=len(ids);counts['joined_facilities']=len(ff)
 c.dump(C,dict(archive=URL,sha256=sha,base=counts,rows=rows))
 print(counts,len(rows),'screening leads')
def publish():
 data=c.read(C,{});base=data['base'];rows=[];seen=set()
 linked=c.read(D/'federal_links.json',{});included={(v['npdes_id'],str(v['version'])) for v in linked.values()}
 for path in [q for q in series_paths('fed_') if q.exists()]:
    for r in c.read(path,[]):
        d=r.get('details',{})
        if d.get('agency_type')=='EP6':included.add((r['record_no'],str(d['version'])))
 for item in data['rows']:
    p=item['permit'];fs=item['facilities'];n=p['EXTERNAL_PERMIT_NMBR'];v=p['VERSION_NMBR'];site=' | '.join(sorted({f['FACILITY_NAME'].strip() for f in fs}));why=item['why'];extra=''
    if (n,v) in included:result='Already in published register'
    elif n=='NMR10067D':
        result='Solar facility supplying a data center';extra='https://www.pnm.com/documents/28767612/40780649/Case-No-23-00251-UT.pdf/871bc00d-2805-2796-91e3-06376b6c0326?t=1691612696972'
    elif n=='NMR1004BJ':result='Combined solar and data center name; scope unresolved'
    elif n in ('PRNOE3009','PRNOEJ00U'):result='No-exposure certification; data center site not established'
    elif re.search(r'distribution center|warehouse|delivery station|apartments|residence|single family home|orchard|apple canyon gourmet|plasma center',site,re.I):result='Named use is not a data center'
    elif re.search(r'water system improvement|waterline |water main |water extension|water transmission line|utility extension|ditch association|transmission line upgrades',site,re.I):result='Utility or off-site project, no data center decision identified'
    else:result='Project use unresolved; operator or industry term insufficient'
    if (n,v) in seen:raise ValueError('Duplicate version '+n)
    seen.add((n,v));rows.append(dict(state=fs[0]['STATE_CODE'],permit_id=n,version=v,facility=site,match='; '.join(why),review=result,case_url='https://echo.epa.gov/detailed-facility-report?permitId='+n,independent_source=extra))
 rows.sort(key=lambda r:(r['state'],r['permit_id'],r['version']))
 with (D/'federal_water_leads.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 counts=collections.Counter(r['review'] for r in rows)
 summary=dict(archive=data['archive'],sha256=data['sha256'],**base,ids_without_facility_join=base['epa_direct_ids']-base['joined_facilities'],matched_versions=len(rows),unique_matched_permits=len({r['permit_id'] for r in rows}),review=dict(counts),newly_admitted=0,limits='Only EPA-issued ICIS records; company text, industrial codes and expanded facility terms supplement the earlier keyword and matched-ID search. No permit enters the atlas solely from this queue.')
 c.dump(D/'federal_water_lead_summary.json',summary);print(counts)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');a=p.parse_args()
 if a.extract:extract()
 publish()
