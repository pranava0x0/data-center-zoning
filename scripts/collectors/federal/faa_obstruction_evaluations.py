"""Read the FAA's public off-airport Part 77 region/year downloads. No account required.
One completed airspace study per ASN. Study points and temporary cranes are not permits or sites.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, collections, csv, io, re
import lib.discovery as c
from lib.url_archive import Archive
from pipeline.national_gate import run as gate
D=c.R/'data/national';P='https://oeaaa.faa.gov/oeaaa/'
YEARS=P+'oe3a/external/portal-api/getReportYearsPerRegion.do'
BASE=P+'oe3a-external-api/downloadArchives.do?fname='
LETTER='https://efiling.energy.ca.gov/GetDocument.aspx?DocumentContentId=63885&tn=232020'
REG='FAA airspace determinations';CUTOFF='2026-11-15'
TERM=re.compile(r'\b(?:data[ -]?cent(?:er|re)s?|server farms?)\b',re.I)
INDIRECT=re.compile(r'(?:adjacent to|near(?:by)?|across from|next to|south of|north of|east of|west of|formerly|not (?:a|for a)) (?:the |an? |proposed |existing |new )*(?:data[ -]?cent(?:er|re)|server farm)',re.I)
def catalog(a):
 return [(r,y,BASE+f'Part77{r}{y}List.gzip') for r,ys in a.json(YEARS)['part77'].items() for y in ys if re.fullmatch('[A-Z]{3}',r)]
def download(start,stop):
 gate(True);a=Archive('federal_aviation',True,owner='federal/faa_obstruction_evaluations');errors={};jobs=[q for q in catalog(a) if start<=q[1]<=stop];jobs.sort(key=lambda q:(-q[1],q[0]))
 for k,(r,y,u) in enumerate(jobs):
    try:a.get(u)
    except Exception as e:errors[u]=str(e)[:240]
    if (k+1)%15==0:print(k+1,'/',len(jobs),'archived or attempted',flush=True)
 c.dump(D/'federal_aviation_fetch_errors.json',errors);print('Fetch failures:',len(errors))
def records(b):
 # FAA escapes quoted frequency JSON using backslashes. The final lines are a generation timestamp,
 # not ASN rows. Read CSV without splitting the individual quoted text fields on commas.
 s=b.decode('utf-8-sig',errors='replace').replace('\\r\\n',' ').replace('\\n',' ')
 rr=csv.reader(io.StringIO(s,newline=''),escapechar='\\');cols=[v.strip() for v in next(rr)]
 for cells in rr:
    if cells and re.fullmatch(r'\d{4}-[A-Z]{3}-\d+-(?:OE|NRA)',cells[0]):
        if len(cells)!=len(cols):yield None
        else:yield dict(zip(cols,cells))
def publish():
 a=Archive('federal_aviation',owner='federal/faa_obstruction_evaluations');geo=list(csv.DictReader((D/'jurisdictions.csv').open()));states={r['state']:r['geoid'] for r in geo if r['layer']=='state'};counties={r['geoid']:r['name'] for r in geo if r['layer']=='counties'}
 signed,letterhash=a.get(LETTER);txt=c.norm(c.parse(signed,'application/pdf',LETTER)[1]);assert '2019-awp-15211-oe' in txt and 'no hazard' in txt and 'building data center' in txt
 out={};audit=[];holds=[];checks=collections.Counter()
 for region,year,u in sorted(catalog(a)):
    if u not in a.sources:continue
    b,h=a.get(u);co=collections.Counter()
    if not b.startswith(b'STUDY (ASN)'):
        audit.append(dict(region=region,year=year,url=u,sha256=h,error='Empty or unrecognized archive, no cases examined'));continue
    for q in records(b):
        co['case_rows']+=1
        if q is None:co['malformed_rows']+=1;continue
        asn=q['STUDY (ASN)'];st=q['STRUCTURE STATE'];nm=q['STRUCTURE NAME'].strip();desc=' '.join(q['PROPOSAL DESCRIPTION'].split());term=TERM.search(nm+' '+desc)
        if not term:continue
        co['literal_matches']+=1
        det=q['DETERMINATION'];day=q['COMPLETION DATE'];why=''
        if INDIRECT.search(nm+' '+desc):why='Nearby or indirect reference; manual site check required'
        elif q['STRUCTURE TYPE'] in ('BUILDING$SCHOOL','BUILDING$WINDMILL','ELECTRICAL_SYSTEM$SOLAR_PANEL','POWER_PLANT'):why='Different named structure use; supporting or separate site requires review'
        elif not asn.endswith('-OE') or st not in states:why='Not a US off-airport case in the geographic directory'
        elif not day or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day) or day>CUTOFF:why='No completed action dated within this edition'
        elif det not in ('No Hazard','Does Not Exceed','Extension','Hazard') or not (q['STATUS'].startswith('Determined') or q['STATUS'] in ('Extended','Terminated')):why='Outcome or case status requires manual review'
        if why:
            co['held']+=1;holds.append(dict(asn=asn,state=st,reason=why,source_url=u));continue
        gid=states[st]+q['STRUCTURE COUNTY ID'].zfill(3);county=counties.get(gid,'') if q['STRUCTURE COUNTY ID'].isdigit() else ''
        # Verify that county name and state-specific number agree. Treat city as reported, never legal jurisdiction.
        if county and q['STRUCTURE COUNTY NAME'] and c.norm(q['STRUCTURE COUNTY NAME']) not in c.norm(county):county=''
        signed_case=asn=='2019-AWP-15211-OE'
        if signed_case and (st,day,det)!=('CA','2020-02-03','No Hazard'):raise ValueError('FAA register and signed letter disagree')
        scope='The FAA evaluated this structure or construction equipment for air navigation. Several study numbers can cover the same building. This is not a zoning, building or operating permit.'
        row=dict(id='fed-faa-'+asn.lower(),state=st,dataset=REG,jurisdiction=county or st,county=county,record_no=asn,project=nm or 'Data center airspace study',kind='Airspace review of '+('construction equipment' if q['STRUCTURE TYPE'].split('$')[0] in ('CRANE','RIG','CONSTRUCTION') else 'proposed structure'),status=det,date=day,date_role='FAA study completion date',url=LETTER if signed_case else u,source_url=u,source_sha256=h,locator=f'{region} {year} off-airport CSV · STUDY (ASN) {asn}',details=dict(federal_issuer='Federal Aviation Administration',scope=scope,structure_city_as_reported=q['STRUCTURE CITY'],original_structure_type=q['STRUCTURE TYPE'],prior_study=q['PRIOR ASN'],reported_case_status=q['STATUS'],source_description=desc[:420],original_determination=det))
        if signed_case:row['details'].update(signed_letter=LETTER,signed_letter_sha256=letterhash)
        if asn in out and out[asn]!=row:raise ValueError('Conflicting published FAA case '+asn)
        out[asn]=row;co['included']+=1
    checks.update(co);audit.append(dict(region=region,year=year,url=u,sha256=h,**co))
 grouped=collections.defaultdict(list)
 for x in sorted(out.values(),key=lambda q:q['id']):grouped[x['state']].append(x)
 for st,v in grouped.items():c.dump(series_path('faa_'+st.lower()),v)
 c.dump(D/'federal_aviation_search.json',dict(agency='FAA',public_catalog=YEARS,as_of=CUTOFF,summary=checks,by_state={k:len(v) for k,v in sorted(grouped.items())},files=audit,held=holds,limits='Named structure or proposal only. Includes dated off-airport determinations on temporary equipment. Distinct study numbers are not counts of campus projects or permits. Several filings for one site are common.'))
 print(len(audit),'files;',checks, len(grouped),'states')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--from-year',type=int,default=2016);p.add_argument('--through-year',type=int,default=2026);x=p.parse_args()
 if x.fetch:download(x.from_year,x.through_year)
 publish()
