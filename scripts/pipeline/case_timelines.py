"""Link actions only by a verified instrument key or a scoped, exact agency file number."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
from collections import defaultdict
import re
import lib.discovery as c
def attach(rows):
 grouped=defaultdict(list)
 for r in rows:
    num=str(r.get('record_no') or '').strip().upper();d=r.get('details') or {};permit=r.get('permit_key')
    if not num or not re.search(r'\d',num):continue
    state=r['state'];ds=r['dataset'];scope=r.get('locality') or r.get('jurisdiction')
    if r.get('federal_issuer')=='U.S. Environmental Protection Agency' and re.fullmatch(r'[A-Z]{2}[A-Z0-9]{7}',num):key=('EPA NPDES',num)
    elif r.get('federal_issuer')=='US Army Corps of Engineers' and re.fullmatch(r'[A-Z]{3}-[0-9A-Z-]+',num):key=('Army Corps docket',num)
    elif ds=='Interior Department land decisions':key=(ds,num)
    elif permit:key=('permit',permit)
    else:key=(ds,scope,num)
    grouped[state,key].append(r)
 count=0;links=0;used=set()
 for (st,k),rr in grouped.items():
    if len({(r.get('date') or r.get('month'),r['kind'],r['status']) for r in rr})<2:continue
    gid=c.digest(repr((st,k)).encode())[:12]
    if gid in used:raise ValueError('Case group collision')
    used.add(gid);count+=1;links+=len(rr)
    for r in rr:r['case_group']=gid
 return dict(groups=count,linked_rows=links,method='Exact file number within issuing register, state and locality, or a verified common instrument/docket. Does not link separate files by operator name, proximity or project nickname.')
