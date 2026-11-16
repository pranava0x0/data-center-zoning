"""City of Norwalk Zoning Commission site plan surety decisions for the 10 Norden Place data recovery center
(pinned extracts from municipal minutes). Issuer: City of Norwalk Zoning Commission."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, D
import json
def download(A):pass  # pinned extract in data/history/connecticut/norwalk.json; nothing is fetched
def rows(A,add):
 for a in json.loads((collector_data('connecticut','norwalk.json')).read_text()):
  add('Norwalk site plan surety decisions','8-11SPR','FPG Norden DC — 10 Norden Place data recovery center','Norwalk','Site plan surety release',a['status'],a['date'],'Effective date of commission action',a['url'],a['locator'],issuer='City of Norwalk Zoning Commission',evidence=a['evidence'],archive='data/history/connecticut/norwalk.json',evidence_mode='Primary municipal minutes via public web index; pinned extract.')
