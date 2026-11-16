"""City of Hobart Plan Commission minutes (scanned PDFs verified by OCR manifest) for data center site plan decisions."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.indiana.evidence_store import DREF, INDEX, REVIEW, get, read, j, make_adder, review_rows
def hobart(row):return bool(row.get('verified_scan'))
def download():
    """Re-fetch any missing pinned minutes; refuse bytes that differ from the pinned hash."""
    for ref in [j(DREF)[row['doc']] for row in j(REVIEW) if hobart(row)]:
        try:read(ref)
        except FileNotFoundError:
            recovered=get(ref['url'],ref['ext'])
            if recovered['sha256']!=ref['sha256']:raise ValueError('Historical document changed; review refreshed bytes before replacing pinned citation: '+ref['url'])
def rows(c,m,add):
    review_rows(c,m,add,hobart)
