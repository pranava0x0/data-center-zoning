"""Texas helpers shared by the source modules: config, archive paths, the archive writer and the record builder."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from lib.files import dump, sha
import gzip, json
from urllib.parse import quote
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
C=ROOT/'cache/history/tx'; CONFIG=json.loads((collector_data('texas','config.json')).read_text())
MAN=collector_data('texas','manifest.json')
cut=CONFIG['as_of']
def saver(m):
    def save(name,b,url):
        if name.endswith('.gz'): b=gzip.compress(b,mtime=0)
        (C/name).write_bytes(b);m[name]={'sha256':sha(b),'bytes':len(b),'url':url}
    return save
def make_add(m,rows,counts,bykey):
    def add(k,n,no,project,kind,status,dt,role,href,locator,extra,local,row_id=None):
        if not no or not project:raise ValueError((k,no))
        if dt and dt>cut:counts[k+' after cutoff']+=1;return
        eventkey=(no+'|'+str(dt)+'|'+str(status) if k=='fort_worth' else no);key=(k,eventkey);row=dict(state='TX',id='tx-'+k+'-'+quote(eventkey,safe=''),dataset={'dallas':'Dallas building permits','austin':'Austin issued construction permits','fort_worth':'Fort Worth development permits','tabs':'TDLR architectural barriers registrations','san_antonio':'San Antonio issued building and trade permits','abilene':'Abilene city site-plan register'}[k],jurisdiction=local,record_no=no,project=project,kind=kind,status=status or 'Not stated',date=dt,date_role=role,url=href,source_url=CONFIG[k]['source'],source_sha256=m[n]['sha256'],locator=locator,details=dict(extra,archive='cache/history/tx/'+n,**({'portal_row_id_at_capture':row_id} if row_id is not None else {})))
        if key in bykey:
            old=bykey[key]
            if k=='san_antonio' and old['date']==dt:
                types=old['details'].setdefault('source_permit_types',[old['kind']]);types[:]=sorted(set(types+[kind]));main=next((t for t in types if t.startswith('Comm ')),types[0]);old['kind']=main+(f' (+{len(types)-1} linked types)' if len(types)>1 else '')
                old['details'].setdefault('additional_source_rows',[]).append({'locator':locator,'portal_row_id_at_capture':row_id,'kind':kind,'archive':n,'sha256':m[n]['sha256']});counts[k+' linked trade/address row']+=1;return
            if (row['date'],row['kind'],row['status']) != (old['date'],old['kind'],old['status']):raise ValueError(('Conflicting repeated permit',key))
            old['details'].setdefault('additional_source_rows',[]).append({'locator':locator,'portal_row_id_at_capture':row_id,'archive':n,'sha256':m[n]['sha256']});counts[k+' duplicate permit']+=1;return
        rows.append(row);bykey[key]=row
    return add
