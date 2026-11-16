"""New York permit history: combines the NYC Department of Buildings, DEC air permit and local board decision sources
into output/history/new_york/history.json, data/history/new_york/cases.json and data/history/new_york/validation.json. Offline replay by default;
--refresh re-downloads every source."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import json
from collectors.new_york.source_store import BIS,BP,NJ,NOW,EL,ASF,TV,read
from collectors.new_york import nyc_dob_permits, dec_air_permits
SOURCES=(nyc_dob_permits, dec_air_permits)
def build():
    from lib.records import save
    from collectors.new_york.decisions import records
    local=records()
    (collector_data('new_york','cases.json')).write_text(json.dumps(local,indent=2)+'\n')
    rows=nyc_dob_permits.rows()+dec_air_permits.rows()+local
    save('NY',rows)
    p=collector_data('new_york','validation.json');v=json.loads(p.read_text())
    v['cutoff_inclusive']='2026-11-15'
    v['source_counts_before_joins']={ds:read(ds)['count'] for ds in (BIS,BP,NJ,NOW,EL,ASF,TV)}
    v['source_identifiers']='City: jobs by job and document; BIS permit by printed job/document/type; DOB NOW permit by work_permit, sequence is an issue/renewal; state air by permit_id. Electrical job numbers never treated as verified independently numbered permits.'
    v['source_event_date_range']=[min(r['date'] for r in rows),max(r['date'] for r in rows)]
    p.write_text(json.dumps(v,indent=2)+'\n')
if __name__=='__main__':
    if '--refresh' in sys.argv:
        for s in SOURCES:s.download()
    build()
