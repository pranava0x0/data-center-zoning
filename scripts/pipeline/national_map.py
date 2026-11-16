"""Read the pinned Census polygons; limit displayed vertices, never use display geometry for joins."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, json, math, xml.etree.ElementTree as ET, zipfile
from collections import defaultdict
from functools import lru_cache
import lib.discovery as c
from lib.url_archive import Archive
def thin(p,tol):
    if len(p)<4:return p
    x,y=p[0];X,Y=p[-1];dx,dy=X-x,Y-y;L=dx*dx+dy*dy
    def sq(v):
        a,b=v;t=max(0,min(1,((a-x)*dx+(b-y)*dy)/L)) if L else 0
        return (a-x-t*dx)**2+(b-y-t*dy)**2
    i=max(range(1,len(p)-1),key=lambda k:sq(p[k]))
    if sq(p[i])>tol*tol:return thin(p[:i+1],tol)[:-1]+thin(p[i:],tol)
    return [p[0],p[-1]]
def national(rules,hi,existing):
    root=c.R;rows=list(csv.DictReader((root/'data/national/jurisdictions.csv').open()))
    ledger={r['geoid']:r for r in csv.DictReader((c.OUT/'national_jurisdiction_checks.csv').open())}
    geo=rules['geo'];keys={p[0] for p in geo};name=lambda s:s.lower().strip().removesuffix(' city').removesuffix(' town').removesuffix(' village')
    names={st:{name(k) for k in areas} for st,areas in hi['areas'].items()}
    wanted={st for st in hi['areas']}
    for g in rows:
        if g['geoid'] in keys:continue
        if g['layer'] in ('state','counties') or (g['layer'] in ('place','cousubs','statistical place','territory subdivisions') and name(g['name']) in names.get(g['state'],{})):
            geo.append([g['geoid'],g['state'],g['layer'],g['name'],round(float(g['lat']),3),round(float(g['lon']),3),'',0,None,0,0]);keys.add(g['geoid'])
    for g in geo:
        rec=ledger.get(g[0])
        if not rec or g[7] or g[10]:continue
        outcome=rec['result']
        if rec['url']:g[8]=rec['url']
        g[10]=int(rec['pages'] or 0)
        if int(rec['mentions'] or 0):g[6]='screened: candidate only'
        elif g[10]:g[6]='screened: limited discovery'
        elif 'read' in outcome.casefold() or 'unavailable' in outcome.casefold():g[6]='retrieval failed'
    # Census 20m polygons cover the mainland and noncontiguous states. For island
    # units not in the generalized file, render a labeled location point in the inset.
    geo_ref={g[0]:g for g in geo};new={'state':[],'county':[]};seen=set()
    for typ in new:
        z=zipfile.ZipFile(root/'cache/geo'/('map_'+typ+'.zip'))
        tree=ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.kml'))))
        for p in tree.findall('.//{*}Placemark'):
            a={s.attrib['name']:s.text for s in p.findall('.//{*}SimpleData')};st=a['STUSPS'];gid=a['GEOID']
            if gid not in geo_ref:continue
            rings=[]
            for node in p.findall('.//{*}LinearRing/{*}coordinates'):
                pts=[[round(float(s),3) for s in item.split(',')[:2]] for item in node.text.split()]
                if st=='AK':pts=[[x if x<0 else x-360,y] for x,y in pts]
                # Small islands must survive simplification.
                simple=thin(pts,.009 if typ=='state' or st in wanted else .025)
                rings.append(simple if len(simple)>=4 else pts)
            new[typ].append([st,gid,a.get('NAMELSAD',a['NAME']),rings]);seen.add(gid)
    # Census 500k includes all 91 inhabited-territory county equivalents. Their
    # real shapes also set a usable island extent when the 20m file lacks one.
    from lib.geo import places
    src='https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip'
    for a,bb,parts in places(Archive('federal_geo', owner='federal', name='geo_sources.json').get(src)[0]):
        gid=a['GEOID'];g=geo_ref.get(gid)
        if not g or g[1] not in ('GU','MP','AS','VI','PR') or gid in seen:continue
        rings=[]
        for part in parts:
            pts=[[round(x,4),round(y,4)] for x,y in part];simple=thin(pts,.001)
            if len(simple)>=4:rings.append(simple)
            elif len(pts)>=4:rings.append(pts)
        if rings:new['county'].append([g[1],gid,g[3],rings]);seen.add(gid)
    for g in geo:
        if g[0] in seen or g[2] not in ('counties','state'):continue
        typ='state' if g[2]=='state' else 'county'
        new[typ].append([g[1],g[0],g[3],[],[float(g[5]),float(g[4])]])
    return new
