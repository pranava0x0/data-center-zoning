"""Project paths. Every module resolves files from here, not from its own location.

Published series live under output/history/ and each collector's own inputs and by-products under data/history/,
both mirroring the collector's path under scripts/collectors/. Callers never build those names by hand:

  series_path('tx')                          -> output/history/texas/history.json   (path column of data/history/series.csv)
  collector_data('texas', 'validation.json') -> data/history/texas/validation.json
  state_folder('TX')                         -> 'texas'
"""
import csv
from functools import lru_cache
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
R = ROOT
D = ROOT / 'data'
OUT = ROOT / 'output'
CACHE = ROOT / 'cache/history'
SERIES_CSV = D / 'history/series.csv'

# State and territory codes -> the folder name used under scripts/collectors/ and data/history/.
STATE_FOLDERS = {
    'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 'AR': 'arkansas', 'CA': 'california', 'CO': 'colorado',
    'CT': 'connecticut', 'DE': 'delaware', 'DC': 'district_of_columbia', 'FL': 'florida', 'GA': 'georgia',
    'HI': 'hawaii', 'ID': 'idaho', 'IL': 'illinois', 'IN': 'indiana', 'IA': 'iowa', 'KS': 'kansas',
    'KY': 'kentucky', 'LA': 'louisiana', 'ME': 'maine', 'MD': 'maryland', 'MA': 'massachusetts',
    'MI': 'michigan', 'MN': 'minnesota', 'MS': 'mississippi', 'MO': 'missouri', 'MT': 'montana',
    'NE': 'nebraska', 'NV': 'nevada', 'NH': 'new_hampshire', 'NJ': 'new_jersey', 'NM': 'new_mexico',
    'NY': 'new_york', 'NC': 'north_carolina', 'ND': 'north_dakota', 'OH': 'ohio', 'OK': 'oklahoma',
    'OR': 'oregon', 'PA': 'pennsylvania', 'RI': 'rhode_island', 'SC': 'south_carolina', 'SD': 'south_dakota',
    'TN': 'tennessee', 'TX': 'texas', 'UT': 'utah', 'VT': 'vermont', 'VA': 'virginia', 'WA': 'washington',
    'WV': 'west_virginia', 'WI': 'wisconsin', 'WY': 'wyoming', 'PR': 'puerto_rico', 'GU': 'guam',
    'AS': 'american_samoa', 'MP': 'northern_mariana_islands', 'VI': 'us_virgin_islands',
}


def state_folder(code):
    return STATE_FOLDERS[code.upper()]


@lru_cache(maxsize=None)
def series_registry():
    """{series: {'state': 'TX', 'path': 'history/texas/history.json'}} from data/history/series.csv (paths relative to output/)."""
    with SERIES_CSV.open() as f:
        return {r['series']: dict(state=r['state'], path=r['path']) for r in csv.DictReader(f)}


def series_path(series):
    """Absolute path of a published series file. The series must be registered in data/history/series.csv."""
    try:
        rel = series_registry()[series]['path']
    except KeyError:
        raise KeyError(f"series {series!r} is not in data/history/series.csv; register it with pipeline/register_release.py") from None
    return OUT / rel


def series_paths(prefix=''):
    """Paths of every registered series whose name starts with prefix, in registry order (files may not exist yet)."""
    return [OUT / v['path'] for s, v in series_registry().items() if s.startswith(prefix)]


def collector_data(folder, name):
    """data/history/<collector folder>/<name>. The folder is the collector's path under scripts/collectors/
    (a state's history.py uses the state folder). The directory is created so writers can save straight away."""
    p = D / 'history' / folder / name
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
