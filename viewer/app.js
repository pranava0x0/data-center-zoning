'use strict';
const $=id=>document.getElementById(id),el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e};
const A=window.ATLAS,G=window.GEOGRAPHY,H=window.HISTORY_INDEX;
let federalOnly=false;const dataCenterCountExplanation=$('countExplanation').textContent;
const places=new Map(A.geo.map(g=>[g[0],g])),sn=new Map(A.geo.filter(g=>g[2]==='state').map(g=>[g[1],g[3]]));
const ok=r=>['snapshot_match','visual_source_check'].includes(r.check),nice=s=>String(s??'').replace(/[_-]/g,' ').replace(/^./,m=>m.toUpperCase());
function options(s,entries,all){const old=s.value;s.replaceChildren(new Option(all,''),...entries.map(([v,t])=>new Option(t,v)));if([...s.options].some(o=>o.value===old))s.value=old}
function norm(s,st){const v=String(s||'').toLowerCase().trim().replace(/^(city|town|village) of /,'');return H.nameExceptions[st]?.includes(v)?v:v.replace(/ (city|town|village)$/,'')}
const byName=new Map();for(const g of A.geo){const k=g[1]+'|'+norm(g[3],g[1]);byName.set(k,byName.has(k)?null:g)}
function matchPlace(st,name){return byName.get(st+'|'+norm(name,st))}
const hcounts=new Map();for(const [st,areas] of Object.entries(H.areas)){let sum=0;for(const [name,num] of Object.entries(areas)){const k=st+'|'+norm(name,st);hcounts.set(k,(hcounts.get(k)||0)+num);sum+=num}hcounts.set(st,H.totals[st])}
function historyCount(st,name){return hcounts.get(name?st+'|'+norm(name,st):st)||0}
function jkey(r){return r.map_geoid||r.state+':'+r.jurisdiction}
const scoped=new Map();
for(const r of A.rules)scoped.set(jkey(r),[r.state,r.jurisdiction]);
for(const [st,areas] of Object.entries(H.areas))for(const name of Object.keys(areas)){const id=matchPlace(st,name)?.[0]||st+':'+name;if(!scoped.has(id))scoped.set(id,[st,name])}
for(const loc of T.locations)if(!scoped.has(loc.geoid))scoped.set(loc.geoid,[loc.state,loc.locality]);
let mode='rules',extra='',visible=[],rulePage=0,generation=0,mapOnly=false;let facet="",scope="";const scopeNames={rules:[["dc","Data center"],["general","General"]],permits:[["dc","Data center land-use cases"],["general","Other permit history"]]};const isDC=r=>mode==="rules"?r.scope_class!=="general":r.review_class===1;function inScope(r){return !scope||isDC(r)===(scope==="dc")}const stateRows=new Map(),size=8;
options($('state'),[...sn].sort((a,b)=>a[1].localeCompare(b[1])),'All states');
options($('family'),[...new Set(A.rules.map(r=>r.category))].sort().map(t=>[t,t]),'All topics');
options($('pathway'),[...new Set(A.rules.flatMap(r=>r.pathways.map(p=>p.path)))].sort().map(t=>[t,nice(t)]),'All pathways');
function juris(){const st=$('state').value,d=new Map([...scoped].filter(([id,[s]])=>!st||st===s).map(([id,[s,name]])=>[id,name+(st?'':' · '+s)]));if(extra&&places.has(extra))d.set(extra,places.get(extra)[3]);options($('jur'),[...d].sort((a,b)=>a[1].localeCompare(b[1])),'All jurisdictions')}
function choose(st,id=''){extra=id;$('state').value=st;juris();$('jur').value=id;update()}
function alternateStates(rows){const groups=new Map();for(const r of rows){if(!groups.has(r.state))groups.set(r.state,[]);groups.get(r.state).push(r)}const out=[];for(let i=0;out.length<rows.length;i++)for(const list of groups.values())if(i<list.length)out.push(list[i]);return out}
function ruleTitle(r){if(r.topic==='use-permission'&&r.pathways.length){const paths=[...new Set(r.pathways.map(p=>nice(p.path)))].join(' / ');return paths+(r.district&&r.district.length<32?' · '+r.district:'')}return nice(r.topic)}
function extLink(label,url){const a=el('a',label);a.href=url;a.target='_blank';a.rel='noopener';return a}
async function fetchDetails(st){return window.PERMIT_DETAILS[st]??=(unpack(st+'-details'))}
const prTerms={
 'CONSULTA DE UBICACION':'Location consultation',
 'Determinación de Cumplimiento Ambiental vía Exclusión Categórica':'Environmental review: categorical exclusion',
 'Permiso para Generadores de Electricidad':'Generator permit',
 'Solicitud de Recomendación - Infraestructura':'Infrastructure referral',
 'Permiso de Construcción':'Construction permit',
 'Solicitud de Recomendación - Salud y Seguridad':'Health and safety referral',
 'Permiso de Construcción Consolidado':'Consolidated construction permit',
 'Pre-Consulta - Edificabilidad':'Preliminary building review',
 'Pre-Consulta - Medioambiente':'Preliminary environmental review',
 'Pre-Consulta - Departamento de Evaluación de Cumplimiento Ambiental':'Preliminary environmental compliance review',
 'Permiso Único':'Unified operating permit',
 'Permiso de Corteza Terrestre':'Earthmoving permit'
};
const monthNames=['January','February','March','April','May','June','July','August','September','October','November','December'];
function prettyDate(r){const d=r.date||'',m=r.month||'';if(/^\d{4}-\d{2}-\d{2}$/.test(d))return monthNames[+d.slice(5,7)-1]+' '+(+d.slice(8))+', '+d.slice(0,4);const v=d||m;if(/^\d{4}-\d{2}$/.test(v))return monthNames[+v.slice(5)-1]+' '+v.slice(0,4);return v}
function historyTitle(r){return r.state==='PR'&&r.title_basis!=='official'&&prTerms[r.kind]?r.title.replace(r.kind,prTerms[r.kind]):r.title}
const stemStatus=s=>String(s).toLowerCase().replace(/[^a-z]/g,'').slice(0,5);
const statusCodes={'Date Issued':'Issued',PER_ISSUED:'Issued',PER_REISS:'Reissued',EFF:'Effective',EXP:'Expired'};
function statusText(s){const t=String(s||'').trim();if(t.length<3)return '';const w=(statusCodes[t]||t).replace(/_/g,' ');return /[a-z]/.test(w)?w.replace(/^./,m=>m.toUpperCase()):w.toLowerCase().replace(/^./,m=>m.toUpperCase())}
const roleVerbs=[[/^(permit )?(issue date|issuance( date)?|date issued)$/i,'issued'],[/^(application( received| submitted)?( date)?|filing date|form filed|intake date)$/i,'filed'],[/^(approval|decision) date$/i,'decided'],[/^effective date$/i,'effective']];
function roleVerb(role0){const role=role0.replace(/\s*\([^)]*\)/g,'').trim().replace(/ completion date$/i,' completed');for(const [re,v] of roleVerbs)if(re.test(role))return v;return /^[A-Z]{2,}/.test(role)?role:role.replace(/^./,m=>m.toLowerCase())}
function historySentence(r){const status=statusText(r.state==='PR'?({PERMIT_APPROVED:'Approved',PERMIT_CLOSED:'Closed',EXPIRED:'Expired','RESUELTO. ACLARA PARTICULARES':'Resolved; clarification issued'}[r.status]||r.status):r.status),when=prettyDate(r),role=String(r.date_role||'').trim();
 if(!when)return status?status+'. No date published.':'No date published.';
 const same=status&&role&&stemStatus(status)&&role.toLowerCase().includes(stemStatus(status).slice(0,4));
 if(!role||/^(date not|status date)/i.test(role))return status?status+' on '+when+'.':when+'.';
 const lower=roleVerb(role);
 return same?status+' on '+when+'.':status?status+'; '+lower+' '+when+'.':role.replace(/^./,m=>m.toUpperCase())+' '+when+'.'}
