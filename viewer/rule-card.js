function appendField(dl,k,v){if(v==null||v==='')return;const dd=el('dd');if(v instanceof Node)dd.append(v);else dd.textContent=typeof v==='string'?v:JSON.stringify(v);dl.append(el('dt',k),dd)}
function prettyIso(d){const m=/^(\d{4})-(\d{2})-(\d{2})/.exec(d||'');return m?monthNames[+m[2]-1]+' '+(+m[3])+', '+m[1]:d||''}
function placeName(name,st){const full=sn.get(st);return !name||name===full?(full||st):name+', '+st}
function office(who,name){const w=String(who||'').trim();if(!name)return w;for(const p of [name,'City of '+name,'Town of '+name,'Village of '+name,'Township of '+name,name+' County',name+' City']){if(w.startsWith(p+' ')){const rest=w.slice(p.length+1);if(/^[A-Z]/.test(rest)&&rest.length>3)return rest}}return w}
function whereLine(place,st,who){const w=String(who||'').trim();if(w&&place){if(place===w)return placeName(place,st);if(place.startsWith(w+' — ')){let d=place.slice(w.length+3);if(/Corps of Engineers/.test(w)&&!/District$/.test(d))d+=' District';return d+', '+st+' · '+w}}return placeName(place,st)+' · '+office(w,place)}
function linkTo(label,url){const a=el('a',label);a.href=url;a.target='_blank';a.rel='noopener';return a}
function listNode(items){const ul=el('ul');for(const t of items)ul.append(el('li',t));return ul}
const docTypes={adopted:'Adopted law or ordinance',agency_guidance:'Agency guidance, not an adopted rule',official_adoption_summary:'Official summary of an adopted ordinance',issued_permit:'Issued permit'};
const opWords={'>':'over','>=':'at least','<':'under','<=':'up to','=':'','==':''},unitWords={ft2:'sq ft',sqft:'sq ft',gpd:'gallons a day',mw:'MW',kw:'kW',dba:'dBA'};
function threshold(t){const unit=unitWords[String(t.unit||'').toLowerCase()]||t.unit||'',value=typeof t.value==='number'?t.value.toLocaleString():t.value,label=nice(t.metric).replace(/gfa/i,'gross floor area').replace(/\bmw\b/i,'MW');
 return label+': '+[opWords[t.operator]??t.operator,value,unit].filter(v=>v!==''&&v!=null).join(' ')+(t.context?' ('+String(t.context).replace(/\.$/,'')+')':'')}
function conditions(r){const th=(r.thresholds||[]).map(threshold),out=th.length?th:r.trigger?[String(r.trigger).replace(/\.$/,'')]:[];for(const p of r.pathways||[])if(p.qualifier&&!out.includes(p.qualifier)&&!(th.length&&/\d{4,}/.test(p.qualifier)))out.push(p.qualifier);return out}
function card(r){const panel=el('article',null,'rowcard'),head=el('div',null,'cardhead'),linkOut=linkTo('Source',r.url);head.append(el('h3',r.card_title),linkOut);linkOut.setAttribute('aria-label','Source for '+r.card_title);
 panel.append(head,el('p',whereLine(r.jurisdiction,r.state,r.card_issuer),'where'),el('p',(ok(r)?'':'Not yet verified. ')+r.card_sentence,'strip brief'));
 const e=el('details',null,'record'),body=el('div',null,'recbody'),dl=el('dl'),src=el('span');src.append(linkTo('Open the source document ↗',r.url));
 for(const [k,label] of [['primary_document','Governing document'],['corroborating_url','Corroborating source']])if(r[k])src.append(' · ',linkTo(label+' ↗',r[k]));
 appendField(dl,'Source document',src);appendField(dl,'Where in the source',r.locator);
 if(r.evidence){const q=el('blockquote','“'+r.evidence+'”','quote');appendField(dl,'Quote',q)}
 const cond=conditions(r);if(cond.length)appendField(dl,'Conditions and exceptions',cond.length===1?cond[0]:listNode(cond));
 if(r.summary&&r.summary!==r.card_sentence)appendField(dl,'Summary',r.summary);
 if(r.card_process)appendField(dl,'How it is decided',r.card_process.replace(/^./,m=>m.toUpperCase()));
 appendField(dl,'Office role evidence',r.card_role_evidence);
 appendField(dl,'Adopted',prettyIso(r.adopted));appendField(dl,'Effective',prettyIso(r.effective));appendField(dl,'Expires',prettyIso(r.expires));
 appendField(dl,'Document type',docTypes[r.document_status]||nice(r.document_status));
 body.append(dl);e.append(el('summary','Details'),body);panel.append(e);return panel}
