"""Inventory searchable government permit tables; catalog hits are leads, not cases.
Use --fetch to pin pages of the public catalogue, --metadata to inspect candidate schemas.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, collections, csv, json, re
from urllib.parse import urlencode
from lib.url_archive import Archive
import lib.discovery as c
D=c.R/'data/national'
TERMS=['building permits','construction permits','land use permits','commercial permits','electrical permits']
def run(fetch=False):
 a=Archive('national_catalog',fetch,owner='pipeline/national_permit_catalog');db={};tot={}
 for word in TERMS:
    n=None;seen=0
    for offset in range(0,6000,100):
        url='https://api.us.socrata.com/api/catalog/v1?'+urlencode({'q':word,'only':'datasets','limit':100,'offset':offset})
        page=a.json(url);n=page['resultSetSize'] if n is None else n
        if not page['results'] and offset<n:raise ValueError('Missing catalog page')
        for x in page['results']:
            r=x['resource'];domain=x['metadata']['domain'];rid=r['id'];k=domain+':'+rid
            if k not in db:db[k]=dict(domain=domain,table=rid,title=r['name'],source=x.get('permalink'),attribution=r.get('attribution'),fields=r.get('columns_field_name',[]),labels=r.get('columns_name',[]),queries=[])
            db[k]['queries'].append(word)
        seen+=len(page['results'])
        if seen>=n:break
    tot[word]={'catalog_count':n,'returned':seen}
 c.dump(D/'permit_catalog_inventory.json',{'discovery':'https://api.us.socrata.com/api/catalog/v1','queries':tot,'results':list(db.values()),'scope':'Discovery includes duplicates, derived views and non-U.S. records. Results count datasets, not permits. Only approved government registers enter the history.'})
 print(len(db),'distinct publisher/table pairs',tot)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
