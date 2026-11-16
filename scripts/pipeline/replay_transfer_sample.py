"""Re-run a fixed cross-jurisdiction sample and compare independently read history bytes before/after."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
from lib.paths import series_path
import subprocess, sys
import lib.discovery as c
CASES={'collectors/virginia/loudoun_county/building_and_zoning_gis.py':['loudoun'],'collectors/ohio/history.py':['oh'],'collectors/texas/history.py':['tx'],'collectors/arizona/history.py':['az'],'collectors/indiana/history.py':['in'],'collectors/virginia/fairfax_county/land_use_cases.py':['fairfax_va'],'collectors/virginia/henrico_county/permits.py':['henrico_va'],'collectors/ohio/central_ohio_entitlements.py':['metropriority_oh'],'collectors/illinois/elk_grove_village_cook_assessor.py':['elkgrove_il'],'collectors/virginia/manassas/development_actions.py':['manassascity_va'],'collectors/federal/faa_letters_california_energy.py':['faaletters_ca'],'collectors/federal/usace_digital_library.py':['corpslibrary_'+s for s in ('oh','or','il','la')],'collectors/federal/usace_virginia_prior_actions.py':['corpsprior_va'],'collectors/multistate/water_fire_authorizations.py':['waterfire_'+s for s in ('az','ca','pa','tx','va','wa')],'collectors/territories/federal_grants.py':['territorygrant_as','territorygrant_vi']}
def run():
 samples=[];n=0
 for script,series in CASES.items():
    def digest():
        return {s:c.digest((series_path(s)).read_bytes()) for s in series}
    before=digest();proc=subprocess.run([sys.executable,str(c.R/'scripts'/script)],cwd=c.R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
    if proc.returncode:raise RuntimeError(script+': '+proc.stdout[-600:])
    after=digest()
    if before!=after:raise ValueError(script+' produced different history bytes on replay')
    rows=sum(len(c.read(series_path(s),[])) for s in series);n+=rows
    samples.append(dict(collector=script,rows=rows,series_sha256=after))
 c.dump(c.OUT/'replay_transfer_sample.json',dict(collectors=len(samples),series=sum(len(s) for s in CASES.values()),rows=n,results=samples,limits='An offline replay compares the same input bytes. It does not measure retrieval from current portals or completeness of the search.'))
 print(len(samples),'collectors reproduced',n,'rows in',sum(len(s) for s in CASES.values()),'series')
if __name__=='__main__':run()
