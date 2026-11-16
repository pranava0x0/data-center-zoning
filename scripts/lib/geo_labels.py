"""Retain City, Town or Village when it belongs to the actual place name (e.g. Kansas City)."""
import csv, re
from collections import defaultdict
import lib.discovery as c
SUFFIX=re.compile(r' (?:city|town|village)$')
def exceptions():
 out=defaultdict(set)
 with (c.R/'data/national/jurisdictions.csv').open() as fp:
    for g in csv.DictReader(fp):
        if g['layer'] in ('place','statistical place'):
            s=g['name'].casefold();base=SUFFIX.sub('',s)
            if s!=base and SUFFIX.search(base):out[g['state']].add(base)
 return {k:sorted(v) for k,v in sorted(out.items())}
def key(raw,st,keep):
 s=re.sub(r'^(?:city|town|village) of ','',str(raw or '').lower().strip())
 return s if s in keep.get(st,()) else SUFFIX.sub('',s)
