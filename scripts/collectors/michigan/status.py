"""Michigan permits to install are distinct from site plans, determinations, inspections and utility orders."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='MI':return None
    ds=r['dataset'];s=r['status'];day=date.fromisoformat(r['date']) if r.get('date') else None
    if ds=='Michigan air permits to install' and s=='Approved':return perm('MI:egle-air-pti','unconfirmed','The signed permit documents approval. The state legacy index closed in 2024 and does not establish current validity.',day)
    if ds=='Michigan EGLE water withdrawal determinations':return no('Numbered site-specific determination authorizes the specified withdrawal; it is not a permit-to-install or water-use permit instrument.','decision')
    if ds=='Saline Township advisory committee':return no('Foundation permits were reported but the committee did not identify individual permit numbers or exact issue dates.','observation')
    if ds=='Michigan EGLE air compliance inspections':return no('Dated inspection, not another permit.','observation')
    if ds in ('Saline Township land use proceedings','Michigan Public Service Commission special contracts','Van Buren Township Planning Commission','City of Southfield site-plan review'):
        if s=='Filed' or s=='Submitted':return app()
        return no('Planning, court, or utility-contract action, not construction permit issuance.','observation' if s in ('On agenda','Held') else 'decision')
    return None
