"""Version the tribal-government roster and U.S. minor outlying area references."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, xml.etree.ElementTree as ET
from lib.url_archive import Archive
import lib.discovery as c
D=c.R/'data/national';FR='https://www.federalregister.gov/documents/full_text/xml/2026/01/30/2026-01899.xml';DOI='https://www.doi.gov/oia/islands/politicatypes'
def main(fetch):
 a=Archive('nationalextras',fetch,owner='pipeline/national_authorities');x=ET.fromstring(a.get(FR)[0]);names=[' '.join(''.join(n.itertext()).split()) for n in x.findall('.//EXTRACT/FP')]
 if len(set(names))!=577 or '575 Tribal entities' not in ''.join(x.itertext()):raise ValueError('Changed Federal Register list of tribal governments')
 c.dump(D/'tribal_governments.json',[dict(name=n,id='BIA-'+c.digest(n.encode())[:12],url='https://www.federalregister.gov/d/2026-01899') for n in names])
 text=c.parse(a.get(DOI)[0],'text/html',DOI)[1].lower()
 islands=['Baker Island','Howland Island','Jarvis Island','Johnston Atoll','Kingman Reef','Midway Atoll','Navassa Island','Palmyra Atoll','Wake Atoll']
 if not all(n.lower() in text for n in islands):raise ValueError('Island reference changed')
 c.dump(D/'outlying.json',[dict(name=n,id='UM-'+n.split()[0],url=DOI,note='No municipal issuer in the Census government roster') for n in islands])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');main(p.parse_args().fetch)
