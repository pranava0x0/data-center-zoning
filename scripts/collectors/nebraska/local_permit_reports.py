"""Papillion (City Administrator permit reports) and Lincoln-Lancaster County air permit records, from the reviewed local extract data/history/nebraska/local.json."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import json
from lib.records import rec
PAP='Papillion City Administrator permit reports'; LAD='Lincoln-Lancaster County air permits'
def rows():
 rows=[]
 p=collector_data('nebraska','local.json')
 for id,n,kind,st,dt,role,project,u,loc,place,county in json.loads(p.read_text()):
    rows.append(rec('NE',id,PAP if id.startswith('papp') else LAD,n,kind,st,dt,role,u,loc,project,place,county,p,source_capture='Reviewed indexed city PDF; digest covers extracted observation manifest.'))
 return rows
