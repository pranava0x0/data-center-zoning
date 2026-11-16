"""Rank county, incorporated-place and governing-township markers using reusable Virginia/Texas geometry rules."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, csv, collections, json
from lib.url_archive import Archive
from lib.geo import PNNL
from lib.geo import places, contains
import lib.discovery as c
D=c.R/'data/national'
def run(fetch):
    src=Archive('hotspots',fetch,owner='pipeline/national_hotspots');features=src.json(PNNL)['features']
    prior=list(csv.DictReader((D/'priority.csv').open()));local={r['geoid']:r for r in csv.DictReader((D/'jurisdictions.csv').open())}
    results=[];bounds={}
    for s in prior:
        st=s['state'];p=[f for f in features if f['properties']['state_abb']==st];bounds[st]={'markers':len(p),'unmatched':{}}
        if not p:continue
        groups=collections.Counter((st,'Reported county',f['properties']['county'],'') for f in p if f['properties']['county'])
        for subtype in ['place']+(['cousub'] if int(s['townships_or_subdivisions']) else []):
            url=f"https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_{s['geoid']}_{subtype}_500k.zip"
            polygons=list(places(src.get(url)[0]));miss=0
            for f in p:
                x,y=f['geometry']['coordinates'][:2];hit=[a for a,(x0,y0,x1,y1),rs in polygons if x0<=x<=x1 and y0<=y<=y1 and contains(x,y,rs)]
                if len(hit)!=1:miss+=1;continue
                a=hit[0];g=local.get(a['GEOID'],{})
                if g.get('state')!=st or g.get('layer') not in ('place','cousubs','statistical place','territory subdivisions'):miss+=1;continue
                groups[(st,g['layer'],g['name'],g['geoid'])]+=1
            bounds[st]['unmatched'][subtype]=miss
        for layer in sorted({k[1] for k in groups}):
            pairs=sorted(((k,n) for k,n in groups.items() if k[1]==layer),key=lambda x:(-x[1],x[0]))
            for k,n in pairs:results.append([*k,n,1+sum(v>n for _,v in pairs)])
    with (D/'hotspots.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow('state layer name geoid markers rank_in_layer'.split());w.writerows(results)
    c.dump(D/'hotspots_audit.json',dict(unit='PNNL IM3 mapped markers, not a facility census or electrical capacity. Zero markers is not evidence of no projects.',source=PNNL,states=bounds))
    print(len(features),'national inventory markers;',len(results),'jurisdiction priority entries.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
