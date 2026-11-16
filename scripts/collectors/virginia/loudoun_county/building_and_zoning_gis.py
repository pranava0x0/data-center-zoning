"""Pull all matching object IDs from configured ArcGIS layers; replay hash-verified bytes offline."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.arcgis as arcgis
import lib.net as netfetch
import argparse, collections, datetime as dt, hashlib, json, pathlib, re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import lib.discovery as collect

ROOT = pathlib.Path(__file__).resolve().parents[4]
DEF_CONF = collector_data('virginia/loudoun_county/building_and_zoning_gis','config.json')
CACHE = ROOT/'cache/history/loudoun'
INDEX = collector_data('virginia/loudoun_county/building_and_zoning_gis','manifest.json')
OUT = series_path('loudoun')
STATS = collector_data('virginia/loudoun_county/building_and_zoning_gis','counts.json')

def sha(b):
    return hashlib.sha256(b).hexdigest()

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
    tmp.replace(path)

def remote(url, **args):
    query = url+'?'+urlencode(dict(f='json', **args))
    raw = netfetch.get(query, timeout=70, limit=32*1024*1024)
    if len(raw)>32*1024*1024: raise ValueError('Oversized batch')
    data = json.loads(raw)
    if 'error' in data: raise ValueError(f'ArcGIS rejected query: {data["error"]}')
    h = sha(raw)
    CACHE.mkdir(parents=True,exist_ok=True)
    path=CACHE/(h+'.json')
    if not path.exists(): path.write_bytes(raw)
    return data, {'url':query,'sha256':h,'bytes':len(raw)}

def load_blob(rec):
    buf=(CACHE/(rec['sha256']+'.json')).read_bytes()
    if sha(buf)!=rec['sha256'] or len(buf)!=rec['bytes']: raise ValueError('Archive mismatch: '+rec['url'])
    return json.loads(buf)

def where(cfg, lay):
    if not all(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',f) for f in lay['text_fields']):
        raise ValueError('Bad SQL field')
    return ' OR '.join("UPPER("+field+") LIKE '"+term.replace("'","''")+"'" for field in lay['text_fields'] for term in cfg['like_terms'])

def fields(l):
    return list(dict.fromkeys(x for x in [l[k] for k in ('oid','guid','number','name','description','type','status','date')]+l['extras'] if x))

def fetch(cfg, conf_hash):
    idx = {'captured_utc':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'config_sha256':conf_hash,'layers':{}}
    for l in cfg['layers']:
        key, endpoint = l['key'], l['base']
        meta, mref = remote(endpoint)
        names = {f['name'] for f in meta['fields']}
        if not set(fields(l)+l['text_fields'])<=names: raise ValueError('Source schema drift: '+key)
        sql=where(cfg,l)
        batch=min(cfg['batch_size'],meta['maxRecordCount'])
        pulled=arcgis.pull(remote,lambda r:r[0],endpoint,sql,','.join(fields(l)),l['oid'],batch,id_params={'returnGeometry':'false'})
        ids=pulled['ids'][0]['objectIds'] or []
        _,cref=remote(endpoint+'/query',where='1=1',returnCountOnly='true')
        rec={'name':meta['name'],'where':sql,'metadata':mref,'all_record_count':cref,'object_ids':pulled['ids'][1],'batches':[r[1] for r in pulled['batches']]}
        idx['layers'][key]=rec
        print(f"{key}: captured {len(ids)} server candidates",flush=True)
    dump(INDEX,idx)

def iso(ms,tz):
    if ms is None: return None
    if not isinstance(ms,(int,float)): raise ValueError('Expected epoch milliseconds')
    return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).astimezone(tz).date().isoformat()

def longest(vals):
    return max(vals,key=lambda s:(len(s),s)) if vals else ''

def rebuild(cfg, conf_hash):
    idx=json.loads(INDEX.read_text())
    if idx['config_sha256']!=conf_hash: raise ValueError('Configuration changed since capture. Refresh or restore the pinned configuration.')
    regex={k:re.compile(p,re.I) for k,p in cfg['patterns'].items()}
    tz=ZoneInfo(cfg['timezone'])
    out,stats=[],{}
    for l in cfg['layers']:
        key=l['key'];section=idx['layers'][key];group=collections.defaultdict(list)
        ids=load_blob(section['object_ids'])['objectIds'] or []
        meta=load_blob(section['metadata'])
        if meta['name']!=section['name'] or section['where']!=where(cfg,l):raise ValueError('Layer metadata or predicate inconsistent')
        seen=set()
        summary={'source_total_all_uses':load_blob(section['all_record_count'])['count'],'source_candidate_object_ids':len(ids),
                 'excluded_no_phrase_rows':0,'excluded_post_cutoff_rows':0,'excluded_missing_number_guid_rows':0}
        for batch in section['batches']:
            for feat in load_blob(batch)['features']:
                a=feat['attributes'];oid=a[l['oid']]
                if oid in seen:raise ValueError(f'{key}: duplicate source row {oid}')
                seen.add(oid)
                hits={field:[n for n,rx in regex.items() if rx.search(a.get(field) or '')] for field in l['text_fields']}
                hits={k:v for k,v in hits.items() if v}
                if not hits:summary['excluded_no_phrase_rows']+=1;continue
                date=iso(a[l['date']],tz)
                if date and date>cfg['as_of']: summary['excluded_post_cutoff_rows']+=1;continue
                num=str(a.get(l['number']) or '').strip();guid=str(a.get(l['guid']) or '').strip()
                if not num and not guid: summary['excluded_missing_number_guid_rows']+=1;continue
                group[num or ('guid:'+guid)].append((a,date,hits))
        if set(ids)!=seen or len(ids)!=len(seen):raise ValueError('Object ID reconciliation failed')
        counter=collections.Counter()
        for num,records in sorted(group.items()):
            records.sort(key=lambda r:r[0][l['oid']])
            arrays=[a for a,_,__ in records]
            recordnum=arrays[0].get(l['number'])
            def vals(f):return sorted({a.get(f) for a in arrays if f and a.get(f) is not None and a.get(f)!=''})
            kinds,statuses=vals(l['type']),vals(l['status'])
            dates=sorted({d for _,d,_ in records if d})
            desc=longest(vals(l['description']))
            names=vals(l['name'])
            hits={f:sorted({tag for _,__,h in records for tag in h.get(f,[])}) for f in l['text_fields']}
            hits={f:h for f,h in hits.items() if h}
            if l['role']=='land_use': classification='Land-use case; not permit issuance'
            elif l['role']=='submitted': classification='Submitted permit; not evidence of issuance'
            elif not dates: classification='Issued-permits source; no issue date reported'
            else: classification='Dated permit from issued-permits register'
            oids=vals(l['oid'])
            uri=l['base']+'/query?'+urlencode(dict(where=l['number']+" = '"+str(recordnum).replace("'","''")+"'" if recordnum else (l['oid']+' = '+str(oids[0])),outFields=','.join(fields(l)),returnGeometry='false',f='pjson'))
            details={'source_object_ids':oids,'source_guids':vals(l['guid']),'matched_fields':hits,'classification':classification,'description':desc}
            if len(statuses)>1 or len(kinds)>1 or len(dates)>1 or len(details['source_guids'])>1:
                details['conflicting_values']={'status':statuses,'kind':kinds,'dates':dates,'guids':details['source_guids']}
                counter['files_with_conflicting_values']+=1
            if l['role'] in {'issued','submitted'}:
                details.update(work_classes=vals('PermitWorkClass'),parcel_pins=vals('ParcelPIN'),application_dates=sorted({iso(x,tz) for x in vals('APPLYDATE')}),final_dates=sorted({iso(x,tz) for x in vals('FINALIZEDATE')}),snapshot_dates=sorted({iso(x,tz) for x in vals('DataSnapshot')}))
            else:
                details['geometry_sources']=vals('Shp_Source')
            display=longest(names) if names else desc
            if len(display)>140:display=display[:137].rsplit(' ',1)[0]+'…'
            out.append({'id':cfg['id_prefix']+'-'+key+'-'+num,'dataset':l['label'],'jurisdiction':cfg['jurisdiction'],'record_no':recordnum or num,
                        'project':display or '(not named)','kind':' / '.join(kinds) or 'Not reported',
                        'status':' / '.join(statuses) or 'Not reported','date':dates[0] if len(dates)==1 else None,
                        'date_role':l['date_role'],'url':uri,'source_url':l['base'],
                        'locator':section['name']+'; '+num+'; object ID '+', '.join(map(str,oids)),'details':details})
            counter['matched_source_rows']+=len(records);counter['files']+=1
            if len(records)>1:counter['multirow_files']+=1
            if not dates:counter['files_missing_date']+=1
        subset=[r for r in out if r['dataset']==l['label']]
        stamp=sorted(r['date'] for r in subset if r['date'])
        stats[key]={**summary,**counter,'first_matched_date':stamp[0] if stamp else None,'last_matched_date':stamp[-1] if stamp else None,
                    'by_year':dict(sorted(collections.Counter(r['date'][:4] if r['date'] else 'unknown' for r in subset).items())),
                    'by_source_status':dict(sorted(collections.Counter(r['status'] for r in subset).items())),
                    'by_source_type':dict(sorted(collections.Counter(r['kind'] for r in subset).items()))}
        s=stats[key]
        assert s['matched_source_rows']+sum(v for k,v in summary.items() if k.startswith('excluded_'))==len(seen)
    if len({r['id'] for r in out})!=len(out):raise ValueError('Nonunique history IDs')
    out.sort(key=lambda r:(r['date'] or '', r['id']))
    dump(OUT,out);dump(STATS,stats)
    print('Wrote',len(out),'records to',OUT.relative_to(ROOT))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true',help='capture a new complete snapshot before rebuilding');p.add_argument('--config',type=pathlib.Path,default=DEF_CONF)
    args=p.parse_args();raw=args.config.read_bytes();cfg=json.loads(raw)
    global CACHE
    CACHE=ROOT/cfg['artifacts']['cache']  # manifest, output and counts are fixed by collector_data()/series_path()
    if any(x.resolve()==ROOT or ROOT not in x.resolve().parents for x in (CACHE,INDEX,OUT,STATS)): raise ValueError('Artifact paths must be within project')
    if any(l['role'] not in {'land_use','issued','submitted'} for l in cfg['layers']):raise ValueError('Invalid layer role')
    if args.fetch:fetch(cfg,sha(raw))
    rebuild(cfg,sha(raw))
if __name__=='__main__':main()
