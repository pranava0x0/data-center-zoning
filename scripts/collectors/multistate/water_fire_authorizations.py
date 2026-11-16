"""Named-site water/fire authorizations. Offline derived output; bounded explicit --refresh acquisition."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.arcgis as arcgis
import lib.net as netfetch
import argparse, csv, json, re, time
from collections import defaultdict,Counter
from datetime import date,datetime,timezone
from urllib.parse import urlencode,quote
from urllib.request import urlopen,Request
from zoneinfo import ZoneInfo
import lib.discovery as c, collectors.virginia.loudoun_county.monthly_reports as loud
R=c.R;D=R/'data/national';OUT=R/'output';CACHE=R/'cache/history/water-fire';INDEX=CACHE/'source_index.json'
FMO='Loudoun fire marshal — data-center property authorizations';TY='US site-specific water permit records'
LDC=c.read(collector_data('virginia/loudoun_county/monthly_reports','config.json'),{});LS=LDC['structures'];LP=LDC['issued'];HIST=series_path('loudoun'); TZ=ZoneInfo('America/New_York')
FF='ID,PermitGUID,PermitNumber,PermitType,PermitStatus,PermitWorkClass,ISSUEDATE,FINALIZEDATE,EXPIREDATE,DESCRIPTION,ParcelPIN,MAIN,ADDRESSLINE1,ADDRESSLINE2,ADDRESSLINE3,STREETTYPE,POSTDIRECTION,PREDIRECTION,UNITORSUITE,DataSnapshot'
FU=re.compile(r'\bfuel(?:s|ing)?\b|\bdiesel\b|flammable|combustible liquid|aboveground|above ground|underground tank|(?:storage|day) tank|generator|\bast\b|\bust\b',re.I)
DC=re.compile(r'\b(?:data\s*cent(?:er|re)|datacenter|server\s*(?:room|farm)|data\s*hall)\b',re.I)
def slug(v):return re.sub(r'[^A-Z0-9]+',' ',str(v or '').strip().upper()).strip()
def civil(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).astimezone(TZ).date().isoformat() if ms else None
def geo(base,**kw):return base+'/query?'+urlencode(dict(f='json',**kw))
def take(store,key,url,fmt='json'):
    if url.startswith('https://cbgcd.com/'):
        # The district requires a modern TLS implementation. macOS system curl verifies certificates.
        b=netfetch.get(url,transport='curl',timeout=30,limit=c.LIMIT);mime='application/pdf' if fmt=='pdf' else 'text/html'
    else:
        resp=netfetch.request(url,timeout=30,limit=c.LIMIT);b=resp.body;mime=resp.mime
    if len(b)>c.LIMIT:raise ValueError('size limit exceeded')
    if fmt=='json':
        js=json.loads(b)
        if isinstance(js,dict) and js.get('error'):raise ValueError(js['error'])
    h=c.digest(b);(CACHE/'objects').mkdir(parents=True,exist_ok=True);(CACHE/'objects'/(h+'.'+fmt)).write_bytes(b)
    store[key]=dict(url=url,sha256=h,bytes=len(b),format=fmt,captured=c.now())
    if fmt!='json':
        kind,s,_=c.parse(b,mime,url);(CACHE/'objects'/(h+'.txt')).write_text(s);store[key].update(adapter=kind,text_sha256=c.digest(s.encode()))
    return js if fmt=='json' else s
def load(ix,k):
    d=ix[k];h=d['sha256'];b=(CACHE/'objects'/(h+'.'+d['format'])).read_bytes();assert c.digest(b)==h
    if d['format']=='json':return json.loads(b)
    tb=(CACHE/'objects'/(h+'.txt')).read_bytes();assert c.digest(tb)==d['text_sha256'];return tb.decode()
def props():
    ref=c.read(collector_data('virginia/loudoun_county/monthly_reports','manifest.json'),{})['structures']
    a=loud.attrs(ref);assert len({r['OBJECTID'] for r in a})==len(a)
    return a
def fetch_loud(ix):
    structures=props();pins=sorted({a['LU_MCPI'] for a in structures if a['LU_MCPI']})
    for k in list(ix):
        if k.startswith('loud-'):del ix[k]
    for i in range(0,len(pins),30):
        keys=pins[i:i+30];assert all(re.fullmatch(r'\d+',p) for p in keys)
        w="(PermitType LIKE 'FMO - %' OR PermitType = 'Fire Protection (Commercial)') AND ParcelPIN IN ("+','.join("'"+p+"'" for p in keys)+")"
        off=[0]
        def g(u,**q):
            if 'returnIdsOnly' in q:key=f'loud-ids-{i}'
            else:key=f'loud-rows-{i}-{off[0]}';off[0]+=120
            return take(ix,key,geo(u[:-len('/query')],**q))
        ids=arcgis.pull(g,lambda j:j,LP,w,FF,'ID',120,id_params={'returnGeometry':'false'})['ids']['objectIds'] or []
        print('Loudoun checked parcel batch:',i,len(ids),flush=True)
def build_loud(ix):
    s=props();properties=defaultdict(list)
    for a in s:
        if a['LU_USE']=='COM_DATA_CENTER' and a['LU_ADDRESS'] and a['LU_MCPI']:properties[(a['LU_MCPI'],slug(a['LU_ADDRESS']))].append(a)
    previous={r['record_no'] for r in c.read(HIST,[]) if r.get('dataset')=='Loudoun issued permits'}
    ids={i for k in ix if k.startswith('loud-ids-') for i in load(ix,k)['objectIds'] or []};raw={}
    for k in ix:
        if not k.startswith('loud-rows-'):continue
        for r in load(ix,k)['features']:
            a=r['attributes'];oid=a['ID'];assert oid not in raw;raw[oid]=(a,ix[k])
    assert set(raw)==ids;selected={};counts=Counter()
    for oid,(a,src) in sorted(raw.items()):
        desc=a['DESCRIPTION'] or '';num=a['PermitNumber'];fld=a['PermitType'];cls=a['PermitWorkClass'] or '';dt=civil(a['ISSUEDATE']);counts['parcel_join_rows']+=1
        if not num or not dt:counts['missing_instrument_or_issue_date']+=1;continue
        if not (fld.startswith('FMO') and (cls=='Hazardous Material' or FU.search(desc+' '+cls)) or fld=='Fire Protection (Commercial)' and FU.search(desc) and re.search(r'(?:fuel|diesel|flammable liquid|combustible liquid|aboveground|above ground|storage tank|day tank)',desc,re.I)):counts['not_specific_fuel_or_hazard_scope']+=1;continue
        addr=slug(' '.join(str(a.get(t) or '') for t in ('ADDRESSLINE1','PREDIRECTION','ADDRESSLINE2','STREETTYPE','POSTDIRECTION','ADDRESSLINE3')));match=properties.get((a['ParcelPIN'],addr),[])
        match=[p for p in match if civil(p['LU_BP_ISSUE_DATE']) and civil(p['LU_BP_ISSUE_DATE'])<=dt]
        if not match and not DC.search(desc):counts['no_independent_use_and_address_agreement']+=1;continue
        if num in previous:counts['already_in_loudoun_issued_feed']+=1;continue
        if num in selected:counts['additional_geometry_for_number']+=1;continue
        link=geo(LP,where="PermitNumber = '"+num.replace("'","''")+"'",outFields='PermitNumber,PermitType,PermitWorkClass,PermitStatus,ISSUEDATE,FINALIZEDATE,EXPIREDATE,DESCRIPTION,ID',returnGeometry='false')
        m=sorted(match,key=lambda p:p['OBJECTID'])
        dtls=dict(authority='Loudoun County, Virginia',issuer_level='county',authority_level='county',county='Loudoun County',permit_type=fld,work_class=cls,fuel_explicit=bool(re.search(r'fuel|diesel|flammable liquid|combustible liquid|storage tank',desc,re.I)),prior_permits_explicit=[p for p in re.findall(r'FMOMH-\d{4}-\d+',desc.upper()) if p!=num],facility_match='Explicit data-center text in permit' if DC.search(desc) else 'Exact parcel and complete street address of county-coded data-center structure; permit issued on/after recorded building-permit date',facility_source_url=LS,source_sha256=src['sha256'],issue_date=dt,final_date=civil(a['FINALIZEDATE']),expiration_date=civil(a['EXPIREDATE']),data_snapshot=civil(a['DataSnapshot']),county_structure_ids=[p['OBJECTID'] for p in m])
        selected[num]=dict(id='waterfire-va-'+c.digest(num.encode())[:16],dataset=FMO,state='VA',jurisdiction='Loudoun County',record_no=num,project='Data-center property — '+fld+' / '+cls,kind=fld+' / '+cls,status=a['PermitStatus'],date=dt,date_role='county permit issue date',url=link,source_url=LP,source_sha256=src['sha256'],locator=f'LandMARC issued-permit register: {num}; object {oid}; county structure register in details',details=dtls)
    counts['published_permit_numbers']=len(selected);c.dump(series_path('waterfire_va'),sorted(selected.values(),key=lambda r:(r['date'],r['record_no'])));return dict(counts)
def main():
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--only',choices=['loudoun','documents','phoenix','sanfrancisco']);a=p.parse_args();CACHE.mkdir(exist_ok=True,parents=True);ix=c.read(INDEX,{})
    if a.refresh:
        if a.only in (None,'documents'):
            for z in csv.DictReader((D/'water_fire_sources.tsv').open(),delimiter='\t'):
                try:take(ix,z['key'],z['url'],z['format'])
                except Exception as e:
                    if not ix.get(z['key'],{}).get('sha256'):ix[z['key']]=dict(url=z['url'],error=str(e))
                c.dump(INDEX,ix)
        if a.only in (None,'loudoun'):fetch_loud(ix);c.dump(INDEX,ix)
        if a.only in (None,'phoenix'):fetch_phx(ix);c.dump(INDEX,ix)
        if a.only in (None,'sanfrancisco'):fetch_sf(ix);c.dump(INDEX,ix)
    if any(k.startswith('loud-rows-') for k in ix):print(build_loud(ix))
    if 'phx-ids' in ix:print(build_phx(ix))
    if 'sf-fire' in ix:print(build_sf(ix))
    build_cases(ix)

PHX='Phoenix Fire Department — data-center project and address match'
AZBASE=c.read(collector_data('arizona','config.json'),{})['phoenix_permit'];AZREG=series_path('az')
def azseeds():
    rs=[r for r in c.read(AZREG,[]) if r['dataset']=='Phoenix permits'];site=defaultdict(list)
    for r in rs:
        d=r['details'];p=d.get('project_number');a=slug(d.get('address'));context=' '.join((str(d.get('matched_text','')),str(d.get('source_scope','')),r['project']))
        if p and a and DC.search(context):site[(p,a)].append(r['id'])
    return site,{r['record_no'] for r in rs}
def fetch_phx(ix):
    seed,_=azseeds();ps=sorted({p for p,a in seed});assert all(re.fullmatch(r'(?:[0-9]+|AFP I)-[0-9]+',p) for p in ps);base=AZBASE['url']
    w="PROJECT IN ("+','.join("'"+p+"'" for p in ps)+") AND (UPPER(PER_TYPE_DESC) LIKE '%TANK%' OR UPPER(PER_TYPE_DESC) LIKE '%FLAMM%' OR UPPER(PER_TYPE_DESC) LIKE '%HAZARDOUS MATERIAL%')"
    for k in list(ix):
        if k.startswith('phx-row-'):del ix[k]
    off=[0]
    def g(u,**q):
        if 'returnIdsOnly' in q:key='phx-ids'
        else:key='phx-row-'+str(off[0]);off[0]+=120
        return take(ix,key,geo(u[:-len('/query')],**q))
    arcgis.pull(g,lambda j:j,base,w,AZBASE['fields'],'OBJECTID',120,id_params={'returnGeometry':'false'})
def build_phx(ix):
    from lib.text import date as azdate
    conflicts=c.read(D/'water_fire_tenant_conflicts.json',{});rows=[];seeds,old=azseeds();ids=sorted(load(ix,'phx-ids').get('objectIds') or []);seen=[];stat=Counter();nums=set()
    for k in ix:
        if not k.startswith('phx-row-'):continue
        for r in load(ix,k)['features']:
            a=r['attributes'];oid=a['OBJECTID'];seen.append(oid);project=a['PROJECT'];street=slug(a['STREET_FULL_NAME']);num=str(a['PER_TYPE'])+' '+str(a['PER_NUM']);dt=azdate(a['PER_ISSUE_DATE'],True)
            if num in old:stat['old']+=1;continue
            if (project,street) not in seeds:stat['project_but_not_same_verified_address']+=1;continue
            if num in conflicts:
                assert all(x in (a['PERMIT_NAME'] or '').upper() for x in conflicts[num]['issuer_name_anchors']);stat['different_named_user_at_shared_site']+=1;continue
            if not dt:stat['no_issue_date']+=1;continue
            if num in nums:raise ValueError('Duplicate Phoenix permit '+num)
            nums.add(num);url=geo(AZBASE['url'],where="PID='"+a['PID'].replace("'","''")+"'",outFields='PID,PROJECT,PER_TYPE,PER_NUM,PER_TYPE_DESC,PERMIT_STAT,PER_ISSUE_DATE,PER_COMPL_DATE,PER_EXPIRE_DATE',returnGeometry='false')
            rows.append(dict(id='waterfire-az-'+c.digest(num.encode())[:16],dataset=PHX,state='AZ',jurisdiction='Phoenix',record_no=num,project=a['PERMIT_NAME'] or 'Phoenix data-center project',kind=a['PER_TYPE_DESC'],status=a['PERMIT_STAT'],date=dt,date_role='city permit issue date',url=url,source_url=AZBASE['url'],source_sha256=ix[k]['sha256'],locator='PID '+a['PID']+', municipal project '+project,details=dict(authority='City of Phoenix',issuer_level='city',authority_level='city',seed_ids=sorted(seeds[(project,street)]),facility_match='Exact municipal project number and normalized street address in original independently data-center-labeled city record(s); neither field alone is accepted. Conflicting named tenants are excluded.',issue_date=dt,expiration_date=azdate(a.get('PER_EXPIRE_DATE'),True),final_date=azdate(a['PER_COMPL_DATE'],True),source_sha256=ix[k]['sha256'],permit_type_code=a['PER_TYPE'])))
    assert sorted(seen)==ids
    c.dump(series_path('waterfire_az'),sorted(rows,key=lambda r:(r['date'],r['record_no'])));return dict(phoenix_rows=len(rows),candidates=len(ids),excluded=dict(stat))

SF='San Francisco Fire Department storage and use permits'
SFR='https://data.sfgov.org/resource/893e-xam6.json'
def fetch_sf(ix):
    fields=['permit_holder','dba_name_associated_with_this_permit_holder'];terms=['DATA CENTER','DIGITAL REALTY','EQUINIX','CORESITE','365 MAIN','DIGITAL 200 PAUL','VANTAGE DATA','TELEHOUSE','QTS REALTY']
    w=' OR '.join("upper("+a+") like '%"+n+"%'" for a in fields for n in terms)
    count=take(ix,'sf-count',SFR+'?'+urlencode({'$where':w,'$select':'count(*) as n'}));n=int(count[0]['n']);assert n<1000
    rs=take(ix,'sf-fire',SFR+'?'+urlencode({'$where':w,'$select':'permit_number,permit_type_description,permit_address,permit_application_date,permit_date_approved,expiration_date,permit_status,permit_holder,dba_name_associated_with_this_permit_holder',' $order'.strip():'permit_number','$limit':1000}));assert len(rs)==n
def build_sf(ix):
    sites={'200 - 202 Paul Ave':'200 Paul Av','365 Main St':'365 Main St'};seeds=defaultdict(list)
    for r in c.read(series_path('ca'),[]):
        if r['dataset']=='San Francisco building permits' and DC.search(r['project']):seeds[r['details'].get('address','')].append(r['id'])
    rs=load(ix,'sf-fire');assert len(rs)==int(load(ix,'sf-count')[0]['n']);selected=[];ns=set()
    for a in rs:
        addr=a.get('permit_address','');site=sites.get(addr);typ=a.get('permit_type_description','');name=a.get('permit_holder','')
        if not typ or not re.search(r'(stationary tank|petroleum gas|battery system)',typ,re.I) or not a.get('permit_date_approved') or (not seeds.get(site) and not DC.search(name)):continue
        num=a['permit_number'];assert num not in ns;ns.add(num);url=SFR+'?'+urlencode({'permit_number':num});dt=a['permit_date_approved'][:10]
        selected.append(dict(id='waterfire-ca-'+num,dataset=SF,state='CA',jurisdiction='San Francisco',record_no=num,project=name+' — '+addr,kind=typ,status=a['permit_status'],date=dt,date_role='fire department permit approval date',url=url,source_url='https://data.sfgov.org/d/893e-xam6',source_sha256=ix['sf-fire']['sha256'],locator='SFFD permit_number '+num,details=dict(authority='San Francisco Fire Department',issuer_level='city',county='San Francisco County',permit_holder=name,source_sha256=ix['sf-fire']['sha256'],city_building_source_ids=sorted(seeds.get(site,[])),identity='Named operator and same locally documented data-center address (approved explicit 200–202 Paul Ave/200 Paul Av correspondence), or permit holder explicitly named data center.',expiration_date=(a.get('expiration_date') or '')[:10] or None)))
    c.dump(series_path('waterfire_ca'),sorted(selected,key=lambda r:(r['date'],r['record_no'])));return dict(SF_candidates=len(rs),SF_approved_storage_records=len(selected))

SC='Santa Clara Fire Marshal permit documents'
WA='Washington Ecology — industrial-user state discharge permits'
def date_us(x):return datetime.strptime(x,'%m/%d/%Y').date().isoformat()
def build_wa(ix):
    from lib.text import TableParser
    out=[];expect={'wa-yahoo':'ST0008106','wa-intuit':'ST0008113','wa-eat02':'ST0501334','wa-malaga':'ST0501377'}
    for key,num in expect.items():
        src=ix[key];doc=load(ix,key);h=src['sha256'];p=TableParser();p.feed((CACHE/'objects'/(h+'.html')).read_text());hit=False
        # Permit status is separate from Facility Status. Enforce named fields, not table position.
        for tab in p.tables:
            heads={}
            for cells in tab:
                vals=[' '.join(''.join(cell['text']).split()) for cell in cells]
                if 'Permit Sub Status' in vals and 'Issue Date' in vals:heads={v:i for i,v in enumerate(vals)};continue
                if not heads or len(vals)!=len(heads):continue
                z={field:vals[i] for field,i in heads.items()}
                if z['Permit Number']!=num or z['Permit Type']!='Industrial (IU) to POTW/PRIVATE SWDP IP' or not DC.search(z['Water Quality Name']):continue
                issue=date_us(z['Issue Date']);version=int(z['Permit Version']);sub=z['Permit Sub Status'];raw=z['Permit Status'];hit=True
                county=re.search(r'County:\s*([A-Za-z ]+)\s+WRIA:',doc).group(1).strip()
                city={'wa-yahoo':'Quincy','wa-intuit':'Quincy','wa-eat02':'East Wenatchee','wa-malaga':'Malaga'}[key]
                assert c.norm('City: '+city) in c.norm(doc)
                out.append(dict(id=f'waterfire-wa-{num.lower()}-v{version}',dataset=WA,state='WA',jurisdiction='Washington',record_no=num,project=z['Water Quality Name'],kind='Industrial pretreatment wastewater discharge permit to publicly or privately owned treatment works',status=raw,date=issue,date_role='state permit-register issue date',url=src['url'],source_sha256=h,source_url=src['url'],locator=f'Permits table; {num}, version {version}',details=dict(issuer_level='state',authority='Washington State Department of Ecology',county=county+' County',locality=city,permit_sub_status=sub,facility_status=z['Facility Status'],permit_version=version,effective_date=date_us(z['Effective Date']),expiration_date=date_us(z['Expiration Date']),source_permit_type=z['Permit Type'])))
        assert hit, ('Expected a verified individual permit table for',key)
    return out

def build_cases(ix):
    out=defaultdict(list)
    for row in c.read(D/'water_fire_cases.json',[]):
        r=dict(row);k=r.pop('source');anchors=r.pop('anchors');event=r.pop('key');src=ix[k]
        if not src.get('sha256'):raise ValueError('Missing required source '+k)
        doc=c.norm(load(ix,k))
        for a in anchors:
            if c.norm(a) not in doc:raise ValueError('Source mismatch: '+k+' / '+a)
        r.update(id='waterfire-'+r['state'].lower()+'-'+event,dataset=SC if r['details'].get('action_type')=='sc_fire' else TY,url=src['url'],source_sha256=src['sha256'],source_url=src['url'])
        r['details']['source_sha256']=src['sha256'];r['details']['source_anchors']=anchors
        out[r['state']].append(r)
    out['WA'].extend(build_wa(ix))
    # Preserve GIS-derived rows if a state (VA, CA, AZ) also adds case-file evidence.
    for state,rows in out.items():
        dest=series_path(f'waterfire_{state.lower()}')
        preserve=[r for r in c.read(dest,[]) if r['dataset'] in [FMO,PHX,SF]]
        c.dump(dest,sorted(preserve+rows,key=lambda r:(r.get('date') or '',r['id'])))
    print('Water events:',{st:len(a) for st,a in out.items()})
    for r in c.read(D/'water_fire_visual_reviews.json',[]):
        assert ix[r['source']]['sha256']==r['sha256'];load(ix,r['source'])

def classify(r,cutoff,perm,no,app,obs):
    from lib.status import iso
    ds=r.get('dataset');s=(r.get('status') or '').casefold();d=r.get('details') or {};day=iso(r.get('date'))
    if ds==FMO:
        fin=iso(d.get('final_date'))
        if fin and fin<=cutoff:return perm('VA:loudoun-building','historical','County records a finalization date for this permit.',fin)
        return obs('VA:loudoun-building',('finaled',),issued=('issued',),when=day)
    if ds==PHX:
        if not day or not r['record_no'].startswith(d.get('permit_type_code','')+' '):return no('Unverified Phoenix permit identity.','unknown')
        fin=iso(d.get('final_date'));exp=iso(d.get('expiration_date'))
        if s=='open' and exp and exp>=cutoff and not fin:return perm('AZ:phoenix-permits','active','Issued and OPEN, within source term and without completion.',day)
        if s=='open':return perm('AZ:phoenix-permits','unconfirmed','OPEN but coverage term or completion does not confirm current effect.',day)
        return obs('AZ:phoenix-permits',('done',),issued=('issued',),when=fin if fin and fin<=cutoff else day)
    if ds==SC:return obs('CA:santa-clara-fire',issued=('permit issued',))
    if ds==SF:return obs('CA:sf-fire-storage',('closed (permit)',),issued=('approved',),when=day)
    if ds==WA:
        eff=iso(d.get('effective_date'));exp=iso(d.get('expiration_date'));version=d.get('permit_version')
        if s=='inactive':return perm('WA:ecology-industrial-user','historical','Ecology explicitly records the industrial-user permit version as inactive.',day,version=version)
        if s=='active' and eff and exp and eff<=cutoff<=exp:return perm('WA:ecology-industrial-user','active','Ecology marks this version Active; the reporting cutoff is within its explicit term. Temporary substatus retained.',day,version=version)
        return perm('WA:ecology-industrial-user','unconfirmed','Register status and term do not establish activity at the cutoff.',day,version=version)
    if ds==TY:
        role=d.get('action_type')
        if role=='application':return app()
        if role=='withdrawn':return no('Applicant withdrew the requested groundwater authorization; no issuance established.','application')
        if role=='srbc_revision':return perm('PA:srbc-consumptive','unconfirmed','Numbered modification of the original SRBC approval; current effectiveness not independently established.',day,stable_no='20240901')
        if role=='related_inactive':return perm('WA:ecology-industrial-user','historical','State register explicitly identifies this numbered related industrial-user permit as inactive; issue date is not in this table.')
        if role=='undated_temp':return no('Agency documents earlier temporary issuance; no uniquely matched number for that event.','unnumbered')
    return None
if __name__=='__main__':main()
