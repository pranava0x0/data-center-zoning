"""Content-neutral topic vocabulary. This module assigns a family, never a legal outcome."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import re

def key(value):
    return ' '.join(re.findall(r'[a-z0-9]+', str(value or '').lower()))

# Explicit aliases, not substring matches: e.g., "permitting pause" does not say
# what regulator took the action, nor that a local zoning moratorium exists.
FAMILIES = {
    'Land use & zoning': ('use prohibition','accessory use','by right','use permission','use classification','use definition','definition','prior approval','permitted use','grandfathering','special exception','special use permit','conditional use','prohibition','moratorium','district','zoning'),
    'Authority & applicability': ('zoning authority','state certification','jurisdiction','permitting pause','consultation'),
    'Construction & land': ('grading','site plan','stormwater','stormwater permit','construction stormwater','land disturbance','erosion control','floodplain','subdivision','construction'),
    'Building & life safety': ('building','building permit','accessibility','demolition','fire safety','fire protection','hazardous materials','occupancy','elevator','plumbing','mechanical','electrical permit'),
    'Air & power': ('air permitting','air permit','power infrastructure','utility capacity','electric capacity','utility interconnection','backup generation','backup generators','energy storage','air emissions'),
    'Site standards': ('environmental review','parking','setback','residential setback','buffer','noise','site assessment','site design','landscaping','lighting','height'),
    'Water & wastewater': ('cooling','water supply','water withdrawal','reclaimed water','wastewater','industrial pretreatment','cooling water','wetlands','water discharge','private well'),
}
TOPICS={k:category for category,names in FAMILIES.items() for k in names}
UNMAPPED='Unclassified — review'
def classify_rule(topic):
    return TOPICS.get(key(topic),UNMAPPED)

# Classify the responsible regulatory activity, never infer approval or technology
# from article titles, capex, project names or applicant identity.
HISTORY_PATTERNS = [
    ('Administration & correspondence',r'\b(correspondence|premeeting|gis update|public information|administrative review)\b'),
    ('Financial guarantee',r'\b(bond|surety|performance guarantee)\b'),
    ('Land use & zoning',r'\b(zoning|rezoning|use permit|final development plan|development plan approval|development plan review|special exception|conditional use|comprehensive plan|land use decision|legislative application|commission permit|variance)\b'),
    ('Construction stormwater',r'\b(construction stormwater|stormwater|storm water|vesmp|erosion|sediment control|swp3|cgp)\b'),
    ('Wetlands & state waters',r'\b(virginia water protection|vwp|surface water determination|surface waters determination|state programmatic general permits|spgp|wetland|wetlands|section 401|section 404|habitat management)\b'),
    ('Water supply & withdrawals',r'\b(drinking|water withdrawal|groundwater withdrawal|private well|water supply|water rights|water appropriation)\b'),
    ('Wastewater & discharge',r'\b(npdes|vpdes|tpdes|pretreatment|wastewater|discharge|sewer)\b'),
    ('Air construction & operation',r'\b(air permit|air quality|air pollution|air construction|air operating|air registration|air ptio|ptio|new source review|nsr|mnsr|title v|standard permit for electric generating units)\b'),
    ('Utility service & grid',r'\b(interconnection|transmission line|substation approval|electric utility|electric service agreement)\b'),
    ('Engineering, subdivision & land',r'\b(engineering plan|plat|lot split|site plan|site compliance plan|site review|grading|land disturbance|floodplain)\b'),
    ('Tree preservation & vegetation',r'\b(urban forestry|tree preservation|tree removal)\b'),
    ('Accessibility & architectural barriers',r'\b(accessibility|architectural barriers)\b'),
    ('Fire & life safety',r'\b(fire|fmo|sprinkler|standpipe)\b'),
    ('Building trades & occupancy',r'\b(electrical|electric|mechanical|plumbing|elevator|gas|building|accessory structure|occupancy|demolition|hvac|mechanics lien)\b'),
    ('General building-code review',r'\b(code modification|construction design release)\b')
]
def classify_history(kind, *, series='', program='', dataset=''):
    # Series fallback is scoped to the registered Virginia DEQ air collector.
    ds,k=key(dataset),key(kind)
    if ds in ('oregon land use ordinance and review records','municipal land use case records'):return 'Land use & zoning'
    if ds=='portlandmaps all permits':
        if k in ('public registry','early assistance'):return 'Planning consultation'
        if 'noise' in k:return 'Noise review'
        if 'site' in k:return 'Engineering, subdivision & land'
        return 'Building trades & occupancy'
    if ds=='fairfax county site plan and land development decisions':return 'Engineering, subdivision & land'
    if ds=='us site specific water permit records' and 'consumptive' in k:return 'Water supply & withdrawals'
    if ds=='santa clara fire marshal permit documents':return 'Fire & life safety'
    if ds=='cook county assessor municipal permit register':return 'Building trades & occupancy'
    if ds=='elk grove village redevelopment resolutions':return 'Land use & zoning'
    if ds=='city of manassas development and construction updates':
        if 'site plan' in k:return 'Land use & zoning'
        if 'grading' in k:return 'Construction & land'
        return 'Building trades & occupancy'
    if ds=='faa airspace determinations':return 'Aviation & airspace'
    if ds in ('arkansas deq air permitting and pds','arkansas deq other air requests'):return 'Air construction & operation'
    if ds=='arkansas pds regulated storage tank records':return 'Fuel storage & tanks'
    if ds=='us epa region 8 tribal minor nsr final actions':return 'Air construction & operation'
    if ds in ('army corps digital library project actions','army corps prior permit amendments'):return 'Wetlands & federal waters'
    if ds=='army corps consultation history':
        return {'esa':'Wildlife & habitat','efh':'Wildlife & habitat','s106Nhpa':'Historic preservation','wqc401':'Wetlands & federal waters'}[program]
    if ds=='guam interagency land use referrals':return 'Regional development review'
    if ds=='puerto rico planning board location consultations':return 'Land use & zoning'
    if ds.startswith('puerto rico ogpe'):
        if kind in ('Permiso de Corteza Terrestre','Pre-Consulta - Edificabilidad'):return 'Engineering, subdivision & land'
        if kind=='Permiso Único':return 'Business & operating permissions'
        if kind=='Pre-Consulta - Medioambiente':return 'Remediation & environmental review'
        if 'ambiental' in k:return 'Remediation & environmental review'
        if 'generador' in k:return 'Air construction & operation'
        if 'construcci' in k or 'construcci' in kind.lower():return 'Building trades & occupancy'
        if 'uso' in k:return 'Land use & zoning'
        if 'recomendaci' in k:return 'Regional development review'
        if 'urbanizaci' in k:return 'Engineering, subdivision & land'
    if k=='state water quality certification':return 'Wetlands & state waters'
    if ds=='interior insular data center financial assistance':return 'Federal funding'
    if ds in ('department of energy land and developer milestones','interior department land decisions'):return 'Public land & rights-of-way'
    if ds in ('new albany verified campus zoning actions','hilliard campus board decisions'):return 'Land use & zoning'
    if ds=='department of energy nepa determinations':return 'Remediation & environmental review'
    if ds in ('us army corps of engineers regulatory public actions','us army corps of engineers district public notices'):
        if 'environmental assessment' in k:return 'Remediation & environmental review'
        return 'Wetlands & federal waters'
    if ds=='fast 41 timetable decisions':return 'Administration & correspondence'
    if ds=='fast 41 federal permitting milestones':
        if 'endangered' in k or 'species' in k:return 'Wildlife & habitat'
        if 'historic' in k:return 'Historic preservation'
        if '404' in k or 'water' in k:return 'Wetlands & federal waters'
        return 'Federal environmental review'
    if ds in ('anchorage permit records','anchorage inspection and review actions'):return 'Building trades & occupancy'
    if ds=='alaska dnr project decisions':return 'Public land & rights-of-way'
    if ds=='ferc preliminary permit applications':return 'Power & utility review'
    if k in ('environmental assessment','environmental management plan','mepa project change determination','notice of project change'):return 'Remediation & environmental review'
    if k=='administrative permit appeal' and ds.startswith('massdep'):return 'Air construction & operation'
    if ds=='nebraska dwee facility air files':return 'Air construction & operation'
    if k=='commercial footing and foundation permit':return 'Building trades & occupancy'
    if k in ('zone change lu to pud','act 250 case milestone'):return 'Land use & zoning'
    if k in ('preliminary subdivision plan with domestic water condition','road use and maintenance agreement'):return 'Engineering, subdivision & land'
    if k=='sage grouse habitat consultation':return 'Wildlife & habitat'
    if k=='underground injection control applicability':return 'Wastewater & discharge'
    if ds=='west virginia dep project files':
        if k in ('major source construction application','power plant air application'):return 'Air construction & operation'
        if k.startswith('state waters'):return 'Wetlands & state waters'
    if ds=='atlanta regional commission dri reviews':return 'Regional development review'
    if ds=='city of alpharetta commercial permits':return 'Building trades & occupancy'
    if ds=='pennsylvania dep data center permit tracker':
        code=key(program) or key(str(kind).split('·')[0])
        topics={'wrm water obstructions encroachments':'Wetlands & state waters','storage tanks':'Fuel storage & tanks','wpc act 537 municipal sewage planning':'Wastewater & discharge','wpc state water pollution control':'Wastewater & discharge','wpc erosion sediment control':'Construction stormwater','environmental cleanup brownfields':'Remediation & environmental review','ming explosives safety':'Construction blasting review','air quality':'Air construction & operation','wpc npdes':'Wastewater & discharge','safe drinking water':'Water supply & withdrawals','clean water':'Wastewater & discharge'}
        if code in topics:return topics[code]
    if ds=='susquehanna river basin commission consumptive use approvals':return 'Water supply & withdrawals'
    if ds=='connecticut siting council data center docket':return 'Power & utility review'
    if ds=='city of fargo commission proceedings':return 'Land use & zoning'
    if ds=='dickey county water resource district proceedings':return 'Flood hazard & waterway review' if 'drainage' in k else 'Land use & zoning'
    if ds=='city of de soto project and planning records' or ds=='mount pleasant plan commission minutes':return 'Land use & zoning'
    if ds=='wisconsin dnr lighthouse campus review':
        if 'wetland' in k:return 'Wetlands & state waters'
        if 'stormwater' in k:return 'Construction stormwater'
        if 'water supply' in k or 'sewer' in k:return 'Water & sewer infrastructure'
        return 'Remediation & environmental review'
    if ds=='wisconsin dnr air permit tracking':return 'Air construction & operation'
    if ds.startswith('north dakota deq air'):return 'Air construction & operation'
    if ds.startswith('north dakota deq discharge'):return 'Wastewater & discharge'
    if ds.startswith('oklahoma deq'):
        if 'air' in k or 'source construction permit' in k or 'title v' in k:return 'Air construction & operation'
        if 'water line' in k or 'public water system' in k or 'sewer line' in k:return 'Water & sewer infrastructure'
    if ds=='south carolina des air permitting files':return 'Coastal zone review' if 'czc' in k else 'Air construction & operation'
    if ds=='south carolina dhec groundwater review':return 'Water supply & withdrawals'
    if ds=='kentucky psc project information requests':return 'Power & utility review'
    if ds in ('louisville metro development plans','oldham county project lincoln withdrawals','west des moines city council site plans'):return 'Land use & zoning'
    if ds=='council bluffs building division issued permits':return 'Building trades & occupancy'
    if ds.startswith('iowa dnr air') or ds.startswith('alabama adem'):return 'Air construction & operation'
    if ds=='municipal project planning dockets' or ds.startswith('tulsa metropolitan'):return 'Land use & zoning'
    if ds=='rhode island dem emergency generator permits':return 'Air construction & operation'
    if ds.startswith('utah daq') or ds.startswith('nc deq air') or ds=='nc deq active air permit register':return 'Air construction & operation'
    if ds=='bluffdale planning commission decisions':return 'Land use & zoning'
    if ds=='salt lake city building permit workflow':return 'Building trades & occupancy'
    if ds.startswith('charlotte rezoning'):return 'Land use & zoning'
    if ds=='delaware coastal zone act decisions':return 'Coastal zone review'
    if ds=='lewiston city council development agreements' or ds=='oregon planning commission cases':return 'Land use & zoning'
    if ds=='denver commercial permits at a verified data center site':return 'Building trades & occupancy'
    if ds=='oregon deq air permit documents':return 'Air construction & operation'
    if ds=='local land use compatibility finding in deq permit':return 'Land use & zoning'
    if ds=='michigan public service commission special contracts':return 'Power & utility review'
    if ds in ('van buren township planning commission','saline township land use proceedings','city of southfield site plan review'):return 'Land use & zoning'
    if ds=='saline township advisory committee':return 'Building trades & occupancy'
    if ds=='michigan egle air compliance inspections':return 'Air construction & operation'
    if ds.startswith('south florida water management district'):
        return 'Water supply & withdrawals' if k.startswith('wu ') or 'consumptive' in k else 'Surface water & environmental resource permits'
    if ds=='town of eatonville council agendas' or ds=='colorado springs land use appeals':return 'Land use & zoning'
    if ds.startswith('njdep njpdes'):return 'Wastewater & discharge'
    if ds=='njdep treatment works applications':return 'Water & sewer infrastructure'
    if ds=='bridgewater township planning agenda':return 'Engineering, subdivision & land'
    if ds=='njdep land resource permitting':return 'Wetlands & state waters' if 'wetland' in k else 'Flood hazard & waterway review'
    if ds=='state issued water permits reported to epa':return 'Wastewater & discharge'
    if ds=='minnesota eqb environmental review notices' or (ds=='chaska cloud hq municipal decisions' and 'auar' in k):return 'Remediation & environmental review'
    if ds=='chaska cloud hq municipal decisions':return 'Land use & zoning'
    if ds=='cec small power plant exemption docket':return 'Power plant exemption'
    if ds in ('santa clara public land use proceedings','hayward public land use proceedings'):return 'Land use & zoning'
    if ds=='san jos planning register' or ds==key('San José planning register'):
        return 'Remediation & environmental review' if ('environmental review' in k or 'mitigation monitoring' in k) else 'Land use & zoning'
    if k in ('environmental review determination','environmental impact statement decision','coastal consistency determination'):return 'Remediation & environmental review'
    if ds in ('ndep air applications','clark county part 70 operating permits','clark county title v renewal applications','clark county active dust control snapshot'):return 'Air construction & operation'
    if ds in ('washoe county planning decisions','washoe county project case files') and k=='amendment of conditions':return 'Land use & zoning'
    if ds=='mississippi deq ensearch facility permits' and k.startswith('air '):return 'Air construction & operation'
    if ds=='southaven board of aldermen planning decisions' and k=='site plan and design review':return 'Engineering, subdivision & land'
    if ds in ('phoenix permits','phoenix plan reviews'):
        if k.startswith(('fp ','fireline ')):return 'Fire & life safety'
        if 'storm water' in k:return 'Construction stormwater'
        if 'work hours' in k:return 'Construction operating conditions'
        if 'sign' in k.split():return 'Signage & design'
        if 'landscape' in k:return 'Tree preservation & vegetation'
        if 'civil permit' in k or k=='site permit':return 'Engineering, subdivision & land'
        if k in ('address assignment','dsd appeal'):return 'Administration & correspondence'
        if k.startswith(('struc ','plmb ','shell struc ')) or k=='annual facilities permit':return 'Building trades & occupancy'
        if 'plan review' in k:return 'General building-code review'
    if ds=='goodyear citizen access' and k in ('commercial construction','industrial construction'):return 'Building trades & occupancy'
    if ds=='pima county dust enforcement':return 'Air construction & operation'
    if key(dataset)=='indiana idem air decisions and notices':return 'Air construction & operation'
    if key(dataset)=='indiana idem waterways decisions and notices' and 'section 401' in key(kind):return 'Wetlands & state waters'
    if key(dataset)=='ohio epa npdes register' and key(kind) in ('construction permits npdes','construction permits inactive npdes'):return 'Construction stormwater'
    if key(dataset)=='ohio epa selected air and water permits' and key(kind)=='surface water permit to install':return 'Water & sewer infrastructure'
    for text in [key(kind),key(program),key(dataset)]:
        if not text: continue
        for family,pattern in HISTORY_PATTERNS:
            if re.search(pattern,text): return family
    return 'Air construction & operation' if series=='air' else UNMAPPED

def classify_stage(kind, status):
    """Broad stage facet only. Never substitute this for the original status/role."""
    k,s=key(kind),key(status)
    if k=='construction design release':return 'State design release; not building permit'
    if k=='construction design release application':return 'Application, planning or review'
    if 'registration' in k and ('accessibility' in k or 'architectural barriers' in k):return 'Registration record'
    if any(w in k for w in ('public notice','notice of intent','draft permit')):return 'Notice or draft record'
    if 'non permit' in k or k.startswith('no vmrc permit nec'):return 'Non-permit activity'
    if 'determination' in k:return 'Determination record'
    if s=='favorable recommendation':return 'Recommendation, not final decision'
    if s in {'issued','per issued','permit issued'}:return 'Issuance reported'
    if s in {'denied','withdrawn','wthd','rejected','void','voided','expired','cancelled','canceled'}:return 'Adverse, withdrawn or expired'
    if s in {'modified','per reiss','transfer','per term','terminated','reissued'}:return 'Modification, reissue, transfer or termination'
    if s in {'approved','appr','voted to approve','site plan approval','grant preliminary plat'}:return 'Approval reported, not necessarily permit issuance'
    if s in {'completed','complete','closed','finaled','finalled','final','finalized','arch','archived','history'}:return 'Completion or archive status, not evidence of issuance'
    if s in {'in review','in progress','submitted online','submitted','planned','md in prog','rs in prog','application','pending','t in prog','md submit','rs submit','received','filed'}:return 'Application, planning or review'
    return 'Other source status; inspect record'
