"""One GeoJSON feature per linked geography; original KML polygon and hole grouping retained."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import csv, json, xml.etree.ElementTree as ET
from collections import defaultdict
from zipfile import ZipFile
import lib.discovery as c
def ring(node,outer):
    pts=[[float(v) for v in p.split(',')[:2]] for p in node.text.split()]
    if pts[-1]!=pts[0]:pts.append(pts[0][:])
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]))
    return pts if (area>0)==outer else list(reversed(pts))
def main():
    rules=c.read(c.OUT/'rules.json',[]);group=defaultdict(list)
    for r in rules:
        if r.get('map_geoid'):group[r['map_geoid']].append(r)
    geos={g['geoid']:g for g in csv.DictReader((c.R/'data/national/jurisdictions.csv').open())}
    geom={}
    for layer in ('state','county'):
        with ZipFile(c.R/'cache/geo'/('map_'+layer+'.zip')) as z:
            doc=ET.fromstring(z.read(next(k for k in z.namelist() if k.endswith('.kml'))))
        for placemark in doc.findall('.//{*}Placemark'):
            idnode=placemark.find('.//{*}SimpleData[@name="GEOID"]')
            if idnode is None or idnode.text not in group:continue
            polygons=[]
            for p in placemark.findall('.//{*}Polygon'):
                outer=p.find('.//{*}outerBoundaryIs/{*}LinearRing/{*}coordinates')
                inners=p.findall('.//{*}innerBoundaryIs/{*}LinearRing/{*}coordinates')
                polygons.append([ring(outer,True)]+[ring(i,False) for i in inners])
            geom[idnode.text]={'type':'MultiPolygon','coordinates':polygons}
    features=[]
    for gid,records in sorted(group.items()):
        g=geos[gid];shape=geom.get(gid,dict(type='Point',coordinates=[float(g['lon']),float(g['lat'])]))
        good=[r['id'] for r in records if r['check'] in ('snapshot_match','visual_source_check')]
        props=dict(geoid=gid,state=g['state'],name=g['name'],layer=g['layer'],boundary_vintage='2025',representation='internal point only' if shape['type']=='Point' else 'generalized issuing geography',published_ids=good,held_ids=[r['id'] for r in records if r['id'] not in good])
        features.append(dict(type='Feature',id=gid,geometry=shape,properties=props))
    data=dict(type='FeatureCollection',name='Selected issuing geographies; not zoning districts or eligible land',features=features)
    (c.OUT/'jurisdictions.geojson').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(len(features),'linked GIS features;',sum(not r.get('map_geoid') for r in rules),'rows without geometry retained in master table')
if __name__=='__main__':main()
