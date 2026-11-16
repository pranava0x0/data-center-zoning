"""Validate the nationwide local search frame before a separate federal history release. A pass is not a completeness claim."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import collections, csv, json, argparse
import lib.discovery as c
D=c.R/'data/national'
def read(p):
 with p.open() as f:return list(csv.DictReader(f))
def run(require=False):
 pri={r['state'] for r in read(D/'priority.csv')};geo=read(D/'jurisdictions.csv');ledger=read(c.OUT/'national_jurisdiction_checks.csv')
 if len(pri)!=56 or {r['state'] for r in geo}!=pri or len(geo)!=len(ledger) or {r['geoid'] for r in geo}!={r['geoid'] for r in ledger}:raise ValueError('Missing national jurisdiction, shape or search disposition')
 units=read(D/'government_units.csv'); layers=collections.Counter(r['layer'] for r in geo);classes=collections.Counter(r['class_name'] for r in units)
 if not {'General Purpose','Special District'}<=classes.keys() or not {'place','cousubs','territory subdivisions','counties'}<=layers.keys():raise ValueError('Government or geography layer omitted')
 checks=read(c.OUT/'national_local_checks.csv');outcomes=collections.Counter(r['outcome'] for r in checks);territory=c.read(D/'territory_directory_checks.json',[]);tribes=c.read(D/'tribal_site_checks.json',[])
 if len({r[0] for r in territory if r[2] in ('html','pdf')})!=5:raise ValueError('One or more territorial research offices missing')
 if len(tribes)!=len(c.read(D/'tribal_governments.json',[])) or not any(r['checked_pages'] for r in tribes):raise ValueError('Tribal site review not reconciled with recognition roster')
 if any(int(r['readable_pages'])==0 and r['outcome'] in ('Possible mention','No mention on pages read') for r in checks):raise ValueError('Unreadable site credited with a search result')
 queued=sum(r['result']=='Website queued' for r in ledger);govqueue=outcomes['Not visited']
 note='Geographic and government coverage only. A missing website, unreadable page or keyword miss does not rule out permits. No claim that every local permit has been recovered.'
 result=dict(states_and_territories=len(pri),geographies=len(geo),geography_classes=layers,government_units=len(units),government_classes=classes,site_outcomes=outcomes,territorial_offices=len(territory),federal_register_printed_entries=len(tribes),tribal_website_outcomes=collections.Counter(r['result'] for r in tribes),supplemental_geography_sites_queued=queued,census_offices_queued=govqueue,local_first_pass_complete=not queued and not govqueue,scope=note)
 c.dump(c.OUT/'national_scope_check.json',result)
 if require and not result['local_first_pass_complete']:raise SystemExit('Finish the local website queues before collecting federal history.')
 print('National frame:',len(geo),'geographies;',len(units),'government records;',govqueue,'Census office entries and',queued,'geographic sites still queued.')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--require-first-pass',action='store_true');run(ap.parse_args().require_first_pass)
