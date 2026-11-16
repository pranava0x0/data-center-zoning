"""Identify explicitly reviewed local-register families. Do not infer an issuer from the situs."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import csv
from collections import defaultdict
import lib.discovery as c
# Exact register names. Adding a state to the project does not silently classify a new feed.
NAMES="""City of Manassas development and construction updates
Cook County assessor municipal permit register
Elk Grove Village redevelopment resolutions
Abilene city site-plan register
Albuquerque issued building permits
Anchorage inspection and review actions
Anchorage permit records
Aurora Building Division issued permit and certificates
Austin issued construction permits
Baltimore DHCD issued building and use permits
Bluffdale Planning Commission decisions
Bossier Parish Police Jury land decisions
Boston ISD approved building permits
Bridgewater Township planning agenda
Chandler Citizen Access
Chandler city council zoning decisions
Charlotte rezoning petitions
Chicago building permits
Clark County active dust-control snapshot
Columbus building and trade permits
Columbus engineering filings
Council Bluffs Building Division issued permits
Dallas building permits
Denver commercial permits at a verified data-center site
Douglas County Planning and Zoning agendas
Durham City-County building permits
East Baton Rouge building permits
Fairfax County site plan and land development decisions
Fort Worth development permits
Framingham building applications
Franklin Municipal Planning Commission site plans
Goodyear Citizen Access
Hartford building and trade permits
Hayward public land-use proceedings
Henderson open development permits
Henrico County monthly issued permits
Hilliard campus board decisions
Honolulu historical building permits
Huntsville building permits
Huntsville occupancy certificates
Laramie County SmartGov planning permits
Laramie County commissioners and planning commission
Lewiston City Council development agreements
Lincoln nonresidential building permits
Little Rock municipal permits
Los Angeles issued building and trade permits
Loudoun fire marshal — data-center property authorizations
Loudoun issued permits
Loudoun land-use applications
Loudoun monthly building reports
Loudoun submitted permits
Louisville Metro development plans
Maricopa County air permit register
Maricopa County air public notices
Mesa building permit register
New Albany verified campus zoning actions
New Albany zoning entitlements
Niagara Falls project decisions
Norwalk site plan surety decisions
NYC BIS permit issuance
NYC DOB building job filings
Oldham County Project Lincoln withdrawals
Palm Beach County Project Tango decisions
Papillion City Administrator permit reports
Phoenix Fire Department — data-center project and address match
Phoenix permits
Phoenix plan reviews
Pima County dust enforcement
PortlandMaps all permits
Prince William data-center building permits
Raleigh building permits
Saline Township land use proceedings
Salt Lake City building permit workflow
San Antonio issued building and trade permits
San Francisco Fire Department storage and use permits
San Francisco building permits
San José C.3 stormwater project tracking
San José building permit registers
San José planning register
Santa Clara Fire Marshal permit documents
Santa Clara public land-use proceedings
Scottsdale permits at a verified data-center site
Seattle building permits
Shelby County Health Department air permits
Shreveport land use decisions
Somerset Planning Board project decisions
Southaven Board of Aldermen planning decisions
Tempe building safety permits
Town of Eatonville council agendas
Tucson commercial building permits
Van Buren Township Planning Commission
Washoe County planning decisions
Washoe County project case files
Washoe County special use permits
West Des Moines City Council site plans
Yellowstone County commission project agenda
City of Alpharetta commercial permits
City of Cheyenne public planning cases
City of De Soto project and planning records
City of Fargo commission proceedings
City of Hobart Plan Commission minutes
City of Kuna planning and zoning cases
City of Miami iBuild permits
City of South Fulton zoning information meeting
City of Southfield site-plan review""".splitlines()
def audit(events):
 grouped=defaultdict(list)
 for e in events:
    if e['dataset'] in NAMES:
        if e['federal_issuer']:raise ValueError('Local issuer conflicts with federal evidence: '+e['id'])
        grouped[(e['state'],e['dataset'])].append(e)
 if set(NAMES)-{k[1] for k in grouped}:raise ValueError('Missing reviewed register: '+str(set(NAMES)-{k[1] for k in grouped}))
 with (c.OUT/'local_register_examples.csv').open('w',newline='') as fp:
    w=csv.writer(fp);w.writerow(['state','local_register','rows','example_government_url','example_record','locator'])
    for (st,reg),rr in sorted(grouped.items()):
        e=rr[0];w.writerow((st,reg,len(rr),e['url'],e['record_no'],e['locator']))
 return frozenset(NAMES)
