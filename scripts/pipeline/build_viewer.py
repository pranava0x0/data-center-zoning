"""Pack the atlas into the original index.html. No runtime requests, imports, or eval."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import base64, gzip, json, re, lzma, argparse, hashlib, csv
from pathlib import Path
import lib.discovery as c
V=c.R/'viewer'
def assigned(path):
    # Source exports are generated JSON assignments, never executable user content.
    text=path.read_text().strip();_,value=text.split('=',1)
    return json.loads(value.rstrip(';'))
def pack(name,data,compact=False):
    b=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()
    raw=lzma.compress(b,format=lzma.FORMAT_ALONE,preset=6) if compact else gzip.compress(b,compresslevel=9,mtime=0)
    if not compact:raw=raw[:9]+b'\xff'+raw[10:]  # Stable gzip OS byte across Python/macOS/Linux.
    codec='lzma' if compact else 'gzip'
    encoded=base64.b64encode(raw).decode()
    return f'<script id="pack-{name}" type="application/octet-stream" data-codec="{codec}">{encoded}</script>'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--snapshot-geography',action='store_true');args=ap.parse_args()
    html=(c.R/'templates/atlas.html').read_text()
    html=re.sub(r'<script defer src="[^"]+"></script>','',html)
    html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(V/'style.css').read_text()+'</style>')
    index=(V/'history-index.js').read_text().split(';window.PERMIT_CHUNKS')[0].split('=',1)[1]
    hi=json.loads(index);rules=assigned(V/'data.js')
    with (c.OUT/'priority_localities.csv').open() as f:priority=[r for r in csv.DictReader(f) if r['group']!='statistical place']
    matched=sum(int(r['reviewed_local_register_rows'])>0 for r in priority)
    hi['coverage']={'numerator':matched,'denominator':len(priority),'percent':round(100*matched/len(priority),1)}
    from pipeline.national_map import national
    if args.snapshot_geography:
        receipt=json.loads((c.R/'data/publication/geography-receipt.json').read_text());b=(c.R/receipt['path']).read_bytes()
        if hashlib.sha256(b).hexdigest()!=receipt['sha256']:raise ValueError('Display geometry snapshot changed')
        snapshot=json.loads(gzip.decompress(b));geo=snapshot['geometry'];rules['geo']=snapshot['geo_labels']
    else:
        geo=national(rules,hi,assigned(V/'geography.js'))
    bundles=[pack('geo',geo),pack('rules',rules),pack('index',hi),pack('telecom',assigned(V/'telecom.js'))]
    for state in hi['areas']:
        for suffix in ('','-details'):
            bundles.append(pack(state+suffix,assigned(V/f'history-{state}{suffix}.js'),True))
    unpack="""function unpack(name){const tag=document.getElementById('pack-'+name);if(!tag)throw new Error('Missing atlas data: '+name);const b=atob(tag.textContent.trim()),bytes=new Uint8Array(b.length);for(let i=0;i<b.length;i++)bytes[i]=b.charCodeAt(i);const decoded=tag.dataset.codec==='lzma'?LZMA.decompress(bytes):pako.ungzip(bytes);return JSON.parse(typeof decoded==='string'?decoded:new TextDecoder().decode(Uint8Array.from(decoded)))}window.TELECOM=unpack('telecom');window.ATLAS=unpack('rules');window.GEOGRAPHY=unpack('geo');window.HISTORY_INDEX=unpack('index');window.PERMIT_CHUNKS={};window.PERMIT_DETAILS={};"""
    code=['/* '+(V/'vendor/pako-LICENSE').read_text().replace('*/','* /')+' */\n'+(V/'vendor/pako_inflate.min.js').read_text(),'/* '+(V/'vendor/lzma-LICENSE').read_text().replace('*/','* /')+' */\n'+(V/'vendor/lzma-d-min.js').read_text(),unpack]+[(V/name).read_text() for name in ['rule-card.js','map.js','telecom-ui.js','app.js']]
    scripts=''.join('<script>'+x.replace('</script','<\\/script')+'</script>' for x in code)
    html=html.replace('</body>',''.join(bundles)+scripts+'</body>');(V/'index.html').write_text(html)
    print(f'Standalone atlas: {len(html.encode()):,} bytes; {len(hi["areas"])} state permit registers')
if __name__=='__main__':main()