const rawDates=[['application_date','Filed'],['file_date','Filed'],['received_date','Received'],['issue_date','Issued'],['effective_date','Effective'],['expiration_date','Expires'],['termination_date','Ended']];
const rawText=[['Description',['description','work_description','document_description','source_description']],['Type of work',['permit_type','work_class','work_type','application_type','case_type']],['Address',['address']]];
const plainLocator=l=>l&&l.length<=100&&!/[=?]|https?:|OBJECTID|MatterId/i.test(l)&&/(page|\bp\.|\bpp\.|section|§|item|agenda|minutes|exhibit|sheet|attachment|pdf)/i.test(l);
function historyDetails(dl,r,raw){const d=raw&&typeof raw==='object'?raw:{},seen=new Set();const first=keys=>{for(const k of keys){const v=d[k];if(typeof v==='string'&&v.trim()&&v!=='None')return v.trim()}return ''};
 appendField(dl,'Source document',(()=>{const s=el('span');s.append(extLink('Open the record ↗',r.url));return s})());appendField(dl,'Where in the source',plainLocator(r.locator)?r.locator:'');
 for(const [label,keys] of rawText){const v=label==='Description'?first(keys)||r.preview:first(keys);appendField(dl,label,v)}
 appendField(dl,'Record number',r.record_no&&r.record_no.length<=40&&!r.record_no.includes(' / ')&&!r.title.includes(r.record_no)?r.record_no:'');appendField(dl,'Project',r.project&&!r.title.includes(r.project)&&r.project!==r.record_no&&!(r.record_no&&r.project.includes(r.record_no))&&r.project!==d.address?r.project:'');
 const when=prettyDate(r);if(when){appendField(dl,(r.date_role||'Date').replace(/^./,m=>m.toUpperCase()),when);seen.add(when)}
 for(const [k,label] of rawDates){const v=prettyIso(first([k]));if(v&&!seen.has(v)){appendField(dl,label,v);seen.add(v)}}
 const status=r.state==='PR'?({PERMIT_APPROVED:'Approved',PERMIT_CLOSED:'Closed',EXPIRED:'Expired'}[r.status]||r.status):r.status,extra=first(['reported_case_status']);appendField(dl,'Status as the agency reports it',[statusText(status),extra&&!extra.toLowerCase().includes(String(status).toLowerCase())&&!String(status).toLowerCase().includes(extra.toLowerCase())?statusText(extra):''].filter(Boolean).join('; '));
 if(r.state==='PR'&&prTerms[r.kind])appendField(dl,'Original register entry',r.kind+' · '+r.status);appendField(dl,'Linked to a data center by',linkText(d.dc_link,r,d));appendField(dl,'Register',r.dataset);if(r.issuer_verification==='inferred')appendField(dl,'Office','Inferred from the record type; the record does not name it');if(r.issuer_evidence&&r.issuer_evidence!==r.url)appendField(dl,'Source for the office',r.issuer_evidence)}
