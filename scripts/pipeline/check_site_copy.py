"""Run the permittingreform writing and design checks on the material the atlas renders."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import html, json, re, subprocess, sys
from pathlib import Path
from html.parser import HTMLParser
import lib.discovery as c
class Reader(HTMLParser):
    def __init__(self):super().__init__();self.lines=[]
    def handle_data(self,data):
        if data.strip():self.lines.append(data.strip())
def main():
    htmlfile=c.R/'templates/atlas.html';doc=Reader();doc.feed(htmlfile.read_text())
    texts=list(doc.lines)
    for r in c.read(c.OUT/'rules.json',[]):
        texts.extend([r.get('reader_title',''),r.get('reader_brief') or r['summary']])
    contents='\n\n'.join(s for s in texts if s)
    artifact=c.OUT/'site-copy.md';artifact.write_text(contents+'\n')
    # Literal regression checks for text the owner found confusing. Search UI source too:
    # official extracts, portal status values, audit docs and pinned source files stay verbatim.
    public=contents+'\n'+'\n'.join((c.R/'viewer'/f).read_text() for f in ['app.js','rule-card.js','map.js'])
    for phrase in ['source checked','backed by a reviewed source','permitted in the ram district','screened only','field edition']:
        if phrase in public.lower():raise ValueError('Unclear site copy: '+phrase)
    base=c.R/'scripts/pipeline/copy_checks'
    for name,args in [('writing',['--profile','public-copy',str(artifact)]),('design',[str(htmlfile),str(c.R/'viewer/style.css')])]:
        p=subprocess.run([sys.executable,str(base/('slop_'+name+'.py')),'--no-review','--json',str(c.OUT/(name+'-check.json')),*args],cwd=c.R,capture_output=True,text=True)
        if p.returncode:
            print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)
        print(name+': '+p.stdout.strip().splitlines()[-1])
if __name__=='__main__':main()
