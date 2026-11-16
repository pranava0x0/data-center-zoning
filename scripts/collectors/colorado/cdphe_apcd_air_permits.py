"""Colorado Department of Public Health and Environment, Air Pollution Control Division: air permit application tracker
(apcdweb PermitStatus register, statewide). Rows keep only data-center-linked applications and issuances."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.records import rec
from lib.files import pack, unpack
from lib.terms import EX
from lib.net import get_simple as get
from lib.paths import CACHE
from urllib.parse import quote
import re, json
D=CACHE/'co';AP='https://apcdweb.dphe.state.co.us/PermitStatus/';API='https://apcdweb.dphe.state.co.us/PermitStatusAPI/api/vResultsAPIs'
def download():
    D.mkdir(exist_ok=True,parents=True);(D/'air.html').write_bytes(get(AP))
    js=json.loads(get(API));pack(D/'air.json.gz',dict(url=API,total=len(js),rows=js))
def rows(cent):
    p=D/'air.json.gz';a=unpack(p);rows=[];sites=set()
    confirmed=any(x['attributes']['City']=='CENTENNIAL' and x['attributes']['FULLADDR'].startswith('12500 E ARAPAHOE RD') for x in cent['rows'])
    for r in a['rows']:
        n=(r.get('permit') or '').strip();fac=r.get('facility') or '';e=' '.join(str(r.get(k) or '') for k in ('company','facility','source'))
        if not EX.search(e) and n!='25DG0038':continue
        m=re.search(r', ([A-Z ]+), COLORADO,',fac)
        if not m:raise ValueError('County ambiguous '+fac)
        co=m[1].title()+' County';place=co
        if co=='Denver County':place='Denver'
        elif n=='26AR0258' and confirmed:place='Centennial'
        elif 'QTS AURORA' in fac:place='Aurora'
        elif 'QTS COLORADO SPRINGS' in fac:place='Colorado Springs'
        scope='State air application includes explicit data-center identifier.' if n!='25DG0038' else 'Same permit number and campus confirmed by state draft notice; state reports separate building addresses.'
        if fac.startswith('IRON MOUNTAIN DATA CENTERS') and '4300 BRIGHTON BOULEVARD' in fac:sites.add(n)
        u=AP+'?permit='+quote(n);dt=(r.get('Received') or '')[:10];iss=(r.get('permitIssuedOn') or '')[:10];svc=(r.get('serviceType') or '').strip();pid=str(r['PER_ID'])
        for mode,when in [('application',dt),('issue',iss)]:
            if not when:continue
            rows.append(rec('CO','air-'+pid+'-'+mode,'Colorado APCD air permit application tracker',n,'Air permit application' if mode=='application' else 'Air permit issuance','Received: '+svc if mode=='application' else 'Permit issued on',when,'application received' if mode=='application' else 'permit issue date',u,'PER_ID '+pid+' / '+mode,fac,place,co,p,issuer='Colorado Department of Public Health and Environment / APCD',register_url=API,service_type=svc,source_received=dt,source_issue_date=iss or None,identity_basis=scope,location_proof=cent['url'] if place=='Centennial' else None))
    if not sites:raise ValueError('Missing official evidence for Denver facility/address join')
    return rows,sites,a['total']
