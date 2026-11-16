"""Replay actions on individually identified project-specific public planning matters."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import series_path
import argparse, collections, re
from lib.url_archive import Archive
import lib.discovery as c
D=c.R/'data/national';DS='Municipal project planning dockets'
def run(fetch):
 cases=c.read(D/'council_cases.json',{});record={(r['client'],str(r['id'])):r for r in c.read(c.R/'cache/national/councils/candidates.json',[])};a=Archive('councilvotes',fetch,owner='multistate/legistar_matters');out=collections.defaultdict(list);holds=[]
 for client,cfg in cases.items():
    for id,proj in cfg['cases'].items():
        r=record[(client,id)];st=cfg['state']
        if st!=r['state']:raise ValueError('Incorrect state')
        if not re.search(r'data[ -]*cent(?:er|re)',(r['title'] or '')+' '+(r['name'] or ''),re.I):raise ValueError('No data center in source')
        uri='https://webapi.legistar.com/v1/'+client+'/matters/'+id;url=uri+'/histories';events=a.json(url);sha=a.sources[url]['sha256']
        if len(events)>=1000:raise ValueError('Potential partial matter history')
        if not events:
            for tag,key,role in [('File introduced','introduced','Date introduced'),('File marked passed','passed','Date marked passed')]:
                day=(r.get(key) or '')[:10]
                if not day or day>'2026-11-15':continue
                details=dict(council_client=client,matter=id,description=r['title'],stage_note='File-level milestone only. The motion or project disposition is not specified by this field.',source_status=r['status'])
                out[st].append(dict(id='council-'+client+'-'+id+'-'+key,state=st,jurisdiction=cfg['locality'],county=cfg['county'],dataset=DS,record_no=r['file'],project=proj,kind='Site-specific planning proceeding',status=tag,date=day,date_role=role,url=uri,source_url=r['source'],source_sha256=r['sha'],locator='Matter '+r['file']+' · MatterId '+id,details=details))
        for e in events:
            if e.get('MatterHistoryMatterId',int(id))!=int(id):raise ValueError('Wrong case')
            day=(e.get('MatterHistoryActionDate') or '')[:10];action=e.get('MatterHistoryActionName');motion=e.get('MatterHistoryActionText');result=e.get('MatterHistoryPassedFlagName')
            if not day or day>'2026-11-15' or not action:
                holds.append([client,id,e['MatterHistoryId'],'No dated named action at cutoff']);continue
            body=e.get('MatterHistoryActionBodyName') or ''
            details=dict(council_client=client,matter=id,source_action=action,decision_body=body,vote_result=result,action_text=motion,description=r['title'],matter_title_source=r['source'],matter_title_sha256=r['sha'])
            out[st].append(dict(id='council-'+client+'-'+str(e['MatterHistoryId']),state=st,jurisdiction=cfg['locality'],county=cfg['county'],dataset=DS,record_no=r['file'],project=proj,kind='Site-specific planning proceeding',status=action,date=day,date_role='Recorded meeting action',url=uri+'/histories',source_url=url,source_sha256=sha,locator='Matter '+r['file']+' · history '+str(e['MatterHistoryId']),details=details))
 for st,rows in out.items():c.dump(series_path('council_'+st.lower()),rows)
 c.dump(D/'council_history_holds.json',holds);print({s:len(v) for s,v in out.items()},len(holds),'undated / unnamed actions held')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
