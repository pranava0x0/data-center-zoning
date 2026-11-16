"""Resolve agency case aliases in the Corps Digital Library before querying the national action register."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import argparse
from datetime import date
from xml.etree import ElementTree as ET
import lib.discovery as c
import collectors.federal.usace_regulatory as f
from lib.url_archive import Archive
M=collector_data('federal/usace_virginia_prior_actions','inquiry.json')
REG='US Army Corps of Engineers regulatory public actions'
NOTICE='US Army Corps of Engineers district public notices'
LIB='https://usace.contentdm.oclc.org/digital/api/collection/'
FILES={'timber':('p16021coll15',10724,10722),'dulles26':('p16021coll15',10795,10790),'dulles20':('p16021coll7',14777,14770)}
def run(fetch=False):
 a=Archive('federal_va_prior',fetch,owner='federal/usace_virginia_prior_actions');manifest=c.read(M,{});docs={}
 if fetch:
    for q in ('NAO-2011-01135','NAO-2021-01135','NAO-2006-07410'):
        ps=f.pages('"'+q+'"','da');found={x['properties']['identifier'] for x,r in f.unpack(ps)}
        manifest[q]=dict(da=ps,sa={k:f.pages('identifier:"'+k+'"','sa') for k in sorted(found|{q})})
    c.dump(M,manifest)
 for name,(col,parent,child) in FILES.items():
    base=LIB+col+'/id/';xml,_=a.get(base+str(parent)+'/download')
    assert str(child) in {e.findtext('pageptr') for e in ET.fromstring(xml).findall('.//page') if 'public notice' in e.findtext('pagetitle','').lower()}
    url=base+str(child)+'/download';raw,h=a.get(url);assert raw.startswith(b'%PDF');txt=c.norm(c.parse(raw,'application/pdf',url)[1]);docs[name]=url,h,txt
 items=[]
 def add(suffix,reg,day,role,kind,status,ref,anchor,summary,*,source_ref=None,view='',extra=None):
    u,h,t=docs[ref];assert c.norm(anchor) in t,(ref,anchor)
    key,county,project=('NAO-2021-01135-mmw','Mecklenburg County','Microsoft Timber data center') if ref=='timber' else ('NAO-2006-07410-TREC','Loudoun County','Digital Dulles data center')
    src,sha=(source_ref['url'],source_ref['sha256']) if source_ref else (u,h)
    d=dict(federal_issuer='US Army Corps of Engineers',scope=summary,corps_file=key,county=county,library_notice=u,library_notice_sha256=h,**(extra or {}))
    if view:d['orm_view']=view
    items.append(dict(id='fed-virginia-corps-'+suffix,state='VA',dataset=reg,jurisdiction=county,county=county,record_no=key,project=project,kind=kind,status=status,date=day,date_role=role,url=src,source_url=src,source_sha256=sha,locator=key+' · '+(view+' action at '+day if view else 'Norfolk District public notice; '+anchor),details=d))
 assert not list(f.unpack(manifest['NAO-2011-01135']['da']))
 for site,short,ident,needle in [('timber','NAO-2021-01135','NAO-2021-01135-mmw','construction of its data center facility'),('dulles26','NAO-2006-07410','NAO-2006-07410-TREC','Digital Dulles data center campus')]:
    assert ident in [x['properties']['identifier'] for x,_ in f.unpack(manifest[short]['da'])]
    for feat,ref in f.unpack(manifest[short]['sa'][ident]):
        z=feat['properties'];assert z['identifier']==ident;kind,st=f.facts(z);day,role=f.dates(z);v=z['vtype']
        summary={'jds':'The Corps determined which waters fall within its jurisdiction. This does not authorize construction.','issued':'The Corps recorded a standard permit with special conditions. The register does not say whether it remains in force.','nepa_ea':'The Corps published its final environmental assessment for the Timber project.'}[v]
        if site=='timber' and day=='2021-10-04':
            # One original issue, two agency dates. Prefer the instrument-specific account, preserve both.
            assert 'originally issued on october 1, 2021' in docs[site][2]
            add('timber-original',REG,'2021-10-01','original issuance date stated in district notice',kind,st,site,needle,'The district dates the original permit October 1; its action register shows October 4. The district later described this permit as expired before reauthorization.',view=v,extra={'orm_action_date':day,'orm_url':ref['url'],'orm_sha256':ref['sha256'],'superseded_original':True});continue
        add(short.lower()+'-'+v+'-'+day,REG,day,role,kind,st,site,needle,summary,source_ref=ref,view=v)
 add('timber-mod24','Army Corps prior permit amendments','2024-08-28','amendment date stated by the Corps','Amendment to the original wetlands permit','Modified','timber','modified on August 28, 2024','The district identifies an amendment to the original permit. Its notice does not supply a new permit number or an exact expiry date.')
 add('timber-notice25',NOTICE,'2025-12-05','publication date printed on notice','Application to reauthorize expired permit','Public notice published','timber','Published: December 5, 2025','Microsoft sought permission to finish the remaining wetland impacts. The public comment deadline was not the permit expiry date.')
 add('dulles-notice20',NOTICE,'2020-07-10','publication date printed on notice','Application for phased data center campus','Public notice published','dulles20','July 10, 2020','The Corps requested comments on a proposed phased campus in Loudoun County.')
 add('dulles-notice26',NOTICE,'2026-01-02','publication date printed on notice','Application to modify wetlands permit','Public notice published','dulles26','Published: January 2, 2026','The applicant sought a modification to an existing individual permit. The notice does not grant the requested change.')
 assert len(items)==9
 c.dump(series_path('corpsprior_va'),items);print('9 dated actions in 2 reconciled Corps files')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
