"""One HTTP GET for every live collector: robots.txt, per-host spacing, retry, size cap, one user agent.

Offline replays never call this. Collectors keep their own archive layout; only the transport is shared.

    import lib.net as fetch
    body = fetch.get(url)                          # bytes
    body = fetch.get(url, params={'f': 'json'})    # appends ?f=json in the given key order
    data = fetch.get_json(url, params)             # raises on an ArcGIS/Socrata {"error": ...} body

robots.txt follows RFC 9309: 4xx means no rules, 5xx or an unreachable file means do not fetch. A crawl delay is
honored by sleeping (up to MAX_DELAY per request); a longer one stops the run instead of hammering the host.
"""
import json, os, subprocess, time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from http.cookiejar import CookieJar
from typing import NamedTuple
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen
from urllib.robotparser import RobotFileParser

AGENT = 'OrdinanceAtlas/1.0 (public-source research)'
TOKEN = 'OrdinanceAtlas'
LIMIT = 80 * 1024 ** 2
MIN_SPACING = 0.25
MAX_DELAY = 30
RETRY_STATUS = {429, 500, 502, 503, 504}
# Hosts whose robots.txt blocks crawlers wholesale but which serve individual, pinned public files for direct
# download. Each entry needs a reason; nothing else bypasses robots.txt.
ROBOTS_EXEMPT = {
    'raw.githubusercontent.com': 'Pinned-commit IM3 data-center atlas file; GitHub serves raw files for direct download.',
}
_robots, _last = {}, {}
# ATLAS_REFETCH=1 (set by `jurisdiction.py refresh`) makes collectors re-download sources they already archived,
# instead of only filling gaps. Archives are content-addressed, so earlier bytes stay on disk for comparison.
REFETCH = os.environ.get('ATLAS_REFETCH') == '1'
SEEN = set()


class Refused(ValueError):
    """The host's robots.txt or crawl delay does not allow this request."""


def _host(url):
    u = urlsplit(url)
    if u.scheme not in ('http', 'https') or not u.hostname:
        raise ValueError('Expected an http(s) URL: ' + url)
    return u.scheme + '://' + u.netloc, u.hostname


def _curl_robots(origin):
    """robots.txt over curl, for hosts whose TLS urllib can't negotiate. Returns (status, text)."""
    out = subprocess.run(['curl', '-LsS', '--max-time', '20', '-A', AGENT, '-w', '\n%{http_code}', origin + '/robots.txt'],
                         capture_output=True, text=True)
    if out.returncode:
        return 0, ''
    body, _, code = out.stdout.rpartition('\n')
    return int(code or 0), body


def _rules(origin, transport='urllib'):
    key = (origin, transport == 'curl')
    if key not in _robots:
        rp = RobotFileParser()
        if transport == 'curl':
            code, text = _curl_robots(origin)
            if code == 200:
                rp.parse(text.splitlines())
            elif 400 <= code < 500:
                rp.parse([])
            else:
                rp.parse(['User-agent: *', 'Disallow: /'])
        else:
            try:
                with urlopen(Request(origin + '/robots.txt', headers={'User-Agent': AGENT}), timeout=20) as r:
                    rp.parse(r.read(512000).decode('utf8', 'replace').splitlines())
            except HTTPError as e:
                if 400 <= e.code < 500:
                    rp.parse([])
                else:
                    rp.parse(['User-agent: *', 'Disallow: /'])
            except (URLError, TimeoutError, OSError):
                rp.parse(['User-agent: *', 'Disallow: /'])
        _robots[key] = rp
    return _robots[key]


def polite(url, robots=True, transport='urllib'):
    """Check robots.txt and space requests to one host. Raises Refused."""
    origin, hostname = _host(url)
    delay = MIN_SPACING
    if robots and hostname not in ROBOTS_EXEMPT:
        rp = _rules(origin, transport)
        if not rp.can_fetch(TOKEN, url):
            raise Refused('robots.txt disallows ' + url)
        delay = max(delay, rp.crawl_delay(TOKEN) or rp.crawl_delay('*') or 0)
    if delay > MAX_DELAY:
        raise Refused(f'crawl delay {delay}s on {origin} exceeds {MAX_DELAY}s')
    wait = _last.get(origin, -1e9) + delay - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last[origin] = time.monotonic()


def with_params(url, params=None):
    return url + ('?' + urlencode(params) if params else '')


def wire(url):
    """Escape spaces, control and non-ASCII characters for the request line; existing %-escapes are kept.
    Archives key on the URL as the collector wrote it, so this only affects what goes over the network."""
    return quote(url, safe=":/?&=;%$+@,!~*'()[]-._#")


