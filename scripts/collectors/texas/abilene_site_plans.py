"""City of Abilene: site-plan register (pinned government-page reader excerpt, reviewed by hand on refresh)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.files import dump, sha
from lib.net import req
from lib.terms import MATCH, patterns
from lib.text import isodate, Fields
import lib.arcgis as arcgis
import gzip, json, re
from urllib.parse import urlencode, quote
from collections import Counter
from collectors.texas.common import ROOT, C, CONFIG, MAN, cut, saver
def download(m):
    snapshot=C/'abilene-government-reader.json'
    m[snapshot.name]={'sha256':sha(snapshot.read_bytes()),'bytes':snapshot.stat().st_size,'url':CONFIG['abilene']['source'],'method':'Government page excerpt, pinned; requires web-reader review on refresh'}
def rows(m,add,exclusions):
    k='abilene';n='abilene-government-reader.json';x=CONFIG[k]
    lines=' '.join(json.loads((C/n).read_text())['lines'])
    for no,v in x['plans'].items():
        if not all(t in lines for t in (no,v['status'],v['project'])):raise ValueError('Abilene reviewed source no longer matches')
        add(k,n,no,v['project'],'City site plan',v['status'],None,'Decision date not stated',v['url'],v['locator'],{'issuer':'City of Abilene','county':'Taylor County','evidence_method':'city register, reviewed web-reader excerpt; associated plan linked','snapshot_as_of':cut},'Abilene')
