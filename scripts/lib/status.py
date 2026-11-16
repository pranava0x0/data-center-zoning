"""Shared status helpers for status_<state>.py: date parsing, detail decoding, EPA ICIS status mapping."""
import json
from datetime import date


def day(s):
    try:return date.fromisoformat(str(s))
    except (ValueError,TypeError):return None
def det(r):
    v=r.get('details') or {}
    return json.loads(v) if isinstance(v,str) else v
def epa(r,cutoff,perm,no):
    d=det(r);s=r['status'];st=r['state'];reg=st+':npdes';issue=day(r.get('date'));exp=day(d.get('expiration_date'));eff=day(d.get('effective_date'))
    if not issue:return no('Undated ICIS observation; no verified issuance.','unknown')
    if s in ('PND','NON'):return no('ICIS pending or not needed.','application')
    if s in ('EXP','TRM','RET'):return perm(reg,'historical','ICIS reports '+s+'; not an active coverage.',issue)
    if s=='EFF':
        if d.get('version')=='0' and eff and exp and eff<=cutoff<=exp:return perm(reg,'active','EPA records Effective coverage with dates spanning the snapshot; check issuing agency for later changes.',issue)
        return perm(reg,'unconfirmed','Older ICIS version or effective label without corroborating dates.',issue)
    return None


def iso(s):
    try:return date.fromisoformat(str(s))
    except (ValueError,TypeError):return None
def details(r):
    d=r.get('details') or {}
    if isinstance(d,str):
        try:d=json.loads(d)
        except ValueError:return {}
    return d if isinstance(d,dict) else {}
