"""EPA ICIS-NPDES permit versions (state slice, Tennessee) joined to ICIS facilities, plus EPA ECHO name-match leads and the
Memphis water-recycling document used as alias evidence. Issuers: U.S. EPA (ICIS-NPDES / ECHO), Tennessee permit-issuing agencies."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import collections, csv, hashlib
from urllib.parse import urlencode
from collectors.tennessee.evidence_store import RX, D, R, j, get, read, collect, M, fetch_documents
DOCS=('memphis_water',)
def download(c,m):fetch_documents(c,m,DOCS);epafetch(m)
def epafetch(m):
    d=m.setdefault('echo',{})
    for key in ['DATA CENTER','DATACENTER','DATA CENTRE','WOOLHAWK','FOXMAN','COLOSSUS','OPPIDAN','PROJECT RAINIER']:
        if key not in d:
            u='https://echodata.epa.gov/echo/cwa_rest_services.get_facility_info?'+urlencode({'output':'JSON','p_st':'TN','p_fn':key})
            r=get(u);rr=read(r)['Results']
            if int(rr['QueryRows'])!=len(rr.get('Facilities') or []):raise ValueError('Truncated ECHO name match')
            d[key]=r;collect.dump(M,m)
def rows(c,m,add):
    from lib import epa_icis as ep
    countyref={v['geoid']:v['name'] for v in csv.DictReader((R/'data/jurisdictions.csv').open()) if v['state']=='TN' and v['layer']=='counties'}
    for n,h in c['epa_slices'].items():
        if hashlib.sha256((D/n).read_bytes()).hexdigest()!=h:raise ValueError('EPA state slice changed '+n)
    fs=list(ep.load('TN','FACILITIES'));ps=list(ep.load('TN','PERMITS'))
    em=j(D/'epa-source.json')
    for k,li in [('ICIS_FACILITIES.csv',fs),('ICIS_PERMITS.csv',ps)]:
        if em['members'][k]['state_rows']['TN']!=len(li):raise ValueError('State slice row mismatch')
    reg=collections.defaultdict(list)
    for z in fs:reg[z['NPDES_ID']].append(z)
    eref={'url':em['url'],'sha256':em['sha256']};echo={}
    for r in m.get('echo',{}).values():
        for f in read(r)['Results'].get('Facilities') or []:echo[f['SourceID']]=f
    # Additional files limited to named operator/site infrastructure with corroboration, not all jobs by a contractor.
    water=m['docs'].get('memphis_water');frank_url='https://franklintn.legistar.com/LegislationDetail.aspx?ID=3824&GUID=A67DD281-837E-447D-8813-9EB1F9075771'
    alias={'TNR241376':('Eddy Lane named site plan + same address/permit applicant',frank_url),'TNR155771':('CTC Property LLC and named Colossus facility',m['docs']['internet_archive']['url'])}
    if water:
        for n in ['TNR155776','TNR155891']:alias[n]=('Named Colossus water-recycling works; shared service infrastructure, not a data hall',water['url'])
    def location(f):
        ccode=f['COUNTY_CODE'];return countyref.get('47'+ccode[2:]) if ccode.startswith('TN') else None
    for p in ps:
        n=p['EXTERNAL_PERMIT_NMBR'];fac=reg[n]
        if not fac or p['PERMIT_TYPE_CODE']=='UFT' or not p['ISSUE_DATE']:continue
        names=' / '.join([f['FACILITY_NAME'] for f in fac]+[p['PERMIT_NAME'] or ''])
        if not(RX.search(names) or n in alias):continue
        if len({(f['CITY'],f['COUNTY_CODE'],f['STATE_CODE']) for f in fac})!=1:raise ValueError('Conflicting facility identity '+n)
        f=fac[0];co=location(f);rep=f['CITY'].title();d=dict(issuer=p['ISSUING_AGENCY'],source_locality=rep,address=f['LOCATION_ADDRESS'],permit_name=p['PERMIT_NAME'],activity_id=p['ACTIVITY_ID'],version=p['VERSION_NMBR'],master_permit=p['MASTER_EXTERNAL_PERMIT_NMBR'],raw_status_code=p['PERMIT_STATUS_CODE'],effective_date=ep.iso(p['EFFECTIVE_DATE']),expiration_date=ep.iso(p['EXPIRATION_DATE']),termination_date=ep.iso(p['TERMINATION_DATE']),retirement_date=ep.iso(p['RETIREMENT_DATE']),dictionary=ep.DICTIONARY)
        if co:d['county']=co
        if n in alias:d['identity_basis'],d['identity_source']=alias[n]
        else:d['identity_basis']='Explicit data center in ICIS facility or permit name'
        day=ep.iso(p['ISSUE_DATE']);add('icis-'+n+'-'+p['ACTIVITY_ID']+'-'+p['VERSION_NMBR'],'EPA ICIS-NPDES permit versions',co or 'Tennessee',n,f['FACILITY_NAME'],'NPDES permit coverage' if p['PERMIT_TYPE_CODE']=='GPC' else 'NPDES discharge permit',p['PERMIT_STATUS_CODE'] or 'Not reported',day,'EPA issue date','https://echo.epa.gov/detailed-facility-report?fid='+n,'ICIS_PERMITS: '+n+', activity '+p['ACTIVITY_ID']+', version '+p['VERSION_NMBR'],eref,d)
    return echo,len(fs),len(ps)
