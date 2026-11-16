"""Small file and hashing helpers shared by collectors (JSON, gzip snapshots, SHA-256)."""
import gzip, hashlib, json
from pathlib import Path


def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_text())
def pack(p,o):p.write_bytes(gzip.compress(json.dumps(o,sort_keys=True).encode(),mtime=0))
def unpack(p):return json.loads(gzip.decompress(p.read_bytes()))
