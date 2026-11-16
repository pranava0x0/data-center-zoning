"""Nebraska permit history: combines the Lincoln building permit, DWEE air file and local permit report sources below
into output/history/nebraska/history.json and data/history/nebraska/validation.json. Offline replay by default; --refresh re-downloads
every source; --fetch-lincoln previews the Lincoln layers."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import sys, json
from lib.records import CUT, save
from collectors.nebraska import lincoln_building_permits as lincoln, dwee_air_files as dwee, local_permit_reports as local
from lib.files import unpack
from concurrent.futures import ThreadPoolExecutor
SOURCES=(lincoln, dwee)
def make():
 lin,candidates,distinct=lincoln.rows();air,stats,duplicates,held=dwee.rows();rows=lin+air+local.rows()
 # Full replacement, not a partial revision. Dates below are the later issued instruments' agency document dates.
 superseded={'CP16-033':('CP17-041','2017-11-21'),'CP17-041':('CP18-024','2018-05-15'),'CP18-024':('CP18-041','2018-10-15'),'CP18-041':('CP19-021','2020-03-31'),'CP19-021':('CP20-033','2021-10-26'),'CP20-033':('CP22-008','2023-03-31'),'CP22-008':('CP24-020','2025-02-14'),'CP19-019':('CP21-007','2022-02-08'),'CP24-016':('CP25-009','2026-01-13'),'OP21S1-036':('OP24S1-017','2025-05-27'),'OP22M2-055':('OP24S1-017','2025-05-27')}
 by={(r['details'].get('facility_id'),r['record_no']):r for r in rows if r['status']=='DEQ Issued Permit'}
 for (fid,n),r in by.items():
    if n not in superseded:continue
    later,dt=superseded[n];other=by.get((fid,later))
    if not other or other['date']!=dt:raise ValueError('Unverified supersession '+n)
    r['details'].update(superseded_by=later,supersession_date=dt,supersession_source_id=other['id'])
 save('NE',rows);v=collector_data('nebraska','validation.json');r=json.loads(v.read_text());r.update(cutoff=CUT,ecm_all_air_documents_per_facility=stats,ecm_duplicate_observations=duplicates,ecm_issued_unverified_numbers=held,lincoln_candidates_each_layer=candidates,lincoln_distinct_numbers=distinct);v.write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__' and '--fetch-lincoln' in sys.argv:
 with ThreadPoolExecutor(max_workers=3) as t:list(t.map(lincoln.layer,range(6)))
 for i in range(6):print(i,[(v['PermNo'],v['CurrStatus'],v['Issued'],v['DescWork'][:80]) for v in unpack(lincoln.D/('lincoln-'+str(i)+'.json.gz'))['records']][:9])
if __name__=='__main__' and '--fetch-lincoln' not in sys.argv:
 if '--refresh' in sys.argv:
    lincoln.D.mkdir(parents=True,exist_ok=True)
    for s in SOURCES:s.download()
 make()
