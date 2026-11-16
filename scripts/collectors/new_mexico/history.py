"""New Mexico permit history: combines the Albuquerque building permit and air notification sources, the New Mexico
Environment Department air dockets and EPA construction stormwater records into output/history/new_mexico/history.json.
Use --fetch once to add missing inputs. Subsequent runs validate and replay the source bytes.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from lib.paths import collector_data, series_path
import argparse
import lib.discovery as c
from lib.url_archive import Archive,place_rank
from collectors.new_mexico import albuquerque_building_permits, albuquerque_air_quality_notifications, nmed_air_dockets

def run(fetch):
    a=Archive('nm',fetch,owner='new_mexico');out=[];held=[]
    rank=place_rank(a,'NM','35');c.dump(collector_data('new_mexico','rank.json'),rank)
    def emit(ds,no,place,county,project,kind,status,day,role,url,pin,loc,**fields):
        if day>'2026-11-15':return
        ident='nm-'+c.digest('|'.join([ds,no,day,role]).encode())[:16]
        out.append(dict(id=ident,state='NM',dataset=ds,record_no=no,jurisdiction=place,county=county,project=project,kind=kind,status=status,date=day,date_role=role,url=url,source_url=fields.pop('source_url',url),source_sha256=pin,locator=loc,details=fields))
    u,ids=albuquerque_building_permits.rows(a,emit,held)
    albuquerque_air_quality_notifications.rows(a,emit)
    nmed_air_dockets.rows(a,emit)
    from collectors.new_mexico.epa_construction_stormwater import water
    wet,uncertain=water();out.extend(wet);held.extend(uncertain)
    if len({o['id'] for o in out})!=len(out):raise ValueError('Repeated action')
    c.dump(series_path('nm'),sorted(out,key=lambda r:(r['date'],r['id'])))
    c.dump(collector_data('new_mexico','coverage.json'),dict(query=u,candidate_building_records=len(ids),held=held,archive_count=len(a.sources),note='Notifications, withdrawals, drafts and original applications do not establish permit issuance. Statewide history is incomplete.'))
    print('New Mexico:',len(out),'actions;',len(held),'excluded candidates')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');run(p.parse_args().fetch)
