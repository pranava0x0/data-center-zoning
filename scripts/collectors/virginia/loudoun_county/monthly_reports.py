"""Rebuild Loudoun's structure-date register, soft permit crosswalk, and indexed monthly report sample."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import lib.arcgis as arcgis
import lib.net as netfetch
import argparse, collections, datetime as dt, io, json, re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pypdf import PdfReader
import collectors.virginia.loudoun_county.building_and_zoning_gis as h

CFG=collector_data('virginia/loudoun_county/monthly_reports','config.json')
INDEX=collector_data('virginia/loudoun_county/monthly_reports','manifest.json')
COUNTS=collector_data('virginia/loudoun_county/monthly_reports','counts.json')
LINKS=collector_data('virginia/loudoun_county/monthly_reports','epd_crosswalk.json')
OUT=series_path('building')
TZ=h.ZoneInfo('America/New_York')
FIELDS='OBJECTID,LU_GIS_LOUD_ID,LU_ADDRESS,LU_MCPI,LU_USE,LU_MULTI_USE_SUBCD1,LU_MULTI_USE_SUBCD2,LU_DEVELOP_STATUS,LU_BP_ISSUE_DATE,LU_DEMOG_YEAR_BUILT,LU_NON_RES_SQ_FT,LU_AS_OF_DATE'
PFIELDS='ID,PermitNumber,PermitType,PermitWorkClass,ParcelPIN,ISSUEDATE,DESCRIPTION'
def load(row):
    return h.load_blob(row)
def query(l,w,fields,oid):
    p=arcgis.pull(h.remote,lambda r:r[0],l,w,fields,oid,batch=125,id_params={'returnGeometry':'false'})
    return {'ids':p['ids'][1],'batches':[r[1] for r in p['batches']],'oid':oid}
def attrs(ref):
    ids=load(ref['ids'])['objectIds'] or []
    out=[x['attributes'] for b in ref['batches'] for x in load(b)['features']]
    found=[a[ref['oid']] for a in out]
    if len(set(found))!=len(found) or set(found)!=set(ids) or len(found)!=len(ids):raise ValueError('Source ID reconciliation failed')
    return out
def fetch(c,reuse=False):
    old=json.loads(INDEX.read_text()) if reuse and INDEX.exists() else {}
    idx={'captured_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'config_sha256':h.sha(CFG.read_bytes()),'reports':{},'permit_candidates':[]}
    w=' OR '.join(f+ " = '"+c['use_value']+"'" for f in c['uses'])
    idx['structures']=query(c['structures'],w,FIELDS,'OBJECTID')
    pins=sorted({a['LU_MCPI'] for a in attrs(idx['structures']) if a['LU_MCPI']})
    for i in range(0,len(pins),30):
        values=pins[i:i+30]
        if not all(re.fullmatch(r'\d+',x) for x in values):raise ValueError('Unexpected PIN')
        psql="PermitType = 'Building (Commercial)' AND PermitWorkClass = 'New Construction' AND ParcelPIN IN ("+','.join("'"+p+"'" for p in values)+")"
        idx['permit_candidates'].append(query(c['issued'],psql,PFIELDS,'ID'))
    for month,url in {**c['reports'],**c.get('legacy_reports',{})}.items():
        oldref=old.get('reports',{}).get(month,{})
        if oldref.get('url')==url:
            b=(h.CACHE/(oldref['sha256']+'.pdf')).read_bytes()
            if len(b)==oldref['bytes'] and h.sha(b)==oldref['sha256']:
                idx['reports'][month]={**oldref,'captured_utc':oldref.get('captured_utc',old['captured_utc'])}
                continue
        b=netfetch.get(url,timeout=40,limit=35*1024*1024)
        if len(b)>35*1024*1024 or not b.startswith(b'%PDF'):raise ValueError('Unexpected report response: '+url)
        k=h.sha(b);(h.CACHE/(k+'.pdf')).write_bytes(b)
        idx['reports'][month]={'sha256':k,'bytes':len(b),'url':url,'captured_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
        print('Captured report:',month,flush=True)
    h.dump(INDEX,idx)
ROW=re.compile(r'^\s*([A-Z][A-Z0-9]+-\d{4}-\d{4,}|[A-Z]\d{7,})\s{2,}(\d{1,2}/\d{1,2}/\d{4})(?:\s{2,}|$)')
PHRASE=re.compile(r'\b(?:data[\s_-]*(?:processing[\s_-]+)?(?:cent(?:er|re)|ctr)s?|data[\s_-]*halls?|server[\s_-]+farms?|co[- ]?location[\s_-]+facilit(?:y|ies))\b',re.I)
def record_url(base,field,value):
    return base+'/query?'+urlencode(dict(where=field+' = '+str(int(value)),outFields='*',returnGeometry='false',f='pjson'))
def report_rows(ref,month):
    b=(h.CACHE/(ref['sha256']+'.pdf')).read_bytes()
    if len(b)!=ref['bytes'] or h.sha(b)!=ref['sha256']:raise ValueError('Archive PDF hash mismatch')
    pages=PdfReader(io.BytesIO(b)).pages; entries=[];segment=None
    for pn,page in enumerate(pages,1):
        page_text=page.extract_text(extraction_mode='layout')
        if pn==1 and not re.search(r'BUILDING PERMITS ISSUED FOR PERIOD',page_text,re.I):raise ValueError('Unrecognized report heading: '+month)
        for line in page_text.splitlines():
            m=ROW.match(line)
            if m:
                if segment:entries.append(segment)
                segment=[pn,line,[]]
            elif segment and line.strip():
                if 'DEPARTMENT OF BUILDING' in line or re.match(r'\s*(Permit Number|Construction Cost)',line):continue
                segment[2].append(line)
    if segment:entries.append(segment)
    if not entries:raise ValueError('No report rows parsed: '+month)
    hits={}
    for pn,head,body in entries:
        cols=re.split(r'\s{2,}',head.strip())
        if len(cols)<4:raise ValueError('Malformed permit row: '+head)
        number,date,work,status=cols[:4]
        if not (number.startswith('BLDC-') or any('Building (Commercial)' in l for l in body[:2])):continue
        date=dt.datetime.strptime(date,'%m/%d/%Y').date().isoformat()
        if date[:7]!=month:raise ValueError('Month/date conflict: '+number+' '+date)
        # Only the county's Structure Type cell, or the explicit Permit Description block.
        # Never promote mentions in an applicant/company name or a street address.
        normalized=[x.casefold() for x in cols]
        cls=any(x=='data center' and i>0 and re.fullmatch(r'\d{10,}',cols[i-1]) for i,x in enumerate(normalized))
        desc_lines=[];column=None
        for l in body:
            marker=l.find('Permit Description')
            if marker>=0:
                start=marker+len('Permit Description')
                tail=l[start:]
                # Applicant names may share a row to the left of the description column.
                column=start+len(tail)-len(tail.lstrip()) if tail.strip() else start
                desc_lines.append(tail.strip())
            elif column is not None and not re.match(r'^\s*Page \d+ of \d+\s*$',l,re.I):
                selected=l[max(0,column-2):].strip()
                if selected:desc_lines.append(selected)
        desc=' '.join(desc_lines)
        if not cls and not PHRASE.search(desc):continue
        url=ref['url']+'#page='+str(pn)
        if number in hits:raise ValueError('Repeated report file: '+number)
        hits[number]={'id':'va-loudoun-reports-'+number,'jurisdiction':'Loudoun County, VA',
                  'dataset':'Loudoun monthly building reports','record_no':number,
                  'project':desc[:140] if desc else 'Data Center (county structure type)','kind':'Building (Commercial)',
                  'status':status,'date':date,'date_role':'issue date','url':url,'source_url':ref['url'],
                  'locator':month+' issued-building-permit report p. '+str(pn)+'; '+number,
                  'details':{'work_classes':[work],'structure_type_match':cls,'description':desc,
                  'description_match':bool(PHRASE.search(desc)),'classification':('County issue report; printed date and In Review status conflict' if status=='In Review' else 'Dated permit from monthly county issue report')}}
    return hits,len(entries),len(pages)
def legacy_rows(ref,month):
    """Pre-LandMARC county report. Extract explicit Purpose-cell hits; exclude owner, address, contractor."""
    b=(h.CACHE/(ref['sha256']+'.pdf')).read_bytes()
    if len(b)!=ref['bytes'] or h.sha(b)!=ref['sha256']:raise ValueError('Archive PDF hash mismatch')
    pages=PdfReader(io.BytesIO(b)).pages;hits={};n=0
    for pn,page in enumerate(pages,1):
        if page.rotation:page.transfer_rotation_to_content()
        text=page.extract_text(extraction_mode='layout')
        if pn==1:
            period=re.search(r'LOG OF BUILDING PERMITS ISSUED FOR PERIOD\s+(\d+/\d+/\d+)',text)
            if not period or dt.datetime.strptime(period[1],'%m/%d/%Y').strftime('%Y-%m')!=month:
                raise ValueError('Legacy reporting period inconsistent: '+month)
        for line in text.splitlines():
            cols=re.split(r'\s{2,}',line.strip())
            if len(cols)<2 or not re.fullmatch(r'B\d{8,}',cols[0]) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',cols[1]):continue
            n+=1
            number,date=cols[:2]
            if date[:7]!=month:raise ValueError('Legacy row date inconsistent: '+number)
            if len(cols)<7 or not PHRASE.search(cols[3]):continue
            # A numeric parcel key precedes the construction code and a COM* occupancy code.
            idx=next((i for i,x in enumerate(cols) if i>=5 and re.fullmatch(r'COM[A-Z]+',x) and re.fullmatch(r'\d{9,12}',cols[i-2])),None)
            if idx is None:continue
            desc=cols[3];work=cols[idx-1];occ=cols[idx]
            if number in hits:raise ValueError('Repeated legacy issued filed number: '+number)
            hits[number]={'id':'va-loudoun-reports-'+number,'dataset':'Loudoun monthly building reports','jurisdiction':'Loudoun County, VA',
                 'record_no':number,'project':desc,'kind':'Building (commercial occupancy code '+occ+')','status':'Issued',
                 'date':date,'date_role':'issue date','url':ref['url']+'#page='+str(pn),'source_url':ref['url'],
                 'locator':month+' county issued-building-permit log p. '+str(pn)+'; '+number,
                 'details':{'work_classes':[work],'occupancy_code':occ,'status_basis':'Log of Building Permits Issued (report heading)',
                            'description':desc,'classification':'Dated permit in legacy county issue log'}}
    if not n:raise ValueError('No rows found in legacy file '+month)
    return hits,n,len(pages)
def rebuild(c):
    idx=json.loads(INDEX.read_text())
    if idx['config_sha256']!=h.sha(CFG.read_bytes()):raise ValueError('Changed supplemental configuration')
    base=json.loads(h.OUT.read_text())
    prior={r['record_no']:r for r in base if r['dataset']=='Loudoun issued permits'}
    sites=attrs(idx['structures'])
    candidates=collections.defaultdict(dict)
    for batch in idx['permit_candidates']:
        for a in attrs(batch):
            date=h.iso(a['ISSUEDATE'],TZ)
            if date:candidates[(a['ParcelPIN'],date)][a['PermitNumber']]=a
    out=[]; links=[];stats={'structures':{},'monthly_reports':{},'crosswalk':{}}
    for a in sorted(sites,key=lambda r:r['OBJECTID']):
        if c['use_value'] not in [a[f] for f in c['uses']]:raise ValueError('Mismatched structure use code')
        oid=a['OBJECTID'];date=h.iso(a['LU_BP_ISSUE_DATE'],TZ);p=a['LU_MCPI']
        if date and date>c['as_of']:continue
        n=str(a['LU_GIS_LOUD_ID']);url=record_url(c['structures'],'LU_GIS_LOUD_ID',n)
        options=candidates[(p,date)]
        links.append({'structure_gis_id':n,'object_id':oid,'issue_date':date,'pin':p,'source_url':url,
                      'candidate_permits':[{'number':num,'url':record_url(c['issued'],'ID',v['ID']),'in_description_screen':num in prior,
                                            'description':v['DESCRIPTION']} for num,v in sorted(options.items())]})
        out.append({'id':'va-loudoun-structure-'+n,'dataset':'Loudoun structures (not permit files)','jurisdiction':'Loudoun County, VA',
                    'record_no':'Structure GIS ID '+n,'project':'County-classified data center: '+(a['LU_ADDRESS'] or n),'kind':'Data-center structure observation',
                    'status':a['LU_DEVELOP_STATUS'],'date':date,'date_role':'building-permit issue date on structure',
                    'url':url,'source_url':c['structures'],'locator':'Existing Structures; GIS ID '+n,
                    'details':{'structure_gis_id':n,'portal_row_id_at_capture':str(oid),'parcel_pin':p,'source_use':a['LU_USE'],'building_permit_number':None,
                        'structure_as_of':h.iso(a['LU_AS_OF_DATE'],TZ),'same_pin_date_new_construction_candidate_numbers':sorted(options),
                        'classification':'Structure observation; no permit ID in source'}})
    stats['structures']={'rows':len(out),'distinct_gis_ids':len({r['record_no'] for r in out}),'issue_years':dict(sorted(collections.Counter(r['date'][:4] if r['date'] else 'unknown' for r in out).items()))}
    stats['crosswalk']={'basis':'same PIN, same local issue day, Building (Commercial), New Construction; candidate only',
       'number_of_candidates_per_structure':dict(sorted(collections.Counter(len(x['candidate_permits']) for x in links).items())),
       'year_2020_number_of_candidates':dict(sorted(collections.Counter(len(x['candidate_permits']) for x in links if (x['issue_date'] or '').startswith('2020')).items()))}
    both={}
    for month,ref in sorted(idx['reports'].items()):
        hits,n,pages=(legacy_rows if month in c.get('legacy_reports',{}) else report_rows)(ref,month);new={k:v for k,v in hits.items() if k not in prior}
        for k,v in hits.items():
            if k in both:raise ValueError('Overlapping monthly issue-file sample: '+k)
            both[k]=v
        for k,v in new.items():out.append(v)
        stats['monthly_reports'][month]={'pages':pages,'parsed_rows_all_types':n,'matched_commercial_building_files':len(hits),
                                          'already_in_issued_registry_screen':len(hits)-len(new),'new_files':len(new),
                                          'matched_numbers':sorted(hits),'new_numbers':sorted(new)}
    if len({r['id'] for r in out})!=len(out):raise ValueError('Duplicate supplementary record')
    h.dump(OUT,sorted(out,key=lambda r:(r['date'] or '',r['id'])));h.dump(LINKS,links);h.dump(COUNTS,stats)
    print('Wrote',len(out),'supplementary records; matched monthly report files',len(both))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--reuse-reports',action='store_true',help='reuse matching pinned monthly reports during --fetch');args=p.parse_args()
    c=json.loads(CFG.read_text())
    if args.fetch:fetch(c,reuse=args.reuse_reports)
    rebuild(c)
