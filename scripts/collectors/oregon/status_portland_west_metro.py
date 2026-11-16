"""Assess municipal evidence without interpreting a zone change or an appeal as a construction permit."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from datetime import date
def classify(r,cutoff,perm,no,app,obs):
 ds=r.get('dataset');s=r.get('status');day=date.fromisoformat(r['date']) if r.get('date') else None
 if ds=='PortlandMaps all permits':
  k=r['kind'];x=r['details'];issue=x['source_dates']['ISSUED']
  if k in {'Early Assistance','Public Registry'}:return no('Consultation or use determination inquiry, not an issued development permit.','observation')
  if k=='Noise Variance':return no('Closed noise variance file; the register does not establish the specific disposition.','closed_file')
  if not issue and x['source_dates'].get('INTAKECOMPLETEDATE') and s=='Final':return no('The only dated action is intake. The city now labels this file Final, but gives neither an issue date nor a final inspection date.','intake')
  if not issue:return no('Permit class but no source issuance date.','unknown')
  if s in {'Final','Expired','Closed'}:return perm('OR:portlandmaps','historical','Numbered municipal permit with issuance date and terminal status: '+s+'.',day)
  if s in {'Issued','Under Inspection'}:return perm('OR:portlandmaps','unconfirmed','Numbered and dated municipal issuance; continued validity is not confirmed by a separate term or verified active flag.',day)
  return no('City status not mapped.','unknown')
 if ds=='Municipal land-use case records':
  if r['id']=='westmetro-hayward-spr23-0036':return perm('CA:hayward-planning','unconfirmed','Planning Commission carried motion approving numbered joint application; validity not established.',day)
  if r['id']=='westmetro-sacramento-prime':return no('County-approved entitlement recorded in NOD, but only state clearinghouse number, not the issued local permit identifier.','observation')
  return no('Environmental appeal filing is a procedural action, not a new permit.','observation')
 if ds=='Oregon land-use ordinance and review records':return no('Parcel rezoning or state appeal disposition, not a separately numbered construction permit.','observation')
 return None