class Response(NamedTuple):
    body: bytes
    url: str        # final URL after redirects
    mime: str       # Content-Type without parameters ('' for curl)
    status: int

    @property
    def text(self):
        return self.body.decode('utf-8', 'replace')


def request(url, params=None, *, data=None, json_body=None, headers=None, timeout=120, retries=3, limit=LIMIT,
            robots=True, transport='urllib', opener=None):
    """GET, or POST when `data` (bytes or dict -> form-encoded) or `json_body` is given. Returns Response.
    Retries network errors and 429/5xx; other 4xx raise immediately. Search POSTs are treated as idempotent."""
    url = with_params(url, params)
    hdrs = {'User-Agent': AGENT, **(headers or {})}
    if json_body is not None:
        data = json.dumps(json_body).encode()
        hdrs.setdefault('Content-Type', 'application/json')
    elif isinstance(data, dict):
        data = urlencode(data).encode()
        hdrs.setdefault('Content-Type', 'application/x-www-form-urlencoded')
    for attempt in range(retries):
        polite(url, robots, transport)
        try:
            if transport == 'curl':
                # Some public servers need a TLS stack urllib lacks; macOS curl verifies certificates.
                if data is not None:
                    raise ValueError('curl transport is GET-only')
                b = subprocess.run(['curl', '--fail', '-LsS', '--max-filesize', str(limit), '--max-time', str(timeout),
                                    '-A', AGENT, wire(url)], check=True, capture_output=True).stdout
                res = Response(b, url, '', 200)
            else:
                with (opener.open if opener else urlopen)(Request(wire(url), data=data, headers=hdrs), timeout=timeout) as r:
                    b = r.read(limit + 1)
                    res = Response(b, r.url, r.headers.get_content_type(), r.status)
            if len(b) > limit:
                raise ValueError(f'Response exceeds {limit} bytes: {url}')
            return res
        except HTTPError as e:
            # Some state servers (e.g. Alaska's public-notice site) answer 403 intermittently behind a firewall.
            # robots.txt already allowed the URL, so one slower retry is reasonable; a persistent 403 still fails.
            if e.code == 403 and attempt == 0 and retries > 1:
                time.sleep(5)
                continue
            if e.code not in RETRY_STATUS or attempt == retries - 1:
                raise
        except (URLError, TimeoutError, ConnectionError, subprocess.CalledProcessError):
            if attempt == retries - 1:
                raise
        time.sleep(2 * (attempt + 1))


def get(url, params=None, *, with_url=False, **kw):
    """Response bytes (and the final URL if with_url)."""
    r = request(url, params, **kw)
    return (r.body, r.url) if with_url else r.body


class Session:
    """Cookie-keeping session for form-driven search pages (ASP.NET postbacks). Same politeness rules."""
    def __init__(self):
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def get(self, url, params=None, **kw):
        return request(url, params, opener=self.opener, **kw)

    def post(self, url, data, **kw):
        return request(url, data=data, opener=self.opener, **kw)


def get_json(url, params=None, **kw):
    o = json.loads(get(url, params, **kw))
    if isinstance(o, dict) and 'error' in o:
        raise ValueError(f"{url}: {o['error']}")
    return o


def download(url, path, *, timeout=300, retries=3, limit=4 * 1024 ** 3, robots=True):
    """Stream a large file (e.g. a national ZIP) to `path` without holding it in memory. Returns bytes written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.part')
    for attempt in range(retries):
        polite(url, robots)
        try:
            n = 0
            with urlopen(Request(wire(url), headers={'User-Agent': AGENT}), timeout=timeout) as r, tmp.open('wb') as f:
                while chunk := r.read(1 << 20):
                    n += len(chunk)
                    if n > limit:
                        raise ValueError(f'Download exceeds {limit} bytes: {url}')
                    f.write(chunk)
            tmp.replace(path)
            return n
        except HTTPError as e:
            if e.code not in RETRY_STATUS or attempt == retries - 1:
                raise
        except (URLError, TimeoutError, ConnectionError):
            if attempt == retries - 1:
                raise
        time.sleep(2 * (attempt + 1))


def req(url, params=None):
    """GET with a 150 s timeout (the Texas-lineage collectors' default)."""
    return get(url, params, timeout=150)


def get_simple(u):
    """GET with a 120 s timeout (the EPA-lineage collectors' default)."""
    return get(u, timeout=120)


def query(base, **p):
    """base?k=v in the given key order."""
    return base + '?' + urlencode(p)
