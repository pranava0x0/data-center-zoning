import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re
from lib.status import day, det
def classify(r,cutoff,perm,no,app,obs):
 if r.get('state')!='MD':return None
 ds,s,t,d=r['dataset'],r['status'],day(r.get('date')),det(r)
 if ds=='Baltimore DHCD issued building and use permits' and t and d.get('base_permit'):return perm('MD:baltimore-dhcd','unconfirmed','Explicit issue date; modifications share the original city permit; not evidence of current validity.',t,stable_no=d['base_permit'])
 if ds=='Maryland MDE Frederick campus air permits' and t:return perm('MD:mde-air-ptc','unconfirmed','Premises-wide signed control number, not separate instruments per equipment installation.',t)
 if ds=='Maryland MDE Frederick water appropriation and use permits' and t:return perm('MD:mde-water','unconfirmed','Issued appropriation instrument; printed expiry does not rule out later renewal or withdrawal.',t,stable_no=re.sub(r'\(\d+\)$','',r['record_no']))
 if ds=='Maryland MDE Frederick land restoration decisions':return no('Land restoration plan approval or withdrawal, not a separate construction permit.','decision')
 if ds=='Maryland MDE Frederick construction stormwater letters':return no('Agency action required letter; individual NOI/continuation numbers do not establish new issuance on the letter date.','notice')
 return None