const DCWORDS=/data[\s_-]*(?:cent(?:er|re)s?|ctr\b|halls?\b|processing cent(?:er|re)|backup cent(?:er|re))|datacent(?:er|re)|hyperscale|server[\s-]*farm|colocation|co-location|high[\s-]performance[\s-]comput/i;
function quoteAround(s){s=String(s||'').replace(/\s+/g,' ').trim();const m=DCWORDS.exec(s);if(!m)return s.slice(0,80);let a=Math.max(0,m.index-35),b=Math.min(s.length,m.index+m[0].length+35);if(a)a=s.lastIndexOf(' ',a)+1;if(b<s.length){const n=s.indexOf(' ',b);b=n>0?n:s.length}return(a?'…':'')+s.slice(a,b).replace(/^[ ,;]+|[ ,;]+$/g,'')+(b<s.length?'…':'')}
function linkText(c,r,d){if(!c){const f=['title','project','kind'].find(k=>DCWORDS.test(r[k]||''));if(f)return'The record says “'+quoteAround(r[f])+'”';return H.datasetLinks[r.dataset]||(r.project?'Project named in the record: '+r.project:'')}const k=c[0],v=c.slice(1);if(k==='r'||k==='d')return'The record says “'+quoteAround(k==='r'?r[v]:d[v])+'”';return k==='p'?'Project named in the record: '+r.project:k==='q'?'The record says “'+v+'”':k==='f'?'Facility named in the record: '+r.project+' ('+v+')':v}
function historyCard(r){const p=el('article',null,'rowcard history-card'),head=el('div',null,'cardhead'),title=historyTitle(r),where=r.locality||r.county;head.append(el('h3',title),extLink('Source',r.url));head.lastChild.setAttribute('aria-label','Source for '+title);
 const wl=el('p',whereLine(where,r.state,r.issuer),'where');const meta=el('div',null,'meta');meta.append(wl);if(r.review_class===1)meta.append(el('span','Land-use case','tag'));p.append(head,meta,el('p',historySentence(r),'strip brief history-date'));

 const d=el('details',null,'record'),s=el('summary','Details'),b=el('div',null,'recbody'),dl=el('dl');historyDetails(dl,r,null);b.append(dl);d.append(s,b);p.append(d);
 if(r.case_group){const group=caseRows.get(r.case_group)||[];if(group.length>1){
   const timeline=el('details',null,'case-timeline');timeline.append(el('summary','Case history ('+group.length+')'));b.append(timeline);
   timeline.ontoggle=()=>{if(!timeline.open||timeline.querySelector('ol'))return;const list=el('ol');
     for(const item of [...group].sort((a,b)=>(b.date||b.month||'').localeCompare(a.date||a.month||''))){const li=el('li');li.append(el('time',item.date||item.month||'Undated'),el('span',item.kind+' · '+item.status+' '),extLink('Source',item.url));list.append(li)}timeline.append(list)}
 }}
 let busy=false;d.ontoggle=async()=>{if(!d.open||busy||b.dataset.loaded)return;busy=true;try{const raw=await fetchDetails(r.state);b.querySelector('.failure')?.remove();dl.replaceChildren();historyDetails(dl,r,raw[r.id]);b.dataset.loaded='yes'}catch{if(!b.querySelector('.failure'))b.append(el('p','More fields are unavailable. Reopen to retry, or use Source.','failure'))}finally{busy=false}};return p}
