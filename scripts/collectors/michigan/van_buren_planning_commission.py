"""Van Buren Township Planning Commission, Wayne County: Project Cannoli (case 25-041) minutes and packets, plus the Wayne County
Commission statement. Issuer: Charter Township of Van Buren."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.michigan.evidence_store import fetch_keys
KEYS=('wayne','vbt_feb','vbt_index','vbt_oct')
def download(m):fetch_keys(m,KEYS)
def rows(m,txt,add):
    assert 'Motion Carried.' in txt('vbt_feb',20)
    add('vbt_feb',20,'preliminary site plan approval with conditions','vbt-25-041-prelim','Van Buren Township Planning Commission','Van Buren Township','25-041','Project Cannoli','Preliminary site plan','Approved with conditions','2026-02-11','commission decision date','Case 25-041, Feb 11 minutes pp. 1 and 20; roll call 5–2',county='Wayne County')
    if 'sha256' in m.get('vbt_oct',{}) and 'Cannoli' in txt('vbt_oct',1):
        add('vbt_oct',1,'Cannoli','vbt-25-041-final-agenda','Van Buren Township Planning Commission','Van Buren Township','25-041','Project Cannoli','Final site plan on agenda','On agenda','2026-10-14','meeting scheduled','October 14 agenda p. 1; final decision not established by agenda',county='Wayne County')
