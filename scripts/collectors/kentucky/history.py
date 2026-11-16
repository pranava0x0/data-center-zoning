"""Reusable state and local case-source adapter, with exact page-level guardrails and an offline default."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.config_collector import run, cli
from lib.records import reviewed
import lib.net as netfetch
import argparse, io, collections, datetime as dt, re
from pypdf import PdfReader
from lib.archive import Store
from lib.paths import R
from lib.files import j
from lib.geo import rank, geofetch
from lib.text import htmltext, slug
from lib.arcgis import arcstore
import lib.discovery as collect
from functools import lru_cache
if __name__=='__main__':cli('KY','21')
# records are configuration, not code: this helper preserves a consistent proof-review format in new cases.
