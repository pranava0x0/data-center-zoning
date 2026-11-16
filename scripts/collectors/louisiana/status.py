"""Louisiana state final decisions, federal cross-checks and local planning events."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import det, day, epa
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='LA':return None
    ds=r['dataset'];d=det(r);when=day(r.get('date'))
    if ds=='EPA ICIS-NPDES permit versions':return epa(r,cutoff,perm,no)
    if ds in ('USACE Vicksburg District regulatory notices','Louisiana DEQ air public notices'):return no('Notice of an application or proposed permit; no issuance.','notice')
    if ds in ('Bossier Parish Police Jury land decisions','Shreveport land use decisions'):return no('Planning action (includes approvals, appeals, and hearing scheduling); tracked separately from permit register.','decision')
    if ds=='Louisiana DEQ quarterly air actions' and r['status']=='Issue Final Decision' and 'initial' in d.get('reported_action','').lower():return perm('LA:ldeq-air','unconfirmed','Initial numbered permit in LDEQ issued report; continued validity not established.',when)
    if ds=='Louisiana DEQ quarterly LPDES actions' and r['status']=='New Coverage':
        end=day(d.get('expiration_date'));effective=day(d.get('effective_date'));cross=d.get('epa_crosscheck',{});e=cross.get('details',{});fed_end=day(e.get('expiration_date'));fed_eff=day(e.get('effective_date'))
        if e.get('version')=='0' and end and end==fed_end and cross.get('status')=='EXP' and end<cutoff:return perm('LA:npdes','historical','Explicit EPA EXP and matching state expiration date.',when)
        if e.get('version')=='0' and end and end==fed_end and effective and fed_eff and max(effective,fed_eff)<=cutoff<=end and cross.get('status')=='EFF':return perm('LA:npdes','active','EPA effective coverage and LDEQ/ICIS permit terms both span cutoff; expiration agrees.',when)
        return perm('LA:npdes','unconfirmed','LDEQ issued coverage; conflicting or insufficient sources for current validity.',when)
    return None
