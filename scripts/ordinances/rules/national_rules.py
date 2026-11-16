"""Archive and check original government responses for the Plains/tribal ordinance supplement."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, hashlib, io, re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pypdf import PdfReader
from lib.paths import R
from lib.archive import Store
from lib.files import j
import lib.discovery as collect
from lib.text import htmltext
S=Store('rules_astra');M=R/'data/national_rules_astra_sources.json';D=R/'cache/ordinance-astra'
TARGET={'nd_code':'https://www.bismarcknd.gov/DocumentCenter/View/55775/Land-Development-Code?bidId=', 'nd_effective':'https://www.bismarcknd.gov/2371/Zoning-and-Guidelines','sd_signed':'https://mcpherson.sdcounty.gov/wp-content/uploads/2026/01/2025-1-Data-Center-Ordinance_signed.pdf','sd_notice':'https://mcpherson.sdcounty.gov/notice-of-public-hearings-ordinance-2026-1/','mt_county':'https://www.missoulacounty.gov/news/new-podcast-episode-what-can-missoula-county-do-about-data-centers','cherokee':'https://www.anadisgoi.com/index.php/government-stories/cherokee-nation-issues-data-center-task-force-report-new-policy-actions'}
TARGET.update({'id_order':'https://www.bannockcounty.gov/wp-content/uploads/2026/07/Data-Center-Moratorium_Final.pdf','id_scope':'https://www.bannockcounty.gov/datacenter/','id_grading':'https://www.bannockcounty.gov/planning/','wy_exhibit':'https://laramiecounty.legistar.com/View.ashx?GUID=CA622251-5580-4D2B-AA97-DA9D67131C2F&ID=14836887&M=F','wy_passage':'https://laramiecounty.legistar.com/LegislationDetail.aspx?GUID=277FD852-B4BB-4AE6-8EA0-CF89F06D3B5F&ID=7691002&Options=&Search=','sd_register':'https://mcpherson.sdcounty.gov/commission/county-ordinances/','sd_minutes':'https://mcpherson.sdcounty.gov/commission/commission-minutes/'})
TARGET.update({'wv_cert': 'https://code.wvlegislature.gov/5B-2-21/', 'wv_preempt': 'https://code.wvlegislature.gov/5B-2-21B/', 'wv_rule': 'https://code.wvlegislature.gov/64-10-1/', 'ky_signed': 'https://louisville.legistar1.com/model/attachments/65594097-2f6f-425b-a94b-113f69b0ac37.pdf', 'ky_text': 'https://louisville.legistar1.com/model/attachments/ac513ccc-189c-4df4-97f3-bfefd1372e1d.pdf', 'ks_sedgwick': 'https://www.sedgwickcounty.org/media/73231/0514-26-resolution-95-2026_ada_aod.pdf', 'ks_expiry': 'https://www.wichita.gov/datacenters', 'ks_olathe': 'https://www.olatheks.gov/home/showpublisheddocument/19178/638338224808700000', 'nm_santafe': 'https://www.santafecountynm.gov/documents/ordinances/Ordinance_2026-06.pdf', 'nm_scope': 'https://www.santafecountynm.gov/news/detail/santa-fe-county-approves-18-month-moratorium-on-data-centers', 'okc_action': 'https://www.okc.gov/News-articles/Oklahoma-City-Council-extends-moratorium-on-new-data-centers', 'tulsa_code': 'https://tulsaplanning.org/plans/TulsaZoningCode.pdf', 'srpmic': 'https://srpmic-nsn.gov/wp-content/uploads/2026/05/ZONING-ORDINANCE-SRO-467-2015.pdf', 'srpmic_current': 'https://srpmic-nsn.gov/government/cdd/planning/', 'mp_zone': 'https://www.cnmizoning.com/sec.asp?secID=6'})
TARGET.update({'wv_definition': 'https://code.wvlegislature.gov/11-6N-2/', 'wv_check': 'https://westvirginia.gov/datacenters/begincertification/', 'ky_registry': 'https://louisville.legistar.com/LegislationDetail.aspx?GUID=7405E0CE-574D-407B-AF7B-2D278775C4C6&ID=8172008&Options=&Search=', 'ky_council': 'https://louisvilleky.gov/news/metro-council-meeting-highlights-thursday-august-13', 'ky_forthcoming': 'https://louisvilleky.gov/news/planning-and-zoning-committee-announces-schedule-discuss-data-center-recommendations', 'ks_edgerton': 'https://edgertonks.org/data-centers/', 'ks_desoto': 'https://www.desotoks.us/465/Data-Centers', 'tulsa_report': 'https://tulsaplanning.org/pc/agendas/2026-11-04-ws.pdf', 'nm_albuquerque': 'https://documents.cabq.gov/planning/IDO/2025_IDO_Update/IDO_2026_Effective-2026-05-06.pdf', 'mp_application': 'https://cnmizoning.com/sec.asp?secID=11', 'mp_article4': 'https://cnmizoning.com/resources/files/law/Amended%20Saipan%20Zoning%20Law%20of%202013/2013%20SZL%20Amended%20-%20Article%204(1).pdf'})
TARGET.update({'ky_ordinance':'https://louisville.legistar.com/LegislationDetail.aspx?FullText=1&GUID=7405E0CE-574D-407B-AF7B-2D278775C4C6&ID=8172008&Options=&Search=','ks_county_sept':'https://www.sedgwickcounty.org/communications/news-releases/this-week-in-sedgwick-county-sept-2-2026/','tulsa_vote':'https://www.tulsacouncil.org/post/city-council-recap-november-6-2024'})
TARGET.update({'cheyenne_index':'https://www.cheyenneandarapaho-nsn.gov/tribal-council/resolutions','cheyenne_final':'https://cdn.prod.website-files.com/625854e97e951a806fc03c22/6aa00f569dd8978b17981eb9_COMPLETE%20Resolution%20Packet%20FOR%20PRINT%20ADOBE.pdf','wv_145':'https://apps.sos.wv.gov/adlaw/csr/readfile.aspx?DocId=58817&Format=PDF','wv_cert_hidc':'https://code.wvlegislature.gov/5B-2-21a/','mp_art7':'https://www.cnmizoning.com/resources/files/law/2024%20AMENDED%20SAIPAN%20ZONING%20LAW%20OF%202013/2013%20SZL_Article%207_2013.pdf','mp_publication':'https://www.cnmizoning.com/sec.asp?secID=37'})
def fetch():
 m=j(M) if M.exists() else {};D.mkdir(exist_ok=True,parents=True);hold_path=R/'data/national_rules_astra_holds.json';holds=j(hold_path) if hold_path.exists() else {}
 def get(item):
  k,u=item
  if k in m and 'error' not in m[k]:return k,m[k]
  ext='pdf' if k in ('nd_code','sd_signed','wy_exhibit','ks_olathe','wv_145') or '.pdf' in u.lower() else 'html'
  try:
   r=S.get(u,ext);b=S.read(r);p=D/(r['sha256']+'.'+ext);p.write_bytes(b);return k,dict(**r,path=str(p.relative_to(R)),retrieved=datetime.now(timezone.utc).isoformat())
  except Exception as e:return k,dict(url=u,error=str(e))
 with ThreadPoolExecutor(max_workers=4) as ex:
  for k,r in ex.map(get,TARGET.items()):
   if 'error' in r:holds[k]=r
   else:m[k]=r;holds.pop(k,None)
   collect.dump(M,m);collect.dump(hold_path,holds);print(k,r.get('error','ok'),flush=True)
def source(k,m):
 r=m[k];b=(R/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];return b
def norm(s):return ' '.join(s.split())
def extract(k,m):
 b=source(k,m)
 if m[k]['ext']=='pdf':
  pages=[norm(p.extract_text() or '') for p in PdfReader(io.BytesIO(b)).pages]
  r=m[k];ocr=r.get('ocr_path')
  if ocr:
   raw=(R/ocr).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['ocr_sha256'];o=j(R/ocr);assert len(o)==len(pages);pages=[t or norm(' '.join(x)) for t,x in zip(pages,o)]
  return pages
 return [htmltext(b)]
def validate():
 import json
 m=j(M);r=j(R/'data/national_rules_astra.json');seen=set();parsed={}
 for k,rec in enumerate(r):
  assert rec['id'] not in seen;seen.add(rec['id']);ref=next(a for a,v in m.items() if v['url']==rec['url']);pages=parsed.get(ref)
  if pages is None:pages=extract(ref,m);parsed[ref]=pages
  num=rec.get('source_page');p=pages[num-1] if num else ' '.join(pages)
  if rec['evidence'] not in p:raise ValueError((rec['id'],rec['evidence']))
 print(len(r),'anchored ordinance and policy provisions')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');a=p.parse_args()
 if a.fetch:fetch()
 if (R/'data/national_rules_astra.json').exists():validate()
