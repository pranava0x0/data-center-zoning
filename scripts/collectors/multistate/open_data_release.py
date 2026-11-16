"""Publish exact data-center work in local-government registers. Each source has separate status meanings."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import csv, json, re, collections
import lib.discovery as c
D=c.R/'data/national'
def specs():return {x['feed']:x for x in csv.DictReader((D/'municipal_feeds.csv').open())}
def classify(r,cutoff,perm,no,app,obs):
    # Dataset/state/permit-key checks are required; unknown statuses must fail publication.
    from lib.status import iso,details
    d=details(r);feed=d.get('feed_id')
    if not feed:return None
    s=r.get('status');state=r['state'];reg=state+':city-feed-'+feed
    if feed=='2vzw-yean' and state=='MA':return app()
    if feed=='ydr8-5enu' and state=='IL':
        if s in ('COMPLETE','EXPIRED'):return perm(reg,'historical','Chicago explicitly reports '+s+'.')
        if s=='ACTIVE':return perm(reg,'active','Chicago explicitly reports this permit as active.')
        if s in ('Not stated','PHASED PERMITTING','SUSPENDED'):return perm(reg,'unconfirmed','Number in city permit register; current validity is not established.')
    if feed=='76t5-zqzr' and state=='WA':
        if not r.get('date'):return no('No issue date in Seattle’s register.','application')
        if s in ('Completed','Expired'):return perm(reg,'historical','Issued permit; city reports '+s+'.')
    if feed=='qxie-8qnp' and state=='MD' and r.get('date') and s=='Finaled':return perm(reg,'historical','County records an issue date and final status.')
    if feed in ('7fq7-8j7r','nbcf-m6c2') and state=='LA' and s=='Issued':return perm(reg,'unconfirmed','City or parish gives an issue date without a current status.')
    return None

def main():
    f=specs();can=c.read(c.R/'cache/national/municipal_candidates.json',[]);out=collections.defaultdict(list);held=[]
    for v in can:
        st=v['state'];code=v['feed'];num=v['no'];desc=v['description'];d=v['date'];q=f[code]
        # Exclude a prior or neighboring use from construction totals, and reject
        # references only to names/contractors rather than work at a data center.
        if not re.search(r'\b(?:data[ -]*cent(?:er|re)s?|server farm)\b',desc,re.I) or re.search(r'formerly a data center|previously a data center|former data center use|adjacent westin building datacenter|converting data center space to office|fit out of an ex[ti]+ng data center office space into office space',desc,re.I):
            held.append([st,num,'Project removed or neighboring; use not the subject of the permit.']);continue
        if d and d>'2026-11-15':continue
        s=v['status'] or ('Filed' if code=='2vzw-yean' else 'Issued' if st=='LA' else 'Not stated')
        role='City permit date (usually ready for issue, subject to fees)' if code=='ydr8-5enu' else 'Application date' if code=='2vzw-yean' else 'Issue date' if d else 'No issue date reported'
        typ='Electrical permit' if st=='MD' else 'Building permit application' if st=='MA' or not d else 'Building permit'
        snippet=' '.join(desc.split())
        out[st].append(dict(id='city-'+code+'-'+c.digest(num.encode())[:14],state=st,dataset=q['series'],jurisdiction=q['government'],county=q['county'],project=typ+' '+num+' · '+q['government'],record_no=num,status=s,kind=typ,date=d or None,date_role=role,url=v['url'],source_url=v['source'],source_sha256=v['hash'],locator=q['series']+' · '+q['number']+' '+num,details=dict(feed_id=code,work_description=snippet,local_type=v['type'])))
    for st,rr in out.items():
        if len({r['id'] for r in rr})!=len(rr):raise ValueError('Duplicate permit number')
        c.dump(series_path('portal_'+st.lower()),rr)
    c.dump(D/'municipal_holds.json',held)
    print('City/parish registers:',{k:len(v) for k,v in out.items()},'; held',len(held))
if __name__=='__main__':main()
