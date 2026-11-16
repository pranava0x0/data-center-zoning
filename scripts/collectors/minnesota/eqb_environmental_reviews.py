"""Minnesota Environmental Quality Board environmental-review notices (statewide). Issuer: the responsible
government unit named on each review; EQB publishes them."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from concurrent.futures import ThreadPoolExecutor
from lib.net import get_simple as get, query
from lib.files import pack, unpack
from lib.records import rec
from lib.paths import CACHE
import json
D=CACHE/'mn'
from lib.terms import EX
E='https://web-api.pca.state.mn.us/eqb-submittal/projects'
def fields_eqb(r):return ' '.join(str(r.get(k) or '') for k in ('projectTitle',))+' '+str((r.get('projectDetails') or {}).get('projectSummary') or '')
def download():
    D.mkdir(parents=True,exist_ok=True)
    def yr(y):
        u=query(E+'/search/0',**{'pub-date-from':str(y)+'-01-01T00:00:00.000Z','pub-date-to':str(y)+('-11-15' if y==2026 else '-12-31')+'T23:59:59.000Z'});raw=get(u);r=json.loads(raw or b'[]');return str(y),dict(url=u,count=len(r),matches=[v for v in r if EX.search(fields_eqb(v))])
    with ThreadPoolExecutor(max_workers=4) as a:slices=dict(a.map(yr,range(2015,2027)))
    pack(D/'eqb-slices.json.gz',slices);projs={(x['aiId'],x['siId']) for s in slices.values() for x in s['matches']}
    def one(ai_si):
        ai,si=ai_si;u=query(E+'/details/'+str(ai),**{'si-id':si});rows=json.loads(get(u));pack(D/('eqb-'+si+'.json.gz'),dict(url=u,groups=rows));return si
    with ThreadPoolExecutor(max_workers=4) as a:list(a.map(one,sorted(projs)))
def rows():
    """Records plus the audit counts the validation file reports."""
    rows=[];slices=unpack(D/'eqb-slices.json.gz');projs={x['siId']:x for s in slices.values() for x in s['matches']};seen=set()
    for si in sorted(projs):
        p=D/('eqb-'+si+'.json.gz');group=unpack(p)
        for cluster in group['groups']:
            for r in cluster:
                if r.get('siId')!=si:continue # API includes other reviews at the same agency-interest site
                d=r.get('eawDocument') or {};l=r['location'];place=l['address'].get('municipality') or projs[si]['location']['address'].get('municipality') or 'Minnesota';cc=[v['name']+' County' for v in l.get('counties') or []];county=cc[0] if len(cc)==1 else 'Multiple counties' if cc else 'Not reported';stage=r.get('servicePath') or r.get('noticeTitle') or r['service'];n=r['submittedCartId'];key=(si,n)
                if key in seen:continue
                seen.add(key);when,role=next(((v[:10],name) for v,name in [(d.get('dateOfDecision'),'environmental review decision date'),(d.get('dateOfAdoption'),'environmental review adoption date'),(r.get('dateApprovedForPublication'),'approval for publication date'),(r.get('monitorPubDate'),'monitor publication date')] if v),(None,'date not recorded'))
                u='https://webapp.pca.state.mn.us/eqb-search/project-detail/'+str(r['aiId'])+'?siId='+si
                rows.append(rec('MN','eqb-'+si+'-'+str(n),'Minnesota EQB environmental review notices',si,'Environmental review / '+r['service'],stage,when,role,u,'EQB project '+si+', submitted cart '+str(n),r['projectTitle'],place,county,p,register_url=group['url'],record_number_is='EQB project identifier, not a permit',responsible_government=(r.get('rguContact') or {}).get('organization',{}).get('organizationName'),counties=cc,project_summary=fields_eqb(r)[:1100],final_notice=r.get('finalNotice'),publication_approved=r.get('dateApprovedForPublication'),adoption_date=d.get('dateOfAdoption'),decision_date=d.get('dateOfDecision')))
    return rows,dict(eqb_unique_project_matches=len(projs),year_query_results={y:s['count'] for y,s in sorted(slices.items())})
