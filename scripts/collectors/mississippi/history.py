"""Mississippi permit history: combines the state and EPA sources below with the curated case file into
output/history/mississippi/history.json. Offline replay only."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, ROOT
import json
from lib.records import save, reconcile
from collectors.mississippi import mdeq_ensearch_permits as mdeq, epa_icis_npdes as icis
def main():
    data=reconcile(list(mdeq.rows()),icis.rows())
    local=collector_data('mississippi','cases.json')
    if local.exists():data.extend(json.loads(local.read_text()))
    save('MS',data)
if __name__=='__main__':main()
