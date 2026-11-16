"""Bounded OCR of cached government PDF originals, separate from ordinary text results.
Offline report by default. --ocr runs Apple Vision on macOS or tesseract on PATH.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import argparse, collections, csv, gzip, hashlib, io, json, os, platform, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path
import fitz
import lib.discovery as c
from ordinances.codebooks.inventory import DC,LAND,EXCLUDE
R=c.R; D=R/'data/national'; BASE=R/'cache/codebook-ocr'; BOOK=R/'cache/codebooks'; ORIGINAL=BOOK/'files'
PLAN=BASE/'cohort.json'; INVENTORY=D/'codebook_ocr_inventory.csv'; SUMMARY=D/'codebook_ocr_summary.json'; PAGES=D/'codebook_ocr_pages.jsonl.gz'
TARGET=re.compile(r'\b(?:data[\W_]*cent(?:er|re)s?|server farms?|hyperscale|digital infrastructure)\b',re.I)
TOPIC=re.compile(r'definition|use.{0,12}table|table.{0,12}use|schedule.{0,12}uses|permitted uses|supplementa\w+ (?:use|standard)|development standards|industrial district|manufacturing district|commercial district',re.I)
IRRELEVANT=re.compile(r'cover page|appointment|board of appeals|board of adjustments?|variance application|\bmap\s+only|contractor|apartment|assessor|marijuana|short.term rental|cannabis|adult.entertainment|fees? schedule|manufactured hous',re.I)
def digest(x):return hashlib.sha256(x).hexdigest()
def rows(path):
 with path.open() as f:return list(csv.DictReader(f))
def textjson(p,v):c.dump(p,v)
def make_inventory():
 frozen=BASE/'population.json.gz'
 if frozen.exists():return json.loads(gzip.decompress(frozen.read_bytes()))
 docs={}
 for r in rows(D/'codebooks.csv'):
    z=c.read(BOOK/'checks'/(digest(r['url'].encode())+'.json'),{})
    if z.get('text_pages')!=0 or not z.get('sha256'):continue
    sh=z['sha256'];d=docs.setdefault(sh,dict(sha256=sh,pages=z['pages'],refs=[],urls=set(),states=set(),geoids=set(),markers=0,ranks=set()));d['refs'].append(r);d['urls'].add(r['url']);d['states'].add(r['state']);d['geoids'].add(r['geoid']);d['markers']=max(d['markers'],int(r['markers']));d['ranks'].add(int(r['state_rank']))
 for d in docs.values():
    d['states']=sorted(d['states']);d['geoids']=sorted(d['geoids']);d['urls']=sorted(d['urls']);d['rank']=min(d.pop('ranks'));d['url']=d['urls'][0];d['geo']=d['geoids'][0];d['state']=d['states'][0]
    labs=' '.join(r['label']+' '+r['url'].split('/')[-1] for r in d['refs']).replace('_',' ');d['label']=d['refs'][0]['label']
    d['target']=bool(TARGET.search(labs));d['broad']=bool(LAND.search(labs) or re.search('zoning|district regulations|land use',labs,re.I)) and not IRRELEVANT.search(labs)
    d['year']=max([int(x) for x in re.findall(r'(?<!\d)(20(?:0\d|1\d|2[0-6]))(?!\d)',labs)] or [0])
 frozen.write_bytes(gzip.compress(json.dumps(docs,sort_keys=True,ensure_ascii=False).encode(),mtime=0))
 return docs
def select(docs,limit,budget):
 usable=[d for d in docs.values() if d['pages'] and 'MO' not in d['states']]
 key=lambda d:(d['rank'],-d['markers'],-d['year'],d['sha256']);chosen=[];seen=set();geos=set();states=collections.Counter()
 def add(d,reason,cap,allow_geo=False):
    if d['sha256'] in seen or len(chosen)>=limit or (d['geo'] in geos and not allow_geo):return
    cap=min(cap,d['pages']);used=sum(v['probe_budget']+v['follow_budget'] for v in chosen)
    if budget-used<cap:return
    follow=min(2,cap//3) if cap<d['pages'] else 0
    chosen.append(dict(sha256=d['sha256'],url=d['url'],geoids=d['geoids'],states=d['states'],reason=reason,total_pages=d['pages'],probe_budget=cap-follow,follow_budget=follow))
    seen.add(d['sha256']);geos.add(d['geo']);states[d['state']]+=1
 for d in sorted([d for d in usable if d['target']],key=key):add(d,'explicit data-center referral',min(24,d['pages']),True)
 # Guarantee broad codes and compact complete instruments, not every zoning amendment.
 for band,reason,cap in [(lambda d:d['pages']>=40,'long zoning book, stratified state',7),(lambda d:3<=d['pages']<=8,'small zoning instrument, full',8),(lambda d:9<=d['pages']<40,'medium zoning book, stratified state',6)]:
    pool=[d for d in usable if d['broad'] and band(d)]
    buckets=collections.defaultdict(list)
    for d in sorted(pool,key=key):buckets[d['state']].append(d)
    for st in sorted(buckets,key=lambda k:(states[k]>0,buckets[k][0]['rank'],k))[:18]:
        for d in buckets[st]:
            if d['geo'] not in geos:add(d,reason,cap);break
 return chosen
def pick(doc,slot):
 n=len(doc);cap=slot['probe_budget']
 if cap>=n:return list(range(1,n+1))
 idx=[1,2]
 for level,title,p in doc.get_toc():
    if isinstance(p,int) and p>0 and TOPIC.search(title):idx.append(p)
 idx+=([3,min(5,n),n,max(1,n//2),max(1,2*n//3)] if n>=9 else [n,max(1,n//2)])
 idx+=list(range(1,n+1));return list(dict.fromkeys(p for p in idx if 1<=p<=n))[:cap]
def follow(n,first,cap):
 seen={v['pdf_page'] for v in first};proposed=[]
 for r in first:
    for i,l in enumerate(r['lines']):
        if TOPIC.search(l) or TARGET.search(l):
            # Contents page numbers may be printed or article-specific, so they only
            # direct a supplementary page check, never establish relative page identity.
            for s in [l]+r['lines'][i+1:i+2]:
                m=re.search(r'(?:\.{2,}|\s|^)(\d{1,3})\s*$',s)
                if m:
                    p=int(m[1])
                    if 1<=p<=n:proposed.extend([p,p+1])
 for r in first:
    if DC.search(' '.join(r['lines'])):proposed.extend([r['pdf_page']+1,r['pdf_page']-1])
 proposed += [n//3,2*n//3,n//2+1,n-1]+list(range(1,n+1))
 return list(dict.fromkeys(p for p in proposed if 1<=p<=n and p not in seen))[:cap]
def engine(name):
 if name=='auto':name='vision' if sys.platform=='darwin' and shutil.which('swiftc') else 'tesseract'
 if name=='vision':
    src=R/'scripts/lib/ocr_vision.swift';sha=digest(src.read_bytes());exe=BASE/('vision-'+sha[:16])
    if not exe.exists():subprocess.run(['swiftc',str(src),'-o',str(exe)],check=True,cwd=R)
    return name,str(exe),dict(engine='Apple Vision VNRecognizeTextRequest',engine_version=platform.mac_ver()[0],recognition='accurate, no language correction; 1650x2200 thumbnail',helper_sha256=sha)
 if name=='tesserocr':
    sys.path.insert(0,str(BASE/'runtime'));import tesserocr
    model=BASE/'tessdata/eng.traineddata';expected='7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'
    if not model.exists() or digest(model.read_bytes())!=expected:raise ValueError('Install the pinned English tessdata_fast model; see docs/codebook-ocr.md')
    return name,'',dict(engine='Tesseract (tesserocr)',engine_version=tesserocr.tesseract_version().splitlines()[0],recognition='tessdata_fast eng; AUTO page segmentation; 180 DPI RGB from PyMuPDF',model_sha256=expected,wrapper_version=tesserocr.__version__)
 if not shutil.which('tesseract'):raise SystemExit('Install tesseract or select --engine vision on macOS.')
 v=subprocess.check_output(['tesseract','--version'],text=True).splitlines()[0]
 return name,shutil.which('tesseract'),dict(engine='Tesseract',engine_version=v,recognition='eng --psm 3; 180 DPI RGB rendered PDF')
def process(slot,eng):
 sh=slot['sha256'];b=(ORIGINAL/(sh+'.pdf')).read_bytes()
 if digest(b)!=sh:raise ValueError('Original PDF digest mismatch: '+sh)
 name,exe,meta=eng;pdf=fitz.open(stream=b,filetype='pdf');dest=BASE/'pages'/sh;dest.mkdir(exist_ok=True,parents=True)
 def read_pages(nums):
    miss=[n for n in nums if not (dest/f'{n:04}.json').exists()]
    if miss:
        with tempfile.TemporaryDirectory(dir=BASE) as td:
            t=Path(td)
            if name=='vision':
                subset=fitz.open()
                for n in miss:subset.insert_pdf(pdf,from_page=n-1,to_page=n-1)
                subset.save(t/'pages.pdf');subset.close()
                cp=subprocess.run([exe,str(t/'pages.pdf'),str(len(miss))],capture_output=True,timeout=max(70,len(miss)*15),check=True)
                output=json.loads(cp.stdout);assert len(output)==len(miss)
            elif name=='tesserocr':
                from PIL import Image
                sys.path.insert(0,str(BASE/'runtime'));import tesserocr
                output=[]
                with tesserocr.PyTessBaseAPI(path=str(BASE/'tessdata'),lang='eng',psm=tesserocr.PSM.AUTO) as api:
                    for n in miss:
                        pix=pdf[n-1].get_pixmap(dpi=180,alpha=False)
                        api.SetImage(Image.open(io.BytesIO(pix.tobytes('png'))));api.SetSourceResolution(180)
                        output.append([line for line in api.GetUTF8Text().splitlines() if line.strip()])
            else:
                output=[]
                for n in miss:
                    pix=pdf[n-1].get_pixmap(dpi=180,alpha=False);png=pix.tobytes('png')
                    cp=subprocess.run([exe,'stdin','stdout','-l','eng','--psm','3'],input=png,capture_output=True,timeout=35,check=True)
                    output.append([v for v in cp.stdout.decode('utf8','replace').splitlines() if v.strip()])
            for n,lines in zip(miss,output):
                s='\n'.join(lines);z=dict(sha256=sh,pdf_page=n,text_sha256=digest(s.encode()),lines=lines,ocr_characters=len(s),**meta)
                textjson(dest/f'{n:04}.json',z)
    recs=[c.read(dest/f'{n:04}.json',{}) for n in nums]
    for r in recs:
        if r.get('sha256')!=sh or r['text_sha256']!=digest('\n'.join(r['lines']).encode()):raise ValueError('OCR receipt mismatch')
    return recs
 try:
    first=read_pages(pick(pdf,slot));added=follow(len(pdf),first,slot['follow_budget']);read_pages(added)
    textjson(BASE/'runs'/(sh+'.json'),dict(sha256=sh,first=[x['pdf_page'] for x in first],follow_up=added,source_pages=len(pdf),status='done'))
 except Exception as e:
    textjson(BASE/'runs'/(sh+'.json'),dict(sha256=sh,status='error',error=f'{type(e).__name__}: {e}'[:320]))
 finally:pdf.close()
def collect(docs,plan):
 slots={d['sha256']:d for d in plan};out=[];doc_reports=[];engine_mix=collections.Counter()
 total_pages=0;ocr_pages=0;legible=0;hits=[];hist=collections.Counter()
 for sh,d in sorted(docs.items()):
    slot=slots.get(sh);run=c.read(BASE/'runs'/(sh+'.json'),{});pp={}
    if slot:
        for path in sorted((BASE/'pages'/sh).glob('*.json')):
            z=c.read(path,{});txt='\n'.join(z['lines'])
            if z['sha256']!=sh or z['text_sha256']!=digest(txt.encode()) or not 1<=z['pdf_page']<=d['pages']:raise ValueError('Damaged or invalid page receipt: '+str(path))
            n=z['pdf_page'];pp[n]=z;out.append(z);engine_mix[z['engine']]+=1
            for m in list(DC.finditer(' '.join(z['lines'])))[:5]:
                s=' '.join(z['lines']);hits.append(dict(sha256=sh,pdf_page=n,text_sha256=z['text_sha256'],match=m.group(),context=s[max(0,m.start()-70):m.end()+85]))
    hpages=sorted({z['pdf_page'] for z in hits if z['sha256']==sh});present=sorted(pp);leg=sum(z['ocr_characters']>=80 for z in pp.values());legible+=leg;ocr_pages+=len(present)
    if slot:total_pages+=d['pages']
    status='unsampled' if not slot else 'OCR run error or incomplete' if run.get('status')!='done' else 'full OCR attempted' if len(present)==d['pages'] else 'partial OCR only'
    hist[status]+=1
    doc_reports.append(dict(sha256=sh,source_bytes=(ORIGINAL/(sh+'.pdf')).stat().st_size,urls=' | '.join(d['urls']),source_referrals=' | '.join(sorted({r['referral'] for r in d['refs']})),url_count=len(d['urls']),states=';'.join(d['states']),geoids=';'.join(d['geoids']),names=' | '.join(sorted({r['jurisdiction'] for r in d['refs']})),markers=d['markers'],best_state_rank=d['rank'],label=d['label'],pdf_pages=d['pages'],selection=slot['reason'] if slot else '',page_status=status,ocr_pdf_pages=';'.join(map(str,present)),follow_up_pages=';'.join(map(str,run.get('follow_up',[]))),unread_pages=d['pages']-len(present),ocr_pages_with_80_characters=leg,keyword_hit_pages=';'.join(map(str,hpages)),error=run.get('error','')))
 with INVENTORY.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(doc_reports[0]));w.writeheader();w.writerows(doc_reports)
 payload=''.join(json.dumps(z,ensure_ascii=False,sort_keys=True)+'\n' for z in sorted(out,key=lambda x:(x['sha256'],x['pdf_page'])))
 PAGES.write_bytes(gzip.compress(payload.encode(),mtime=0))
 textjson(D/'codebook_ocr_hits.json',hits)
 textjson(SUMMARY,dict(cutoff='2026-11-15',source_population_urls=len({u for d in docs.values() for u in d['urls']}),source_population_unique_pdfs=len(docs),population_pdf_pages=sum(d['pages'] for d in docs.values()),empty_pdfs=sum(d['pages']==0 for d in docs.values()),no_text_criterion='Original scanner found zero pages with >80 characters of embedded text, not necessarily a blank PDF.',sampled_documents=len(plan),sampled_states=sorted({s for x in plan for s in x['states']}),selected_by=dict(collections.Counter(x['reason'] for x in plan)),sampled_document_total_pages=total_pages,selected_page_budget=sum(x['probe_budget']+x['follow_budget'] for x in plan),ocr_attempted_pages=ocr_pages,ocr_pages_with_at_least_80_characters=legible,unread_pages_in_sampled_docs=total_pages-ocr_pages,by_document_status=dict(hist),keyword_hits_documents=len({x['sha256'] for x in hits}),keyword_hit_pages=len({(x['sha256'],x['pdf_page']) for x in hits}),engines=dict(engine_mix),portable_page_receipts_sha256=digest(PAGES.read_bytes()),scope='OCR keyword search is a lead. Full OCR attempted does not establish legal absence. Every unselected or unread page remains unknown; a short or unreadable OCR result is not a negative finding.'))
 print('OCR:',len(out),'pages;',len(hits),'keyword contexts;',dict(hist))
def stage():
 authored=c.read(D/'codebook_ocr_claims.json',[]);visual=c.read(D/'codebook_ocr_visual_reviews.json',{});idx={};outs=[]
 inventory={r['sha256']:r for r in rows(INVENTORY)}
 for r in authored:
    sh=r['sha256'];pg=r['page'];key=r['id'];z=visual.get(key,{});src=inventory[sh]
    if sh!=z.get('sha256') or z.get('page')!=pg or z.get('url')!=r['url'] or str(pg) not in src['ocr_pdf_pages'].split(';') or r['geoid'] not in src['geoids'].split(';'):raise ValueError('Visual/coverage/issuer mismatch: '+key)
    page=c.read(BASE/'pages'/sh/f'{pg:04}.json',{})
    image=BASE/'review'/f'{sh[:8]}-{pg}.png'
    if z.get('review_png')!=str(image.relative_to(BASE)) or not image.exists() or digest(image.read_bytes())!=z.get('image_sha256') or page.get('text_sha256')!=z.get('ocr_text_sha256'):raise ValueError('Visual image or OCR digest mismatch: '+key)
    if r['url'] not in src['urls'].split(' | '):raise ValueError('URL not in original referral set: '+key)
    raw=ORIGINAL/(sh+'.pdf');assert digest(raw.read_bytes())==sh
    if c.address(r['url']) not in idx:
        dst=c.CACHE/(sh+'.bin')
        if not dst.exists():
            try:os.link(raw,dst)
            except OSError:shutil.copyfile(raw,dst)
        assert digest(dst.read_bytes())==sh
        p=c.CACHE/(sh+'.txt')
        if not p.exists():
            with fitz.open(raw) as doc:p.write_text('\n'.join('[Page '+str(i)+']\n'+g.get_text() for i,g in enumerate(doc,1)))
        lk=c.CACHE/(sh+'.links.json')
        if not lk.exists():textjson(lk,[])
        # Preserve native text as the shared snapshot. Separately pinned OCR informs visual inspection.
        receipt=c.read(BOOK/'checks'/(digest(r['url'].encode())+'.json'),{})
        idx[c.address(r['url'])]=dict(url=c.address(r['url']),resolved=receipt.get('resolved',r['url']),sha256=sh,text_sha256=digest(p.read_bytes()),bytes=raw.stat().st_size,adapter='scan_needs_review',fetched_at=receipt['checked'])
    outs.append({k:v for k,v in r.items() if k not in ('sha256','page')})
 textjson(BASE/'reviewed_index.json',idx);textjson(D/'codebook_ocr_rules.json',outs);print('Visually reviewed provisions:',len(outs))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ocr',action='store_true');p.add_argument('--claims',action='store_true');p.add_argument('--verify',action='store_true',help='Verify all sampled original hashes, coverage, portable receipts and staged visual reviews.');p.add_argument('--engine',choices=('auto','vision','tesseract','tesserocr'),default='auto');p.add_argument('--docs',type=int,default=60);p.add_argument('--page-budget',type=int,default=365);p.add_argument('--workers',type=int,default=3);a=p.parse_args()
 if not 1<=a.docs<=180 or not 1<=a.page_budget<=1500 or not 1<=a.workers<=4:p.error('docs 1–180, page budget 1–1500, workers 1–4')
 BASE.mkdir(exist_ok=True,parents=True);docs=make_inventory()
 if not PLAN.exists():
    if not a.ocr:raise SystemExit('Missing frozen plan: run with --ocr first')
    textjson(PLAN,select(docs,a.docs,a.page_budget))
 plan=c.read(PLAN,[])
 if a.ocr:
    e=engine(a.engine)
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i,_ in enumerate(ex.map(process,plan,repeat(e)),1):
            if i%10==0:print('Completed',i,'of',len(plan),flush=True)
 collect(docs,plan)
 if a.claims or a.verify:stage()
 if a.verify:
    summary=c.read(SUMMARY,{});auth=c.read(D/'codebook_ocr_claims.json',[]);visual=c.read(D/'codebook_ocr_visual_reviews.json',{});reviewed=c.read(BASE/'reviewed_index.json',{});by=rows(INVENTORY)
    allp=[json.loads(line) for line in gzip.decompress(PAGES.read_bytes()).splitlines()]
    pairs={(p['sha256'],p['pdf_page']) for p in allp}
    assert len(pairs)==len(allp)==summary['ocr_attempted_pages']<=summary['selected_page_budget']
    assert len({r['sha256'] for r in by})==len(by)==summary['source_population_unique_pdfs']
    assert sum(int(x['pdf_pages']) for x in by)==summary['population_pdf_pages']
    for x in by:
        pp={int(n) for n in x['ocr_pdf_pages'].split(';') if n}
        assert pp=={n for h,n in pairs if h==x['sha256']} and len(pp)+int(x['unread_pages'])==int(x['pdf_pages'])
    for slot in plan:
        sh=slot['sha256'];assert digest((ORIGINAL/(sh+'.pdf')).read_bytes())==sh
    for z in allp:assert digest('\n'.join(z['lines']).encode())==z['text_sha256']
    assert {x['id'] for x in auth}==set(visual) and len(visual)==len(auth)
    assert {c.address(x['url']) for x in auth}==set(reviewed)
    for x in auth:
        assert (x['sha256'],x['page']) in pairs and x['id'].startswith('ocr-')
    assert not any(('gibraltar' in x['id'] or 'lexington' in x['id']) for x in auth)
    textjson(D/'codebook_ocr_validation.json',dict(passed=True,source_population_digest=digest((BASE/'population.json.gz').read_bytes()),sample_cohort_digest=digest(PLAN.read_bytes()),original_source_hashes_verified=len(plan),receipt_hashes_verified=len(allp),intact_page_numbers=True,complete_coverage_accounting=True,provisions=len(auth),accepted_originals=len(reviewed),image_reviews_verified=len(visual),pages_artifact_digest=digest(PAGES.read_bytes()),visual_manifest_digest=digest((D/'codebook_ocr_visual_reviews.json').read_bytes()),rule_artifact_digest=digest((D/'codebook_ocr_rules.json').read_bytes())))
    print('Verified original hashes, page coverage, OCR receipts and',len(auth),'visual claims.')
if __name__=='__main__':main()
