"""Indiana Department of Environmental Management (Office of Air Quality and Office of Water Quality): air permit decisions,
notices and Waterways decisions, cited from pinned PDFs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from collectors.indiana.evidence_store import DREF, INDEX, REVIEW, get, read, j, make_adder, review_rows
def hobart(row):return bool(row.get('verified_scan'))
def download():
    """Re-fetch any missing pinned document (the IDEM notice index and every pinned decision not cited from Hobart minutes);
    refuse bytes that differ from the pinned hash."""
    cited={row['doc'] for row in j(REVIEW) if hobart(row)}
    for ref in [j(INDEX),*(v for k,v in j(DREF).items() if k not in cited)]:
        try:read(ref)
        except FileNotFoundError:
            recovered=get(ref['url'],ref['ext'])
            if recovered['sha256']!=ref['sha256']:raise ValueError('Historical document changed; review refreshed bytes before replacing pinned citation: '+ref['url'])
def rows(c,m,add):
    review_rows(c,m,add,lambda row:not hobart(row))
