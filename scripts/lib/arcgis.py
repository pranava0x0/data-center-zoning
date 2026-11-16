"""ArcGIS FeatureServer/MapServer paging with a completeness proof.

Collectors keep their own storage. They pass `get(url, **query) -> ref` (fetch and archive one response) and
`read(ref) -> dict` (load an archived response). Query parameters are sent in a fixed order, so the same query
always produces the same URL and the same archive key.

    p = arcgis.pull(get, read, layer_url, where, 'OBJECTID,NAME', batch=150)
    rows = arcgis.records(read, p)          # re-verifies the archived pages offline
"""


class Incomplete(ValueError):
    """A page or the archived set does not match the object IDs the layer reported."""


def oid_field(get, read, url):
    """The layer's object-ID field name, from its metadata. Returns (name, metadata ref)."""
    meta = get(url + '?f=json')
    return next(f['name'] for f in read(meta)['fields'] if f['type'] == 'esriFieldTypeOID'), meta


def ids(get, read, url, where, *, sort=True, id_params=None):
    ref = get(url + '/query', where=where, returnIdsOnly='true', **(id_params or {}))
    raw = read(ref).get('objectIds') or []
    found = sorted(raw) if sort else list(raw)
    if len(set(found)) != len(found):
        raise Incomplete('Duplicated object IDs from ' + url)
    return ref, found


def pull(get, read, url, where, fields, oid='OBJECTID', batch=150, *, sort=True, id_params=None, page_params=None,
         on_page=None):
    """Fetch every matching feature in object-ID slices. Each slice must return exactly the IDs requested.

    `id_params` / `page_params` append extra query keys after the standard ones (e.g. f='json' last), so a
    collector's existing URLs, and therefore its archive keys, stay byte-identical. `sort=False` keeps the
    server's ID order for collectors whose slices were cut that way. `on_page(ref, rows)` sees each page."""
    ids_ref, found = ids(get, read, url, where, sort=sort, id_params=id_params)
    pages = []
    for i in range(0, len(found), batch):
        want = found[i:i + batch]
        ref = get(url + '/query', objectIds=','.join(map(str, want)), outFields=fields, returnGeometry='false',
                  **(page_params or {}))
        d = read(ref)
        got = sorted(x['attributes'][oid] for x in d['features'])
        if got != sorted(want) or d.get('exceededTransferLimit'):
            raise Incomplete(f'Truncated page {i // batch} from {url}')
        if on_page:
            on_page(ref, [x['attributes'] for x in d['features']])
        pages.append(ref)
    return dict(ids=ids_ref, batches=pages, where=where, oid=oid)


def records(read, pulled, with_ref=False):
    """All archived features; fails if the pages no longer add up to the reported ID set."""
    want = read(pulled['ids']).get('objectIds') or []
    oid = pulled.get('oid', 'OBJECTID')
    rows = [(x['attributes'], b) for b in pulled['batches'] for x in read(b)['features']]
    if len(rows) != len(want) or {a[oid] for a, _ in rows} != set(want):
        raise Incomplete('Archived pages do not match the reported object IDs')
    return rows if with_ref else [a for a, _ in rows]


# Two storage-specific wrappers kept verbatim from the collectors that introduced them.
import json, sys
arcgis = sys.modules[__name__]  # the moved bodies call arcgis.pull / arcgis.records
from lib.net import get_simple as get, query
from lib.files import pack


def arcstore(store,url,where,out,batch=50):
    oid,meta=arcgis.oid_field(store.get,store.read,url)
    p=arcgis.pull(store.get,store.read,url,where,','.join([oid]+out),oid,batch)
    return dict(url=url,where=where,oid=oid,meta=meta,ids=p['ids'],batches=p['batches'])
def snapshot(base,where,fields,p):
    def g(u,**q):
        link=query(u,**q,f='json');return dict(url=link,body=json.loads(get(link)))
    r=arcgis.pull(g,lambda ref:ref['body'],base,where,','.join(fields),batch=125)
    ids=r['ids']['body']['objectIds'] or []
    pack(p,dict(count=len(ids),ids_url=r['ids']['url'],urls=[b['url'] for b in r['batches']],rows=arcgis.records(lambda ref:ref['body'],r)))
