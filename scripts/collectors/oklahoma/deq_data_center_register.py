"""Oklahoma Department of Environmental Quality (DEQ) consolidated data-center register: the index page and its air,
water and land permit tables. download() fetches each linked proof; rows() walks the register rows and hands each to the
application or final-instrument module by proof type."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
from urllib.parse import urljoin
import lib.discovery as collect
from lib.text import slug
from collectors.oklahoma.common import ST, M, tables, csv_rows, capture
from collectors.oklahoma import deq_air_permit_applications as applications, deq_final_instruments as instruments
KEYS=('index','air','active','issued','active_csv','issued_csv')
def stage(m):capture(m,KEYS)
def download(m):
    for row in tables(ST.read(m['index']))[1][1:]:
        for u in row[-1][1]:
            url=urljoin(m['index']['url'],u)
            if url in m.setdefault('proofs',{}):continue
            try:m['proofs'][url]=ST.get(url,'pdf' if '.pdf' in url.lower() else 'html')
            except (OSError,ValueError) as e:m['proofs'][url]=dict(url=url,error=str(e))
            collect.dump(M,m)
def rows(m,out,holds,oo):
    rs=tables(ST.read(m['index']))[1];head=[v for v,u in rs[0]]
    if head!=['DIV','COUNTY','COMPANY','FACILITY','PERMIT TYPE','STATUS','LINK']:raise ValueError('Changed issuer table')
    issued={x['Permit Number'].strip():x for x in csv_rows(m,'issued_csv')};active=csv_rows(m,'active_csv')
    for i,rr in enumerate(rs[1:],1):
        div,county,company,fac,typ,status,link=[v for v,u in rr];urls=rr[-1][1]
        if div not in ('AQD','WQD','LPD'):continue
        url=urljoin(m['index']['url'],urls[0]);r=m['proofs'][url];det=dict(county=county.title()+' County',agency_company=company,source_class=typ,register_status=status,register_row=i,index_sha256=m['index']['sha256']);day=None
        if 'sha256' not in r:
            got=applications.from_csv(m,active,i,fac,county,r,holds)
            if got is None:continue
            num,day,role,status,kind,r,url,ds=got
        elif r['ext']=='html':
            num,day,role,status,kind,ds=applications.from_html(r)
        else:
            got=instruments.from_pdf(m,oo,issued,out,holds,i,div,county,fac,url,r,det)
            if got is None:continue
            num,day,role,kind,ds=got
        if num in out:raise ValueError('Overlapping case keys '+num)
        out[num]=dict(id='ok-deq-'+slug(num),state='OK',dataset=ds,jurisdiction=det['county'],record_no=num,project=fac,kind=kind,status=status,date=day,date_role=role,url=url,source_url=m['index']['url'],locator='DEQ consolidated data-center register row '+str(i)+'; '+num,details=dict(source_sha256=r['sha256'],**det))
    return len(rs)
