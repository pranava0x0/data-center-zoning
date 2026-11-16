"""Bridgewater Township (Somerset County) planning board agenda entry, read from the curated file
data/history/new_jersey/bridge.json. Offline only: there is no live download in this collector."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, D
import json
import lib.files
def rows():
 seen={}
 b=collector_data('new_jersey','bridge.json');v=json.loads(b.read_text());uid='nj-bridgewater-'+v['record_no'];seen[uid]=dict(id=uid,state='NJ',dataset='Bridgewater Township planning agenda',jurisdiction='Bridgewater Township',record_no=v['record_no'],project=v['project'],kind='Preliminary major subdivision',status='On agenda',date=v['date'],date_role='Agenda date',url=v['url'],source_url=v['url'],source_sha256=lib.files.sha(b.read_bytes()),locator=v['locator'],details=dict(county='Somerset County',issuer=v['authority'],evidence_method=v['method'],archive='data/history/new_jersey/bridge.json'))
 return seen
