"""Michigan Public Service Commission case U-21990: DTE / Green Chile Ventures special contracts (application, December 18 decision,
rehearing denial). Issuer: Michigan Public Service Commission."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.michigan.evidence_store import fetch_keys
KEYS=('mpsc','mpsc_order')
def download(m):fetch_keys(m,KEYS)
def rows(m,txt,add):
    add('mpsc_order',1,'On November 3, 2025' if 'On November 3, 2025' in txt('mpsc_order',1) else 'November 3, 2025','mpsc-21990-app','Michigan Public Service Commission special contracts','Saline Township','U-21990','DTE / Green Chile Ventures data center','Electric service and storage contract application','Filed','2025-11-03','application date','MPSC issue brief p. 1; Case U-21990',county='Washtenaw County')
    add('mpsc_order',4,'conditional approval of the special contracts','mpsc-21990-decision','Michigan Public Service Commission special contracts','Saline Township','U-21990','DTE / Green Chile Ventures data center','Power contract decision','Conditionally approved','2025-12-18','commission decision date','MPSC December 18 issue brief pp. 1 and 4',county='Washtenaw County')
    add('mpsc',None,'denied petitions for rehearing','mpsc-21990-rehearing','Michigan Public Service Commission special contracts','Saline Township','U-21990','DTE / Green Chile Ventures data center','Rehearing and reopening requests','Denied','2026-03-27','commission decision date','March 27 commission release; U-21990 paragraph',county='Washtenaw County')
