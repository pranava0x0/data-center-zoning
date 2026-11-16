"""Georgia issuer status adapter: an issue date does not establish continued validity."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='GA':return None
    ds=r['dataset']; s=r['status'];day=date.fromisoformat(r['date']) if r.get('date') else None
    if ds=='Georgia EPD issued air permits' and s=='Issued':return perm('GA:epd-air','unconfirmed','Georgia EPD issued this numbered instrument. Continued validity is unverified.',day)
    if ds=='City of Alpharetta commercial permits' and s=='ISSUED':return perm('GA:alpharetta-commercial','unconfirmed','Municipal issuance task completed. No expiration or closure established.',day)
    if ds=='Atlanta Regional Commission DRI reviews':return no('Regional project impact review; not a local development permit.','observation')
    if ds in {'Douglas County Planning and Zoning agendas','City of South Fulton zoning information meeting'}:return app()
    return None
