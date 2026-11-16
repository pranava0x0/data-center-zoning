"""EPA ICIS-NPDES national permit and facility archive, sliced to Nevada: NPDES permit versions for facilities whose names
match the sector phrases. The archive is pinned in cache; --epa-zip replaces it and seal() records its hashes."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import json
import lib.files
from collectors.nevada.common import rx, SOURCES, labels, C, MAN
def split(zip_path):
 from lib import epa_icis as e; e.split(zip_path,('NV',))
def rows(add):
 from lib import epa_icis as epa
 fac={a['NPDES_ID']:a for a in epa.load('NV','FACILITIES') if rx.search(a['FACILITY_NAME'])};county_codes={'NV003':'Clark County','NV031':'Washoe County','NV029':'Storey County'}
 for p in epa.load('NV','PERMITS'):
  num=p['EXTERNAL_PERMIT_NMBR'];f=fac.get(num)
  if not f or p['PERMIT_TYPE_CODE']=='UFT' or not p['ISSUE_DATE']:continue
  assert f['STATE_CODE']=='NV' and p['PERMIT_TYPE_CODE']=='GPC'
  n='epa-ICIS_PERMITS.csv.gz';co=county_codes.get(f['COUNTY_CODE']);assert not f['COUNTY_CODE'] or co,(num,f['COUNTY_CODE'])
  details=dict(issuer=p['ISSUING_AGENCY'],source_locality=f['CITY'],address=f['LOCATION_ADDRESS'],facility_name=f['FACILITY_NAME'],facilities_archive='cache/history/nv/epa-ICIS_FACILITIES.csv.gz',identity_source=SOURCES['clark.pdf'],dictionary=epa.DICTIONARY,version=p['VERSION_NMBR'],activity_id=p['ACTIVITY_ID'],raw_status_code=p['PERMIT_STATUS_CODE'],effective_date=epa.iso(p['EFFECTIVE_DATE']),expiration_date=epa.iso(p['EXPIRATION_DATE']),termination_date=epa.iso(p['TERMINATION_DATE']),master_permit=p['MASTER_EXTERNAL_PERMIT_NMBR'])
  if co:details['county']=co
  labels['icis']='EPA ICIS-NPDES permit versions'
  add('icis',n,num,f['FACILITY_NAME'],'NPDES permit coverage',p['PERMIT_STATUS_CODE'],epa.iso(p['ISSUE_DATE']),'EPA issue date',co or 'Nevada',f"ICIS_PERMITS EXTERNAL_PERMIT_NMBR={num}, ACTIVITY_ID={p['ACTIVITY_ID']}, VERSION_NMBR={p['VERSION_NMBR']}; ICIS_FACILITIES NPDES_ID={num}",details,'https://echo.epa.gov/detailed-facility-report?fid='+num,key='-'.join((num,p['ACTIVITY_ID'],p['VERSION_NMBR'])))
def seal():
 from lib import epa_icis as e
 m=json.loads(MAN.read_text())
 for name in ['epa-source.json','epa-ICIS_PERMITS.csv.gz','epa-ICIS_FACILITIES.csv.gz']:
  b=(C/name).read_bytes();m['files'][name]=dict(url=e.URL,bytes=len(b),sha256=lib.files.sha(b))
 lib.files.dump(MAN,m)
