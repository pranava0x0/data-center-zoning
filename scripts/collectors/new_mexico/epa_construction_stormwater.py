"""Replay New Mexico CGP permit versions, with identity verified beyond the operator name."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, CACHE
import csv, datetime as dt, gzip, hashlib, json, re
from pathlib import Path
import lib.discovery as c
from lib.epa_icis import load, URL
from collectors.new_mexico.sources import LETTER,JUP_LOC,AQNS
BASE=CACHE/'nm'
def water():
    # County/municipality is tied to separate primary location evidence, not the permittee's mailing city.
    fac={x['NPDES_ID']:x for x in load('NM','FACILITIES')}; rows=[];held=[];seen=set()
    raw=c.read(BASE/'epa-source.json',{});slicepins=c.read(collector_data('new_mexico','epa_pins.json'),{})
    for n,h in slicepins.items():
        if not h or hashlib.sha256((BASE/n).read_bytes()).hexdigest()!=h:raise ValueError('EPA evidence changed: '+n)
    if len(slicepins)!=3:raise ValueError('Missing state slice pins')
    for p in load('NM','PERMITS'):
        num=p['EXTERNAL_PERMIT_NMBR'];f=fac.get(num,{})
        who=p['PERMIT_NAME'].strip();name=f.get('FACILITY_NAME','');address=f.get('LOCATION_ADDRESS','')
        if not re.search(r'data\s*cent(?:er|re)|greater kudu|project jupiter|project antelope|westpointe',name+' '+who,re.I):continue
        key=(num,p['VERSION_NMBR'])
        if key in seen:raise ValueError('Duplicate EPA version '+str(key))
        seen.add(key)
        if 'WESTPOINTE DATA CENTER' in name and 'DAYTONA' in address:location=('Albuquerque','Bernalillo County',AQNS)
        elif 'PROJECT JUPITER MICROGRID' in name:location=('Doña Ana County','Doña Ana County',JUP_LOC)
        elif who.casefold()=='greater kudu' and '4250 MESSENGER LOOP' in address:location=('Los Lunas','Valencia County',LETTER)
        else:
            held.append(dict(permit=num,version=p['VERSION_NMBR'],project=name,reason='Possible energy project or applicant-only match; data-center site not independently established.'));continue
        if p['MASTER_EXTERNAL_PERMIT_NMBR']!='NMR100000':raise ValueError('Unexpected master permit')
        place,county,cite=location;status=p['PERMIT_STATUS_CODE'];datecol={'TRM':'TERMINATION_DATE','EFF':'EFFECTIVE_DATE','EXP':'EXPIRATION_DATE'}[status]
        iso=lambda v:dt.datetime.strptime(v,'%m/%d/%Y').date().isoformat() if v else ''
        day=iso(p[datecol]);term=iso(p['EXPIRATION_DATE'])
        if day>'2026-11-15':continue
        u='https://echo.epa.gov/effluent-charts#/'+num
        rows.append(dict(id='nm-epa-'+num.lower()+'-v'+p['VERSION_NMBR'],state='NM',dataset='EPA New Mexico construction stormwater coverage',record_no=num,jurisdiction=place,county=county,project=name.title(),kind='Construction stormwater permit coverage',status={'EFF':'Effective','EXP':'Expired','TRM':'Terminated'}[status],date=day,date_role={'EFF':'Effective date','EXP':'Expiration date','TRM':'Termination date'}[status],url=u,source_url=URL,source_sha256=raw['sha256'],locator='ICIS_PERMITS · '+num+' · version '+p['VERSION_NMBR'],details=dict(version=p['VERSION_NMBR'],raw_status=status,permittee=who,facility=name,permit_name=p['PERMIT_NAME'],address=address,project_location_source=cite,issue_date=iso(p['ISSUE_DATE']),effective_date=iso(p['EFFECTIVE_DATE']),expiration_date=term,termination_date=iso(p['TERMINATION_DATE']),master_permit=p['MASTER_EXTERNAL_PERMIT_NMBR'])))
    return rows,held