const caseRows=new Map();
async function loadState(st){if(!stateRows.has(st)){const rows=unpack(st).map(v=>Object.fromEntries(H.keys.map((k,i)=>[k,v[i]])));for(const r of rows)if(r.case_group){if(!caseRows.has(r.case_group))caseRows.set(r.case_group,[]);caseRows.get(r.case_group).push(r)}stateRows.set(st,rows)}return stateRows.get(st)}
function summary(rows){
 const box=$('overview');box.replaceChildren();const all=rows;rows=rows.filter(inScope);const cats=new Map();for(const r of rows)cats.set(r.category,(cats.get(r.category)||0)+1);
 const total=rows.length.toLocaleString(),states=new Set(rows.map(r=>r.state)).size,term=mode==='rules'?(rows.length===1?'rule':'rules'):$('bucket').value?'distinct permits':(rows.length===1?'public record':'public records');
 const info=el('p',total+' '+term+(states>1?' across '+states+' states and territories':''));box.append(info);
 if(mode==='permits'&&federalOnly){
   const only=$('bucket').value,n=rows.filter(r=>r.permit_representative).length;
   if(only||n){const toggle=el('button',only?'Show all federal records':'Show '+n.toLocaleString()+' distinct '+(n===1?'permit':'permits'),'text-button');toggle.id='federalInstruments';toggle.onclick=()=>{facet='';$('bucket').value=only?'':'permits';mapMetric=only?'active':'permits';update()};info.append(' · ',toggle)}
 }
 const seg=el('div',null,'scopes');seg.setAttribute('role','group');seg.setAttribute('aria-label','Data center or general');const dcN=all.filter(isDC).length;for(const [key,label] of [['','All'],...scopeNames[mode]]){const n=key==='dc'?dcN:key?all.length-dcN:all.length,b=el('button',label+' '+n.toLocaleString());b.setAttribute('aria-pressed',String(scope===key));b.title=key==='dc'?(mode==='rules'?'Rules written for data centers':'Rezoning, special exception and other land-use case records for a data center, whatever their status'):key?(mode==='rules'?'Rules every project follows, data centers included':'Building, trade, air, water and other permit records'):'';b.onclick=()=>{scope=key;facet='';update()};seg.append(b)}if(scope||(dcN&&dcN<all.length))box.append(seg);
 const wrap=el('div',null,'facets');box.append(wrap);
 const chooseFacet=key=>{facet=facet===key?'':key;update()};
 const sorted=[...cats].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));if(!cats.has(facet))facet='';
 for(const [key,n] of sorted.filter(([k],i)=>i<3||k===facet)){const b=el('button',key+' '+n.toLocaleString());b.setAttribute('aria-pressed',String(key===facet));b.onclick=()=>chooseFacet(key);wrap.append(b)}
 const other=sorted.slice(3).filter(([k])=>k!==facet);if(other.length){const sel=el('select');sel.setAttribute('aria-label','More topics');sel.append(new Option('More topics',''),...other.map(([k,n])=>new Option(k+' '+n.toLocaleString(),k)));sel.onchange=()=>chooseFacet(sel.value);wrap.append(sel)}
}
function render(){const list=$('list'),total=Math.ceil(visible.length/size);list.replaceChildren(...visible.slice(rulePage*size,(rulePage+1)*size).map(mode==='rules'?card:mode==='telecom'?telecomCard:historyCard));if(!visible.length)list.append(el('p',mode==='rules'?'No matching ordinance records.':mode==='telecom'?'No matching telecom records in this pilot.':'No matching permit records in this collection.','empty'));
 $('totals').textContent=visible.length.toLocaleString();const box=$('rulePages');box.replaceChildren();if(total>1){const prev=el('button','‹'),next=el('button','›');prev.setAttribute('aria-label','Previous page');next.setAttribute('aria-label','Next page');prev.disabled=!rulePage;next.disabled=rulePage>=total-1;prev.onclick=()=>{rulePage--;render()};next.onclick=()=>{rulePage++;render()};box.append(prev,el('span',(rulePage+1)+' / '+total),next)}$('export').disabled=!visible.length}
