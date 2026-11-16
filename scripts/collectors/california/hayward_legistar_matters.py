"""City of Hayward: Legistar matters and histories (webapi.legistar.com/v1/hayward) for site-specific data center land-use matters. Issuer: City of Hayward."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.california.evidence_store import cf, leg, legistar_rows
HAY='https://webapi.legistar.com/v1/hayward/matters'
def download_tasks():return [lambda:leg('hay',HAY,cf['hayward_matter_ids'])]
def rows(ctx):legistar_rows(ctx,'hay','Hayward',HAY,cf['hayward_matter_ids'])
