"""Deterministic, narrow extraction recipes. Return candidates only, with original conditions.
A new number can be flagged on refresh. No automatic change of legal interpretation.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import re, json, csv
from decimal import Decimal
import lib.discovery as c
# Phrases before and after each value disambiguate dimensions, comparison and averaging basis.
RECIPES=[
 ('va-lou-grade','land_disturbed','>=','ft2',r'land disturbance that equals ([\d,]+) square feet or more will require a grading permit','Sensitive-area exception; county grading only.'),
 ('va-lou-grandfather-admin','grandfather_residential_distance','>','ft',r'more than ([\d,]+) feet from all existing residential structures on february 12, 2025','Grandfathering test only; also check prior application, date and retention.'),
 ('va-fx-setback','equipment_residential_setback','>=','ft',r'power supply equipment, must be either: 1\. located at least ([\d,]+) feet from the lot line of an r district','Equipment alternative: intervening building; special exception may reduce.'),
 ('in-withdrawal-registration','withdrawal_capacity','>','gal/day',r'capability of withdrawing more than one hundred thousand \(([\d,]+)\) gallons of ground water','Aggregate withdrawal capacity, not actual consumption or a withdrawal permit.'),
 ('oh-consumptive-use','new_or_increased_consumptive_use','>','gal/day',r'new or increased consumptive use of more than an average of (two million) gallons of water per day in any thirty-day period','Average over any 30-day period; statute exceptions apply.'),
 ('az-chandler-noise','annual_postconstruction_studies','duration','year',r'annual noise study during peak operation times for (five) years','After construction; baseline and notification are separate requirements.'),
 ('az-navajo-minor-air','application_lead_time','>=','days',r'at least ([\d,]+) days prior to the requested beginning of construction','Applicable minor-source application, with general-permit exception.')]
def extract(s,pattern):
    values=set(re.findall(pattern,c.norm(s)))
    if len(values)!=1:return None
    raw=values.pop();return {'two million':2000000,'five':5}.get(raw) if not raw[0].isdigit() else int(raw.replace(',',''))
def main():
    rules={r['id']:r for r in c.rules()};idx=c.read(c.INDEX,{})
    out=[]
    for rid,metric,op,unit,pat,ctx in RECIPES:
        r=rules[rid];src=idx.get(c.address(r['url']),{});h=src.get('sha256');s=(c.CACHE/(h+'.txt')).read_text() if h else ''
        val=extract(s,pat)
        out.append(dict(rule_id=rid,metric=metric,operator=op,value=val,unit=unit,condition=ctx,state=r['state'],status='extracted_candidate' if val is not None else 'review_pattern_or_source',source_url=r['url'],sha256=h,pattern=pat))
    c.dump(c.OUT/'extracted_values.json',out);print(sum(x['value'] is not None for x in out),'of',len(out),'typed recipes matched')
if __name__=='__main__':main()