function mobileMap(show){mapOnly=show;$('federalOnly').hidden=mode!=='permits'&&(mode==='telecom'||!show);$('panels').classList.toggle('map-mode',show);for(const [id,active] of [['showMap',show],['showRecords',!show&&mode==='rules'],['historyLink',!show&&mode==='permits'],['telecomLink',!show&&mode==='telecom']])$(id).setAttribute('aria-pressed',String(active))}
function setMode(next){if(next==='telecom'&&mode!==next)$('telecomKind').value='';if(next!=='permits')federalOnly=false;if(next!==mode){mode=next;$('query').value='';facet='';scope=''}$('bucket').value='';mapMetric=next==='telecom'?'tc_rules':next==='permits'?'active':'rules';mobileMap(false);update()}
function selectMetric(k){if(k.startsWith('tc_')){mapMetric=k;mode='telecom';$('telecomKind').value={tc_rules:'requirement',tc_instruments:'instrument',tc_events:'event'}[k];mobileMap(mapOnly);update();return}if(k==='rules')federalOnly=false;mapMetric=k;mode=k==='rules'?'rules':'permits';$('bucket').value=k==='rules'?'':k;for(const id of ['year','register','family','pathway','query'])$(id).value='';$('held').checked=$('stateRules').checked=false;facet='';mobileMap(mapOnly);update()}
for(const b of document.querySelectorAll('[data-metric]'))b.onclick=()=>selectMetric(b.dataset.metric);
$('telecomLink').onclick=()=>setMode('telecom');$('telecomKind').onchange=()=>{mapMetric={requirement:'tc_rules',instrument:'tc_instruments',event:'tc_events'}[$('telecomKind').value]||'tc_rules';update()};$('printMap').onclick=()=>window.print();
$('historyLink').onclick=()=>setMode('permits');$('showRecords').onclick=()=>setMode('rules');$('showMap').onclick=()=>mobileMap(true);
function displayContext(st,j,name){const box=$('context');box.replaceChildren();box.hidden=!j;if(!j)return;
 const n=historyCount(st,name),rs=A.rules.filter(r=>jkey(r)===j&&ok(r)).length;
 if(mode==='rules'&&n||mode==='permits'&&rs){const btn=el('button',mode==='rules'?'See '+n.toLocaleString()+' permit records':'See '+rs+' verified '+(rs===1?'ordinance':'ordinances'));btn.onclick=()=>setMode(mode==='rules'?'permits':'rules');box.append(btn)}
 const g=places.get(j);if(g&&mode==='rules'&&!rs){const raw=g[6],desc=el('span',localSearchNote(g));box.append(desc);if(g[8])box.append(extLink('Local website',g[8]))}box.hidden=!box.children.length}
