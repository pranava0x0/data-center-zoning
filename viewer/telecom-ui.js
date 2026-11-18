'use strict';
const T=window.TELECOM;
function telecomRows(kind=''){
 const locations=new Map();for(const l of T.locations){if(!locations.has(l.instrument_id))locations.set(l.instrument_id,[]);locations.get(l.instrument_id).push(l)}
 const instruments=new Map(T.instruments.map(i=>[i.id,i]));
 const located=(r,id)=>{const ls=locations.get(id)||[];return {...r,locations:ls,state:ls[0]?.state,locality:ls.map(l=>l.locality).join('; '),geoid:ls[0]?.geoid}};
 return [...T.provisions.map(p=>({...p,row_kind:'requirement',locality:p.jurisdiction})),...T.instruments.map(i=>located({...i,row_kind:'instrument'},i.id)),...T.events.map(e=>located({...e,title:e.action,row_kind:'event',issuer:e.assignee,identifier:instruments.get(e.instrument_id)?.identifier,description:instruments.get(e.instrument_id)?.description},e.instrument_id))].filter(r=>!kind||r.row_kind===kind);
}
function telecomScope(rows,st,id){return rows.filter(r=>(r.locations||[{state:r.state,geoid:r.geoid}]).some(l=>(!st||l.state===st)&&(!id||l.geoid===id||places.get(id)?.[2]==='state'&&l.state===places.get(id)[1])))}
function telecomCard(r){
 const p=el('article',null,'rowcard telecom-card'),h=el('div',null,'cardhead');h.append(el('h3',r.title),extLink('Source',r.url));
 p.append(h,el('p',r.locality+', '+r.state+(r.issuer?' · '+r.issuer:''),'where'),el('p',nice(r.row_kind)+(r.record_type==='agency_guidance'?' · agency guidance':'')+(r.date?' · '+r.date:'')+(r.status?' · '+r.status:''),'strip'),el('p',r.summary||r.description,'brief'));
 if(r.row_kind==='instrument')p.append(el('p','ROW authority: '+r.row_controller+'. Current validity: '+r.validity+'.','brief'));
 const d=el('details',null,'record'),dl=el('dl');d.append(el('summary','Details'),dl);
 for(const [label,value] of [['Citation',r.locator],['Applicant',r.applicant],['Identifier type',r.identifier_type],['Original target',r.original_target],['Revised target',r.revised_target],['Actual completion',r.completion_date],['Source inconsistency',r.source_inconsistency?'The application is approved but a substep remains in progress.':null],['Data-center relationship',r.data_center_relationship],['Source excerpt',r.evidence],['Retrieved',r.retrieved_at],['Source SHA-256',r.source_sha256]])if(value){dl.append(el('dt',label),el('dd',value))}
 if(r.row_kind==='instrument'){const events=T.events.filter(e=>e.instrument_id===r.id);const list=el('ol');for(const e of events.sort((a,b)=>a.date.localeCompare(b.date))){const li=el('li');li.append(e.date+' · '+e.action+' ',extLink('Source',e.url));list.append(li)}dl.append(el('dt','Dated actions'),el('dd'));dl.lastChild.append(list)}
 p.append(d);return p;
}
function telecomUpdate(st,j,q){
 const kind=$('telecomKind').value;visible=telecomScope(telecomRows(kind),st,j).filter(r=>q.every(w=>JSON.stringify(r).toLowerCase().includes(w)));
 $('overview').replaceChildren(el('p',visible.length+' '+(kind?nice(kind)+' records':'requirements, instruments and dated actions')+'. Applications and easement votes do not count as issued permits.'));
 $('context').hidden=false;$('context').replaceChildren(el('p','Virginia pilot. VDOT controls its own ROW permissions; county and town processes apply only where those authorities control the property. No data-center customer is established for these records.'));
 render();
}
function telecomCoverage(){
 const authorities=['VDOT','Fairfax County','Town of Leesburg','Loudoun County'];const reviewed=new Set(T.coverage.filter(c=>c.source_review==='verified').map(c=>c.authority));
 return Math.round(reviewed.size/authorities.length*100)+'% of Virginia pilot authority source checks ('+reviewed.size+'/'+authorities.length+'). History completeness unknown. Leesburg access blocked; Loudoun county process unreviewed.';
}
