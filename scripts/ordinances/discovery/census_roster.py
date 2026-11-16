"""Match the 2022 Census General Purpose government roster by FIPS and unit name."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv, io, re, zipfile
from pathlib import Path
import openpyxl
import lib.discovery as c
D=c.R/'cache/local-screen';outfile=c.R/'data/screen_rosters/census.csv'
def main():
    geo={r['geoid']:r for r in csv.DictReader((c.R/'data/jurisdictions.csv').open())}
    with zipfile.ZipFile(D/'census-gov.zip') as z:
        w=openpyxl.load_workbook(io.BytesIO(z.read(next(n for n in z.namelist() if n.endswith('.xlsx')))),read_only=True)
    it=w['General Purpose'].values;cols=next(it);rows=[]
    for values in it:
        r=dict(zip(cols,values));st,ct,place=(str(r[k] or '') for k in ['FIPS_STATE','FIPS_COUNTY','FIPS_PLACE'])
        if not r['WEB_ADDRESS'] or r['IS_ACTIVE']!='Y':continue
        typ=str(r['UNIT_TYPE'])[:1];gid=st+ct if typ=='1' else st+place if typ=='2' else st+ct+place if typ=='3' else ''
        g=geo.get(gid);u=r['WEB_ADDRESS'].strip();name=str(r['UNIT_NAME']).lower()
        if not g or not re.fullmatch(r'(?:https?://)?[\w.-]+\.[A-Za-z]{2,}(?:/[^ ]*)?',u):continue
        base=re.sub(r' (city|village|township|town|county|parish)$','',g['name'].lower())
        if base not in name or re.search(r'facebook\.com|wikipedia\.org',u,re.I):continue
        rows.append((gid,g['state'],g['name'],'https://'+re.sub('^https?://','',u,flags=re.I)))
    with outfile.open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['geoid','state','name','url']);wr.writerows(sorted(rows))
    print(len(rows),'Census-listed government URLs')
if __name__=='__main__':main()
