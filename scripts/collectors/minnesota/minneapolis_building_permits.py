"""City of Minneapolis construction permits (CCS permits layer). Issuer: City of Minneapolis."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.net import get_simple as get, query
from lib.files import pack, unpack
from lib.records import rec
from lib.paths import CACHE
import json
D=CACHE/'mn'
from lib.arcgis import snapshot as arc
from lib.terms import pred, EX
from lib.text import ms
M='https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0'
def download():
    D.mkdir(parents=True,exist_ok=True)
    arc(M,pred(['comments']),['OBJECTID','Display','permitNumber','permitType','workType','status','milestone','comments','issueDate','completeDate'],D/'minneapolis.json.gz')
def rows():
    rows=[]
    p=D/'minneapolis.json.gz';mn=unpack(p)
    unique={}
    for raw in mn['rows']:
        n=raw['permitNumber'];v={k:i for k,i in raw.items() if k!='OBJECTID'}
        if n in unique and unique[n]!=v:raise ValueError('Conflicting city permit number '+n)
        unique[n]=v
    for r in unique.values():
        if 'Remodel Data Center to New Pickleball Courts'.lower() in (r['comments'] or '').lower():continue
        if not EX.search(r['comments'] or ''):continue
        n=r['permitNumber'];u=query(M+'/query',where="permitNumber='"+n+"'",outFields='permitNumber,permitType,workType,status,milestone,comments,issueDate,completeDate',returnGeometry='false',f='pjson');start=ms(r['issueDate']);end=ms(r['completeDate']);when=start or end
        rows.append(rec('MN','mpls-'+n,'Minneapolis CCS construction permits',n,'Building permit / '+str(r['permitType']),r['status'] or 'Not reported',when,'issue date' if start else 'completion date' if end else 'not reported',u,'permitNumber '+n,r['comments'],'Minneapolis','Hennepin County',p,issuer='City of Minneapolis',address=r['Display'],source_milestone=r['milestone'],issue_date=start,completion_date=end,work_type=r['workType']))
    return rows,dict(minneapolis_candidates=mn['count'])
