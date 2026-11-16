"""Clark County Department of Environment and Sustainability, Division of Air Quality: Part 70 operating permit and Title V
renewal register, dust-control permit snapshot, public-participation notices, and the stationary-source inventory layer
(inventory leads only, no permit dates)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import html, re
import lib.text
from collectors.nevada.common import read, pages, plain, SOURCES, fetch_sources, pull_layer, candidates
NAMES=('ctitle.html','clark.pdf','dust.pdf','flexential.html')
def download(m,stats):
 fetch_sources(m,NAMES);pull_layer(m,stats,'clark_sources')
def rows(add,excluded,leads):
 cl={'county':'Clark County','issuer':'Clark County Division of Air Quality'}
 for a,n,o,loc,u in candidates('clark_sources',excluded):
  leads.append({'source_id':a['Source_ID'],'facility':a['Source_Name'],'postal_location':a['Source_Location'],'source_type':a['Source_Type'],'url':u,'reason':'Air stationary source inventory; no issued permit or action date in layer.'})
 n='clark.pdf';s=pages(n)[0];assert all(v in s for v in ['July 1, 2021','June 30, 2026','May 15, 2025','16304','Significant Revision'])
 for status,dt in [('Issued','2021-07-01'),('Significant Revision','2025-05-15')]:
  add(n,n,'16304','Switch, Ltd.','Part 70 operating permit',status,dt,'Issue date' if status=='Issued' else 'Revision date','Clark County','p. 1, source 16304',dict(**cl,expiration_date='2026-06-30',renewal_register=SOURCES['ctitle.html']),key='16304-'+dt)
 n='ctitle.html';s=plain(read(n).decode());assert re.search(r'16304 Switch LTD.{0,150}June 30 2026 Dec 3 2025',s)
 add(n,n,'16304','Switch, Ltd.','Part 70 operating permit renewal','Renewal application received','2025-12-03','Renewal application received date','Clark County','Title V table, 16304, renewal application received',cl)
 n='dust.pdf';pgs=pages(n)
 for pg,no,project,exp in [(50,'46555 - 12','Switch NAP11','06/18/2025'),(55,'56593 - 4','Switch NAP 17 & 18','04/04/2026')]:
  line=pgs[pg-1];assert all(v in line for v in [no,project,exp,'As of 6/2/2025'])
  add(n,n,no,project,'Dust control operating permit','Active at snapshot','2025-06-02','Register snapshot date','Clark County',f'p. {pg}, permit {no}',dict(**cl,expiration_date=lib.text.isodate(exp)))
 n='flexential.html';s=html.unescape(read(n).decode());assert all(v in s for v in ['March 23, 2026','17272','3330 East Lone Mountain Road','Clark County Division of Air Quality'])
 add(n,n,'17272','Flexential Lone Mountain Data Center','Stationary source air permit public participation','Public participation initiated','2026-03-23','Public notice posting date','Clark County','County notice header; Source ID 17272',dict(**cl,postal_location='North Las Vegas'))
