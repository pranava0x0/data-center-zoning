'use strict';
const T=window.TELECOM;
const TELECOM_SCOPES={data_center_specific:'Data center connectivity',general:'General fiber & telecom'};
/* Category filter. Built here (no template change): inserted after #telecomFilters and shown or hidden with it. */
function telecomScopeValue(){const s=document.getElementById('telecomScope');return s?s.value:''}
(function telecomScopeControl(){
 const build=()=>{
  const anchor=document.getElementById('telecomFilters');if(!anchor||document.getElementById('telecomScope'))return;
  const label=document.createElement('label'),select=document.createElement('select');label.id='telecomScopeFilter';select.id='telecomScope';label.hidden=anchor.hidden;
  for(const [v,t] of [['','All fiber & telecom'],['data_center_specific',TELECOM_SCOPES.data_center_specific],['general',TELECOM_SCOPES.general]]){const o=document.createElement('option');o.value=v;o.textContent=t;select.append(o)}
  label.append('Category',select);anchor.after(label);
  new MutationObserver(()=>{label.hidden=anchor.hidden}).observe(anchor,{attributes:true,attributeFilter:['hidden']});
  select.addEventListener('change',()=>{if(typeof update==='function')update()});
  /* Reset clears the category too; capture runs before the page's own reset handler redraws. */
  document.addEventListener('click',e=>{if(e.target&&e.target.closest&&e.target.closest('#reset'))select.value=''},true);
 };
 build();if(!document.getElementById('telecomScope')&&document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);
})();
function telecomRows(kind=''){
 const locations=new Map();for(const l of T.locations){if(!locations.has(l.instrument_id))locations.set(l.instrument_id,[]);locations.get(l.instrument_id).push(l)}
 const instruments=new Map(T.instruments.map(i=>[i.id,i]));
 const located=(r,id)=>{const ls=locations.get(id)||[];return {...r,locations:ls,state:ls[0]?.state,locality:ls.map(l=>l.locality).join('; '),geoid:ls[0]?.geoid}};
 const labelled=r=>({...r,category_label:TELECOM_SCOPES[r.scope_class]||''});
 const scope=telecomScopeValue();
 return [...T.provisions.filter(p=>p.publication_status!=='held').map(p=>labelled({...p,row_kind:'requirement',locality:p.jurisdiction})),...T.instruments.map(i=>labelled(located({...i,row_kind:'instrument'},i.id))),...T.events.map(e=>{const i=instruments.get(e.instrument_id)||{};return labelled(located({...e,title:e.action,row_kind:'event',issuer:e.assignee,identifier:i.identifier,work_description:i.description,brief:e.brief,scope_class:i.scope_class,scope_basis:i.scope_basis},e.instrument_id))})].filter(r=>(!kind||r.row_kind===kind)&&(!scope||r.scope_class===scope));
}
function telecomScope(rows,st,id){return rows.filter(r=>(r.locations||[{state:r.state,geoid:r.geoid}]).some(l=>(!st||l.state===st)&&(!id||l.geoid===id||places.get(id)?.[2]==='state'&&l.state===places.get(id)[1])))}
function telecomPlace(r){
 const names=typeof sn!=='undefined'&&sn.get?sn.get(r.state):'';
 const where=r.locality&&r.locality!==names?r.locality+(r.state?', '+r.state:''):(names||r.state||'');
 return where+(r.issuer?' · '+r.issuer:'');
}
function telecomCard(r){
 const p=el('article',null,'rowcard telecom-card'),h=el('div',null,'cardhead');h.append(el('h3',r.title),extLink('Source',r.url));
 const where=el('p',telecomPlace(r),'where');if(r.category_label){const b=el('span',r.category_label,'tc-scope tc-scope-'+(r.scope_class==='data_center_specific'?'dc':'general'));where.append(' ',b)}
 if(r.row_kind==='requirement')where.append(' · '+nice(r.record_type));
 p.append(h,where,el('p',r.brief||r.summary||r.description,'brief'));
 const d=el('details',null,'record'),dl=el('dl');d.append(el('summary','Details'),dl);
 const source=el('span');source.append(r.source_title?r.source_title+' ':'',extLink('Open the record ↗',r.url));
 appendField(dl,'Category',r.category_label?r.category_label+(r.scope_basis?'. '+r.scope_basis:''):'');
 appendField(dl,'Source document',source);
 appendField(dl,'Where in the source',r.locator);
 appendField(dl,'Requirement and conditions',r.summary&&r.summary!==r.brief?r.summary:'');
 appendField(dl,'Quote',r.evidence?'“'+r.evidence+'”':'');
 appendField(dl,'Document status',r.document_status?nice(r.document_status):'');
 appendField(dl,'Applies to',r.applies_to);
 appendField(dl,'Source capture',r.source_capture_method);
 appendField(dl,'Identifier',r.identifier?(r.identifier_type?r.identifier_type.replace(/_/g,' ')+' ':'')+r.identifier:'');
 appendField(dl,'Applicant',r.applicant);
 appendField(dl,'Effective',r.effective);
 appendField(dl,'Date',r.row_kind==='event'?r.date+(r.date_role?' ('+r.date_role+')':''):'');
 appendField(dl,'Agency original target date',r.original_target);appendField(dl,'Agency revised target date',r.revised_target);appendField(dl,'Agency completion date',r.completion_date);
 appendField(dl,'Status as the agency reports it',r.status_reported||r.status);
 appendField(dl,'ROW authority in the source',r.row_kind==='instrument'?r.row_controller:'');
 appendField(dl,'Authority basis',r.row_kind==='instrument'?r.row_control_basis:'');
 appendField(dl,'Authority source',r.row_kind==='instrument'&&r.row_control_source_url?extLink('Official authority source',r.row_control_source_url):'');
 appendField(dl,'Current validity',r.row_kind==='instrument'?r.validity:'');
 appendField(dl,'Source inconsistency',r.source_inconsistency?'The application is approved but a substep remains in progress.':'');
 appendField(dl,'Linked to a data center by',r.row_kind==='instrument'?r.data_center_relationship:'');
 appendField(dl,'Step description',r.row_kind==='event'?r.description:'');
 appendField(dl,'Work description',r.row_kind==='instrument'?r.description:r.row_kind==='event'?r.work_description:'');
 appendField(dl,'Retrieved',r.retrieved_at);appendField(dl,'Source SHA-256',r.source_sha256);
 if(r.row_kind==='instrument'){const events=T.events.filter(e=>e.instrument_id===r.id);if(events.length){const list=el('ol');for(const e of events.sort((a,b)=>a.date.localeCompare(b.date))){const li=el('li');li.append(e.date+' · '+e.action+' ',extLink('Source',e.url));list.append(li)}const dd=el('dd');dd.append(list);dl.append(el('dt','Dated actions'),dd)}}
 p.append(d);return p;
}
function telecomUpdate(st,j,q){
 const kind=$('telecomKind').value;visible=telecomScope(telecomRows(kind),st,j).filter(r=>q.every(w=>JSON.stringify(r).toLowerCase().includes(w)));
 const dc=visible.filter(r=>r.scope_class==='data_center_specific').length,held=T.provisions.filter(p=>p.publication_status==='held').length;
 $('overview').replaceChildren(el('p',visible.length+' '+(kind?nice(kind)+' records':'requirements, instruments and dated actions')+' ('+dc+' data-center-specific, '+(visible.length-dc)+' general fiber & telecom). Applications and easement votes do not count as issued permits.'));
 $('context').hidden=false;$('context').replaceChildren(el('p','Data center connectivity records name data centers; some concern network equipment without naming fiber. General records cover the providers and work stated in each source. '+held+' research holds, including unadopted proffers and unverified historical text, are separate in Downloads.'));
 render();
}
function telecomCoverage(){
 const c=T.coverage_summary,v=c.virginia,p=c.pilot;
 return 'Virginia: '+v.numerator+'/'+v.denominator+' authority source checks ('+v.percent+'%; '+c.roster_vintage+' local-government roster plus VDOT). Original pilot: '+p.numerator+'/'+p.denominator+' ('+p.percent+'%). Leesburg permit process remains blocked; charter review is partial. Histories are bounded samples. National completeness unknown.';
}
function telecomCoverageShort(){return 'Telecom: '+T.coverage_summary.virginia.percent+'% VA source checks; incomplete.'}
