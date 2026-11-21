"""Archive one official source for the telecom atlas: python3 telecom_fetch.py ID URL [ext] [official-title].

Uses lib/net.py (robots.txt, spacing, retry). Writes data/telecom/evidence/ID.ext and a sources.json receipt.
HTML titles are extracted when available; PDF or untitled sources need an explicit title.
Never used by the offline build."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import hashlib, json, re
from html import unescape
from datetime import datetime, timezone
import lib.net as net

R = Path(__file__).resolve().parents[4]
D = R / 'data/telecom'


def archive(key, url, ext='html', title=None):
    body = net.get(url)
    if title is None and ext=='html':
        match=re.search(r'<title[^>]*>(.*?)</title>',body.decode('utf-8',errors='replace'),re.I|re.S)
        title=unescape(re.sub(r'<[^>]+>','',match.group(1))).strip() if match else None
    if not title:
        raise ValueError('An official source title is required for this archive')
    path = D / 'evidence' / f'{key}.{ext}'
    path.write_bytes(body)
    sources = json.loads((D / 'sources.json').read_text())
    sources[key] = dict(url=url, title=title, capture_method='HTTP response', path=str(path.relative_to(R)), sha256=hashlib.sha256(body).hexdigest(), bytes=len(body), content_type={'pdf': 'application/pdf'}.get(ext, 'text/html'), retrieved_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(), status='retrieved')
    (D / 'sources.json').write_text(json.dumps(sources, indent=2, ensure_ascii=False) + '\n')
    return sources[key]


if __name__ == '__main__':
    print(archive(*sys.argv[1:]))
