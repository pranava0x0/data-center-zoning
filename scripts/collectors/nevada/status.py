"""Reporting status for NV’s source-specific fields; do not infer an active permit from a notice."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.status import day, det, epa
def classify(r,cutoff,perm,no,app,obs):
    if r.get('state')!='NV':return None
    ds=r['dataset'];s=r['status'];d=det(r);dt=day(r.get('date'))
    if ds=='EPA ICIS-NPDES permit versions':return epa(r,cutoff,perm,no)
    if ds in ('NDEP preliminary air determinations','Northern Nevada Public Health air notices','Clark County air participation notices'):return no('Proposed action or public comment notice; no final issuance established.','notice')
    if ds in ('NDEP air applications','Clark County Title V renewal applications'):return app()
    if ds=='Clark County Part 70 operating permits' and s in ('Issued','Significant Revision'):
        # County table identifies the term by stationary source, issue and expiration. No standalone permit number is assigned.
        return perm('NV:clark-title-v','unconfirmed','Issued permit term; term date passed and renewal application was received. No final renewal decision in this snapshot.',dt,stable_no=r['record_no']+'|'+d['expiration_date'])
    if ds=='Clark County active dust-control snapshot' and s=='Active at snapshot':
        return perm('NV:clark-dust','unconfirmed','County listed this version as active in 2025; its stated end date passed and no current status was included.',dt,stable_no=r['record_no'].split(' - ')[0])
    if ds=='Henderson open development permits':
        if not day(d.get('issue_date')):return app()
        return obs('NV:henderson-building',historical=('done',),issued=('issued',),when=dt)
    if ds=='Clark County inspection sites':return obs('NV:clark-building',issued=('issued',),when=dt)
    if ds in ('Washoe County special use permits','Washoe County project case files'):
        if s=='Approved' and r['kind']=='Special use permit':return perm('NV:washoe-sup','unconfirmed','County expressly records special use permit approval; present rights and current compliance are not established.',dt)
        if s=='Submitted':return app()
    if ds=='Washoe County planning decisions' and s=='Approved with amended conditions':return no('Amendment of conditions to an underlying special use permit, not a new permit.', 'decision')
    return None
