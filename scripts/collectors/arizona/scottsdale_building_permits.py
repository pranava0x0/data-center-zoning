"""City of Scottsdale parcel permit listing, screened to the verified data-center site (parcel and address match
against the Maricopa County air permit facility record). Issuers: City of Scottsdale (permits) and Maricopa County
Air Quality Department (facility lookup)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
def download(save,query,queries):
    sx=conf['scottsdale']; ids=sx['facilities']; air_url=conf['air']['url']+'/query'
    q={'where':"facility_id IN ("+','.join(repr(id_) for id_ in ids)+')','outFields':'facility_id,facility_nm,facility_desc,name,address1,city,county_nm,parcel_no,permit_nbr','returnGeometry':'false','f':'json'}
    lookup=query('scottsdale-county-sites.json.gz',air_url,q)['features']
    sites=[v['attributes'] for v in lookup];assert set(ids)=={v['facility_id'] for v in sites}
    # Do not retain the entire statewide-taxpayer/owner listing. Keep screened rows and hash all downloaded bytes.
    b=lib.net.req(sx['url']);raw=csv.DictReader(io.TextIOWrapper(io.BytesIO(b),encoding='utf-8-sig'));total=0;subset=[]
    norm=lambda st:re.sub(r'[^A-Z0-9]','',st.upper());cols='permit_id PermitNumber PermitType PermitStatus IssueDate Address APN Subdivision Owner ResponsibleParty Builder'.split()
    for a in raw:
        total+=1
        if any(norm(a['APN'])==norm(v['parcel_no']) or norm(v['address1'])[:-2] in norm(a['Address']) for v in sites):
            subset.append({col:a[col] for col in cols})
    slim={'source_url':sx['url'],'source_sha256':lib.files.sha(b),'total_bytes':len(b),'records_scanned':total,'rows':subset}
    save('scottsdale-parcel-screen.json.gz',sx['url'],json.dumps(slim,sort_keys=True,separators=(',',':')).encode())
    queries['scottsdale']=total
def rows(b):
    add=b.add;reject=b.reject;m=b.m;meta=b.meta;archived=b.archived
    n='scottsdale-parcel-screen.json.gz';screen=archived(n);sx=conf['scottsdale']
    site=next(a['attributes'] for a in archived('scottsdale-county-sites.json.gz')['features'] if a['attributes']['facility_id']==sx['promotable_facility'])
    assert screen['records_scanned']==meta['candidate_counts']['scottsdale']
    assert match(site['facility_desc']) and sx['verified_legal_owner_base'] in site['name'].upper()
    for a in screen['rows']:
        no=a['PermitNumber']
        if not (a['Address'].upper()==site['address1'].upper() and a['APN'].upper()==site['parcel_no'].upper() and a['Owner'].upper()==sx['verified_legal_owner_base']):
            reject.append(['scottsdale',no,'At/near a screened parcel only; no sector attribution']);continue
        # City does not publish the narrative here. Classify site-associated work, not a new data hall.
        dt=datetime.strptime(a['IssueDate'][:10],'%Y/%m/%d').date().isoformat()
        add('Scottsdale permits at a verified data-center site',n,no,site['facility_nm'],a['PermitType'],a['PermitStatus'],dt,'Issue date','Scottsdale',sx['source'],'PermitNumber '+no+'; permit_id '+a['permit_id'],{'county':site['county_nm']+' County','evidence_basis':'Exact street address, parcel, and facility operator; purpose of specific work not stated','issuer':'City of Scottsdale','operator':a['Owner'],'parcel':a['APN'],'county_facility_id':site['facility_id'],'facility_source':m['scottsdale-county-sites.json.gz']['url'],'address':a['Address'],'full_csv_sha256':screen['source_sha256']},source=sx['url'])
