"""Pack the atlas into the original index.html. No runtime requests, imports, or eval."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import base64, gzip, json, re, lzma
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
    codec='lzma' if compact else 'gzip'
    encoded=base64.b64encode(raw).decode()
    return f'<script id="pack-{name}" type="application/octet-stream" data-codec="{codec}">{encoded}</script>'
def main():
    html=(c.R/'templates/atlas.html').read_text()
    html=re.sub(r'<script defer src="[^"]+"></script>','',html)
    html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(V/'style.css').read_text()+'</style>')
    index=(V/'history-index.js').read_text().split(';window.PERMIT_CHUNKS')[0].split('=',1)[1]
    hi=json.loads(index);rules=assigned(V/'data.js')
    from pipeline.national_map import national
    geo=national(rules,hi,assigned(V/'geography.js'))
    bundles=[pack('geo',geo,True),pack('rules',rules,True),pack('index',hi)]
    for state in hi['areas']:
        for suffix in ('','-details'):
            bundles.append(pack(state+suffix,assigned(V/f'history-{state}{suffix}.js'),True))
    unpack="""function unpack(name){const tag=document.getElementById('pack-'+name);if(!tag)throw new Error('Missing atlas data: '+name);const b=atob(tag.textContent.trim()),bytes=new Uint8Array(b.length);for(let i=0;i<b.length;i++)bytes[i]=b.charCodeAt(i);const decoded=tag.dataset.codec==='lzma'?LZMA.decompress(bytes):pako.ungzip(bytes);return JSON.parse(typeof decoded==='string'?decoded:new TextDecoder().decode(Uint8Array.from(decoded)))}window.ATLAS=unpack('rules');window.GEOGRAPHY=unpack('geo');window.HISTORY_INDEX=unpack('index');window.PERMIT_CHUNKS={};window.PERMIT_DETAILS={};"""
    code=['/* '+(V/'vendor/pako-LICENSE').read_text().replace('*/','* /')+' */\n'+(V/'vendor/pako_inflate.min.js').read_text(),'/* '+(V/'vendor/lzma-LICENSE').read_text().replace('*/','* /')+' */\n'+(V/'vendor/lzma-d-min.js').read_text(),unpack]+[(V/name).read_text() for name in ['rule-card.js','map.js','app.js']]
    scripts=''.join('<script>'+x.replace('</script','<\\/script')+'</script>' for x in code)
    html=html.replace('</body>',''.join(bundles)+scripts+'</body>');(V/'index.html').write_text(html)
    print(f'Standalone atlas: {len(html.encode()):,} bytes; {len(hi["areas"])} state permit registers')
if __name__=='__main__':main()
