"""Replay a configured set of agency case documents and Accela record-detail pages."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.net as netfetch
import argparse, datetime as dt, json, re
from pathlib import Path
import lib.discovery as c
def capture(src,folder,idx,refresh):
    u=src['url']
    if refresh or u not in idx:
        res=netfetch.request(u,timeout=25,limit=c.LIMIT);raw=res.body;mime=res.mime
        if len(raw)>c.LIMIT:raise ValueError('over size limit')
        h=c.digest(raw);(folder/(h+'.bin')).write_bytes(raw);idx[u]=dict(url=u,sha256=h,mime=mime)
    v=idx[u];b=(folder/(v['sha256']+'.bin')).read_bytes()
    if c.digest(b)!=v['sha256']:raise ValueError('snapshot digest mismatch')
    return c.parse(b,v['mime'],u)[1],v['sha256']
def accela(s):
    header=re.search(r'(?m)^Record\s+([\w-]+):[^\n]*\n([^\n]+)\nRecord Status:\s*([^\n]+)',s)
    if not header:raise ValueError('missing record header')
    num,kind,status=[x.strip() for x in header.groups()]
    if not re.search(r'data[ -]?cent(?:er|re)',s,re.I):raise ValueError('unconfirmed data-center association')
    project=re.search(r'Project Description:\s*\n([^\n]+)',s)
    p=project[1].strip() if project else num
    event_list=[]
    for lab,exp in [('Permit issued',r'Permit Issued Date:\s*(\d\d/\d\d/\d{4})'),('Board decision',r'Meeting was held on\s*(\d\d/\d\d/\d{4})\s*ACTION:\s*BOS Approved')]:
        dates=set(re.findall(exp,s,re.I))
        for d in sorted(dates):
            event_list.append(dict(tag=lab+'-'+d,date=dt.datetime.strptime(d,'%m/%d/%Y').date().isoformat(),date_role=lab))
    if not event_list:event_list=[dict(tag='state',date=None,date_role='Status as listed; event date not provided')]
    for e in event_list:e.update(record_no=num,kind=kind,status=status,project=p,locator='Record '+num+' · '+(e['date_role'] if e['date'] else 'Record Status'))
    return event_list
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=collector_data('multistate/accela_case_pages','config.json'));ap.add_argument('--cache',type=Path,default=c.R/'cache/history/cases');ap.add_argument('--output',type=Path,default=series_path('cases'));ap.add_argument('--fetch',action='store_true');a=ap.parse_args()
    cfg=c.read(a.config,{});folder=a.cache;folder.mkdir(exist_ok=True,parents=True);idx={i['url']:i for i in c.read(folder/'index.json',[])};out=[];held=[]
    for src in cfg['sources']:
        u=src['url']
        try:
            if not a.fetch and u not in idx:raise ValueError('no archived response')
            s,h=capture(src,folder,idx,a.fetch)
            if src['adapter']=='accela':events=accela(s)
            else:
                events=[]
                for e in src['events']:
                    if not all(c.norm(k) in c.norm(s) for k in e['anchors']):raise ValueError('missing evidence anchor: '+e['tag'])
                    events.append(dict(e,record_no=src['record_no'],project=src['project'],kind=src['kind'],locator=e['anchors'][0]))
            for e in events:
                if e['date'] and e['date']>cfg['cutoff']:continue
                key=c.digest((u+'|'+e['tag']).encode())[:16]
                out.append(dict(id='case-'+key,dataset='County case files',jurisdiction=src['jurisdiction'],record_no=e['record_no'],project=e['project'],kind=e['kind'],status=e['status'],date=e['date'],date_role=e['date_role'],month=e.get('month'),url=u,locator=e['locator'],details=({'note':e.get('details'),'date_source':e['date_source'],'date_locator':e['date_locator'],'date_method':'Manually transcribed from indexed county report. The archived county release separately confirms the actions.'} if e.get('date_source') else e.get('details')),source_url=e.get('date_source',u),source_sha256=h))
        except Exception as exc:
            # Never silently drop a previously verified snapshot on a live refresh.
            if a.fetch and u in idx:raise
            held.append(dict(url=u,error=str(exc)))
    if a.fetch:c.dump(folder/'index.json',list(idx.values()))
    c.dump(a.output,out);c.dump(a.output.with_name(a.output.stem+'_coverage.json'),dict(configured=len(cfg['sources']),published=len(out),unavailable=held))
    print(len(out),'case events;',len(held),'unavailable sources')
if __name__=='__main__':main()
