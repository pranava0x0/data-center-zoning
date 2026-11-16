"""Geography ranking inputs: PNNL data center point inventory (Arizona markers) and Census places, used to rank
counties and places in data/history/arizona/rankings.csv. Issuers: Pacific Northwest National Laboratory and the U.S.
Census Bureau."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data
from collectors.arizona.common import *
def download(save):
    for k,n in [('pnnl','pnnl.geojson.gz'),('census','census-places.zip')]:save(n,conf[k],lib.net.req(conf[k]))
def rank():
    txs=[a for a in js(gzip.decompress((C/'pnnl.geojson.gz').read_bytes()))['features'] if a['properties']['state_abb']=='AZ'];polys=list(lib.geo.places((C/'census-places.zip').read_bytes()))
    tally=Counter();geo={};outside=0;county_geo={'Maricopa County':'04013','Cochise County':'04003','Pima County':'04019'}
    for a in txs:
        p=a['properties'];tally['county',p['county']]+=1;geo['county',p['county']]=county_geo.get(p['county'],'')
        x,y=a['geometry']['coordinates'][:2];matches=[m for m,(l,b,r,t),rings in polys if l<=x<=r and b<=y<=t and lib.geo.contains(x,y,rings)]
        assert len(matches)<=1
        if matches:
            m=matches[0];k=('census_designated_place' if m['LSAD']=='57' else 'incorporated_place',m['NAMELSAD']);tally[k]+=1;geo[k]=m['GEOID']
        else:outside+=1
    with (collector_data('arizona','rankings.csv')).open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['level','rank','name','point_count','geoid','inventory_commit','boundary_vintage'])
        for lev in ('county','incorporated_place','census_designated_place'):
            arr=sorted([(k,n) for k,n in tally.items() if k[0]==lev],key=lambda it:(-it[1],it[0][1]))
            for k,n in arr:w.writerow([lev,1+sum(j>n for _,j in arr),k[1],n,geo[k],'fe4d8420f9fdc7b16b82b8461c5e4c39b93d8f1d','2024 generalized' if lev!='county' else 'Atlas county'])
    return dict(markers=len(txs),source_geometry=Counter(a['properties']['type'] for a in txs),outside_mapped_place=outside,place_points=sum(v for k,v in tally.items() if k[0]!='county'))
