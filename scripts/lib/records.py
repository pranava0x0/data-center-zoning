"""Interchange records: build, reconcile duplicates across registers, save with a validation summary."""
import json
from collections import Counter, defaultdict
from lib.paths import ROOT, collector_data, series_path, state_folder
from lib.files import sha as _sha


def digest(p):
    return _sha(p.read_bytes())


CUT='2026-11-15'
def rec(st,id,ds,n,kind,status,when,role,u,loc,project,place,county,p,**more):
    if when and when>CUT:return None
    return dict(state=st,id=st.lower()+'-'+id,dataset=ds,record_no=str(n),kind=kind,status=status,date=when,date_role=role,url=u,source_url=u,locator=loc,project=project,jurisdiction=place,source_sha256=digest(p),details=dict(county=county,**more))
def reconcile(state,epa):
    """Only suppress exact permit + calendar-day duplicate evidence. Agency wording wins."""
    out=state[:];by=defaultdict(list)
    for r in state:by[r['record_no'],r['date']].append(r)
    for r in epa:
        hits=by.get((r['record_no'],r['date']),[])
        if len(hits)>1:raise ValueError('Ambiguous cross-register date match; inspect '+r['record_no'])
        if hits:
            hits[0]['details']['epa_crosscheck']={'url':r['url'],'locator':r['locator'],'source_sha256':r['source_sha256'],'details':r['details'],'status':r['status']}
        else:out.append(r)
    return out
def save(st,rows):
    rows.sort(key=lambda x:((x.get('date') or ''),x['id']))
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate event ID')
    p=series_path(st.lower());p.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    tally=lambda vals:dict(sorted(Counter(vals).items(),key=lambda x:(-x[1],x[0])))
    x=dict(state=st,unit='Collected source events after joining matching source records; NOT count of operating facilities or total permits. Cities reflect register address, not incorporated boundaries.',events=len(rows),county=tally(r['details']['county'] for r in rows),agency_reported_locality=tally(r['jurisdiction'] for r in rows),datasets=tally(r['dataset'] for r in rows),cross_register_date_matches=sum('epa_crosscheck' in r['details'] for r in rows))
    collector_data(state_folder(st),'validation.json').write_text(json.dumps(x,indent=2)+'\n');print(x)
def reviewed(src,id,ds,jur,num,proj,kind,status,day,role,loc,ev,page=None,details=None,**kw):
    return dict(source=src,id=id,dataset=ds,jurisdiction=jur,record_no=num,project=proj,kind=kind,status=status,date=day,date_role=role,locator=loc,evidence=ev,**({'page':page} if page else {}),details=details or {},**kw)
