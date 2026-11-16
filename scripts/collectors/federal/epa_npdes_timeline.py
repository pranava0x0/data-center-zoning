"""Recover distinct issue and end dates. One date can describe both issuance and start.
Detailed register records outrank the derived timeline on the same permit/date.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import collections, csv
import lib.discovery as c
from collectors.federal.epa_npdes import CACHE,D,DS
from lib.epa_icis import URL, DICTIONARY, iso
EVENTS='EPA water permit timeline'
def run():
    data=c.read(CACHE,{});states=collections.defaultdict(list);known={};new=[]
    links=c.read(D/'federal_links.json',{})
    for s in csv.DictReader((c.R/'data/history/series.csv').open()):
        for r in c.read(series_path(s['series']),[]):
            if r['id'] in links or r['dataset']==DS:
                v=str(r['details']['version']);known[(r['record_no'],v)]=r
    for e in data['rows']:
        p=e['permit'];k=p['EXTERNAL_PERMIT_NMBR'],p['VERSION_NMBR'];r=known.get(k)
        if not r:continue
        seen={r['date']};d=r['details'];st=r['state']
        for col,status in [('ISSUE_DATE','Issued'),('EFFECTIVE_DATE','Effective'),('TERMINATION_DATE','Terminated'),('EXPIRATION_DATE','Expired')]:
            day=iso(p[col]);code=p['PERMIT_STATUS_CODE']
            if not day or day>'2026-11-15' or day in seen:continue
            if col=='EXPIRATION_DATE' and code!='EXP':continue
            if col=='TERMINATION_DATE' and code!='TRM':continue
            seen.add(day);num,v=k
            det=dict(federal_issuer='U.S. Environmental Protection Agency',base_record=r['id'],npdes_id=num,version=v,agency_type='EP6',reported_issuer=p['ISSUING_AGENCY'],field=col,program='NPDES')
            states[st].append(dict(id='fed-date-'+p['ACTIVITY_ID']+'-'+v+'-'+col.lower(),state=st,jurisdiction=r['jurisdiction'],county=r.get('county',''),project=r['project'],record_no=num,kind=r['kind'],dataset=EVENTS,date=day,date_role=col.replace('_',' ').title(),status=status,url=r['url'],source_url=URL,source_sha256=data['sha256'],locator='ICIS_PERMITS · '+num+' · '+p['ACTIVITY_ID']+' · version '+v+' · '+col,details=det))
    for st,rows in states.items():c.dump(series_path('edate_'+st.lower()),rows)
    print(sum(map(len,states.values())),'additional dated actions; number of permits unchanged.')
if __name__=='__main__':run()
