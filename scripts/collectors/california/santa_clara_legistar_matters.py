"""City of Santa Clara: Legistar matters and histories (webapi.legistar.com/v1/santaclara) for site-specific data center land-use matters. Issuer: City of Santa Clara."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.california.evidence_store import cf, leg, legistar_rows
SC='https://webapi.legistar.com/v1/santaclara/matters'
def download_tasks():return [lambda:leg('sc',SC,cf['city_matter_ids'])]
def rows(ctx):legistar_rows(ctx,'sc','Santa Clara',SC,cf['city_matter_ids'])