function syncURL(st,j,name){const p=new URLSearchParams();if(st)p.set('state',st);if(j){p.set('id',j);if(name)p.set('area',name)}if(mode==='telecom'){p.set('view','telecom');const ts=$('telecomScope')?.value;if(ts)p.set('telecom_scope',ts)}if(mode==='permits'){p.set('view','permits');if(federalOnly)p.set('issuer','federal');if($('bucket').value)p.set('status',$('bucket').value)}if(scope&&mode!=='telecom')p.set('scope',scope);if($('query').value)p.set('q',$('query').value);const hash=p.toString()?'#'+p:'';if(location.hash!==hash)try{history.replaceState(null,'',location.pathname+hash)}catch{}}
function update(){
 const seq=++generation,st=$('state').value,j=$('jur').value,g=places.get(j),name=scoped.get(j)?.[1]||g?.[3]||'',q=$('query').value.trim().toLowerCase().split(/\s+/).filter(Boolean);rulePage=0;
 $('federalGuide').hidden=!federalOnly;$('federalOnly').hidden=mode!=='permits'&&(mode==='telecom'||!mapOnly);$('federalOnly').setAttribute('aria-pressed',String(federalOnly));
 $('query').placeholder=mode==='rules'?'Rule, approval, issuer or keyword':'Project, permit title, issuer or number';$('resultTitle').textContent=mode==='telecom'?'Fiber & telecom rights-of-way':mode==='rules'?'Ordinances':metricNames[$('bucket').value]||(federalOnly?'Federal permit history':'Permit history');
 const coverageText=mode==='telecom'?telecomCoverage():'Data centers: '+H.coverage.percent+'% priority-locality evidence coverage ('+H.coverage.numerator+'/'+H.coverage.denominator+'). National ordinance completeness unknown. See Downloads for definitions and unresolved records.';const shortCoverage=mode==='telecom'?telecomCoverageShort():'Data centers: '+H.coverage.percent+'% priority places; incomplete.';const compactCoverage=el('a',shortCoverage,'coverage-short');compactCoverage.href='downloads.html';compactCoverage.title=coverageText;$('coverageNote').replaceChildren(el('span',coverageText,'coverage-full'),compactCoverage);document.querySelector('header h1').textContent=mode==='telecom'?'Fiber and telecom ROW':'Data center zoning';$('telecomFilters').hidden=mode!=='telecom';$('ruleFilters').hidden=mode!=='rules';$('permitFilters').hidden=mode!=='permits';$('filterButton').hidden=mode==='telecom';document.querySelector('.mapcounts').hidden=mode==='telecom';$('telecomMapCounts').hidden=mode!=='telecom';displayContext(st,j,name);syncURL(st,j,name);
 $('countExplanation').textContent=mode==='telecom'?'Requirements, instruments/applications and dated actions have separate counts. Applications and easement votes are not issued permits. One instrument counts once nationally, even when its locations appear in several local views. Gray means no matching atlas record; national completeness is unknown.':dataCenterCountExplanation;
 $('printTitle').textContent=(mode==='telecom'?'Fiber and telecom rights-of-way':'Data-center zoning and permits')+' · '+(name||sn.get(st)||'All states')+' · '+metricNames[mapMetric]+' · '+(mode==='telecom'?new Date(window.TELECOM.as_of+'T12:00:00').toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'}):'November 15, 2026');
 map(st,j);if($('coverageDetails').open)geoList();
 if(mode==='telecom'){telecomUpdate(st,j,q);return}
 const f=$('family').value,path=$('pathway').value;
 if(mode==='rules'){visible=A.rules.filter(r=>(!st||r.state===st)&&(!j||jkey(r)===j||($('stateRules').checked&&r.level==='state'&&r.state===st))&&(!f||r.category===f)&&(!path||r.pathways.some(p=>p.path===path))&&($('held').checked||ok(r))&&q.every(w=>(r._search??=JSON.stringify(r).toLowerCase()).includes(w)));if(!st&&!j&&!q.length)visible=alternateStates(visible);if(j)visible.sort((a,b)=>Number(!ok(a))-Number(!ok(b))||Number(b.topic==='use-permission')-Number(a.topic==='use-permission'));$('filterButton').textContent=f||path||$('held').checked||$('stateRules').checked?'Filters •':'Filters';summary(visible);visible=visible.filter(inScope);if(facet)visible=visible.filter(r=>r.category===facet);render();return}
 const sources=federalOnly?H.federalMetrics:H.areas,states=st?(sources[st]?[st]:[]):Object.keys(sources);
 function show(rr){if(seq!==generation)return;const locs=rr.filter(r=>!federalOnly||r.federal_issuer).filter(r=>!j||(g?.[2]==='state'?r.state===g[1]:(norm(r.locality,r.state)===norm(name,r.state)||norm(r.county,r.state)===norm(name,r.state))&&r.state===(st||scoped.get(j)?.[0]||g?.[1])));const year=r=>(r.date||r.month||'').slice(0,4)||'Undated';
 options($('register'),[...new Set(locs.map(r=>r.dataset))].sort().map(v=>[v,v]),'All registers');options($('year'),[...new Set(locs.map(year))].sort().reverse().map(v=>[v,v]),'All years');
 const reg=$('register').value,yr=$('year').value,bucket=$('bucket').value;$('filterButton').textContent=reg||yr||bucket?'Filters •':'Filters';visible=locs.filter(r=>(!bucket||(r.permit_representative&&(bucket==='permits'||r.permit_bucket===bucket)))&&(!reg||reg===r.dataset)&&(!yr||yr===year(r))&&q.every(w=>(r._search??=[r.title,r.issuer,r.project,r.record_no,r.kind,r.status,r.locality,r.county,r.preview,r.dataset,r.federal_issuer,r.date,r.month].join(' ').toLowerCase()).includes(w)));if(q.length){const exact=visible.filter(r=>String(r.record_no||'').toLowerCase()===q.join(' '));if(exact.length)visible=exact}if(states.length>1)visible.sort((a,b)=>(b.date||b.month||'').localeCompare(a.date||a.month||'')||a.id.localeCompare(b.id));summary(visible);visible=visible.filter(inScope);if(facet)visible=visible.filter(r=>r.category===facet);render()}
 if(states.every(s=>stateRows.has(s))){show(states.flatMap(s=>stateRows.get(s)));return}
 visible=[];$('overview').replaceChildren();$('list').replaceChildren(el('p','Loading permit records…','empty'));$('totals').textContent='';$('rulePages').replaceChildren();$('export').disabled=true;
 Promise.all(states.map(loadState)).then(data=>show(data.flat())).catch(()=>{if(seq!==generation)return;const retry=el('button','Retry');retry.onclick=update;$('list').replaceChildren(el('p','Permit records could not be loaded.','empty'),retry)})
}
$('state').onchange=()=>{facet='';choose($('state').value)};$('jur').onchange=()=>{facet='';const id=$('jur').value,st=scoped.get(id)?.[0]||places.get(id)?.[1];if(id&&!$('state').value&&st)choose(st,id);else update()};
for(const id of ['family','held','pathway','stateRules','register','year','bucket'])$(id).onchange=()=>{facet='';if(id==='bucket')mapMetric=$('bucket').value||'rules';update();if($('more').matches(':popover-open'))$('more').hidePopover()};
$('query').oninput=update;$('geosearch').oninput=geoList;$('coverageDetails').ontoggle=()=>{if($('coverageDetails').open)geoList()};$('national').onclick=()=>choose('');
$('federalOnly').onclick=()=>{federalOnly=!federalOnly;mode='permits';facet='';$('register').value=$('bucket').value='';mapMetric='active';mobileMap(mapOnly);update()};
$('reset').onclick=()=>{federalOnly=false;scope='';for(const id of ['query','family','pathway','geosearch','year','register','bucket'])$(id).value='';$('held').checked=$('stateRules').checked=false;facet='';$('telecomKind').value='';mapMetric=mode==='telecom'?'tc_rules':'rules';choose('')};
$('export').onclick=()=>{if(!visible.length)return;const cols=mode==='telecom'?[...new Set(visible.flatMap(r=>Object.keys(r)))]:mode==='rules'?['id','state','jurisdiction','card_title','card_issuer','card_role','card_role_evidence','card_role_quote','card_process','card_sentence','category','topic','scope','summary','document_status','district','pathways','adopted','effective','expires','thresholds','authority','locator','evidence','url','check','sha256']:H.keys;
 const esc=v=>{let s=typeof v==='object'&&v!==null?JSON.stringify(v):String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"'};const blob=new Blob([[cols,...visible.map(r=>cols.map(k=>r[k]))].map(row=>row.map(esc).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});const u=URL.createObjectURL(blob),a=el('a');a.href=u;a.download=mode+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
function openLocation(){
$('telecomKind').value='';facet='';for(const id of ['family','pathway','year','register','bucket'])$(id).value='';
$('held').checked=$('stateRules').checked=false;
const args=new URLSearchParams(location.hash.slice(1)||location.search),st=args.get('state')==='all'?'':sn.has(args.get('state'))?args.get('state'):args.has('area')?'VA':'';
mode=args.get('view')==='telecom'?'telecom':args.get('view')==='permits'?'permits':'rules';if(mode==='telecom'&&$('telecomScope')&&args.get('telecom_scope'))$('telecomScope').value=args.get('telecom_scope');federalOnly=mode==='permits'&&args.get('issuer')==='federal';mapMetric=mode==='telecom'?'tc_rules':mode==='permits'?'active':'rules';$('query').value=args.get('q')||'';scope=['dc','general'].includes(args.get('scope'))?args.get('scope'):'';if(mode==='permits'&&['active','historical','unconfirmed','permits'].includes(args.get('status'))){mapMetric=args.get('status');$('bucket').value=mapMetric}mobileMap(false);
const area=args.get('area');choose(st,args.get('id')||matchPlace(st,area)?.[0]||(area&&H.areas[st]?.[area]?st+':'+area:''));
}
window.addEventListener('hashchange',openLocation);openLocation();
