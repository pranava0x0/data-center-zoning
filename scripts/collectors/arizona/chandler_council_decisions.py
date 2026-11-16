"""City of Chandler City Council minutes of December 11, 2025: PLH24-0046 Price Road Innovation Campus rezoning
denial. Issuer: Chandler City Council."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.arizona.common import *
from pypdf import PdfReader
def download(save):
    k='chandler_minutes';n='chandler-minutes.pdf';save(n,conf[k],lib.net.req(conf[k]))
def rows(b):
    add=b.add
    n='chandler-minutes.pdf';pdf=PdfReader(C/n)
    assert 'PLH24-0046 Price Road Innovation Campus' in pdf.pages[11].extract_text()
    assert 'Motion to deny items 37 and 38 passed unanimously, 7-0' in pdf.pages[37].extract_text()
    assert 'December 11, 2025' in pdf.pages[0].extract_text()
    add('case',n,'PLH24-0046','Price Road Innovation Campus','Rezoning and preliminary development plan','Denied','2025-12-11','Council decision date','Chandler',conf['chandler_minutes']+'#page=38','City Council minutes, pp. 12, 37–38; agenda items 37–38',{'vote':'7–0 to deny both items','case_scope':'Proposed PAD rezoning for data center and additional uses; companion development agreement. One case, not a citywide ban.'},source=conf['chandler_minutes'])
