'use strict';
const ns='http://www.w3.org/2000/svg';
function svg(tag,attrs){const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n}
const rad=Math.PI/180,p1=29.5*rad,p2=45.5*rad,n=(Math.sin(p1)+Math.sin(p2))/2,c0=Math.cos(p1)**2+2*n*Math.sin(p1);
function project([lon,lat]){const rho=Math.sqrt(c0-2*n*Math.sin(lat*rad))/n,t=n*(lon+96)*rad;return [rho*Math.sin(t)*1000,rho*Math.cos(t)*1000]}
const outlying=new Set(['AK','HI','PR','GU','MP','AS','VI']);
const geometryCache=new Map();
function geometry(st){
 if(geometryCache.has(st))return geometryCache.get(st);
 const fs=st?G.county.filter(f=>f[0]===st):G.state.filter(f=>!outlying.has(f[0]));let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;
 const shapes=fs.map(([state,id,name,rings,point])=>({state,id,name,point:point&&project(point),d:(point?[[point]]:rings).map(ring=>'M'+ring.map(v=>{const [x,y]=project(v);x0=Math.min(x,x0);x1=Math.max(x,x1);y0=Math.min(y0,y);y1=Math.max(y1,y);return x.toFixed(2)+','+y.toFixed(2)}).join('L')+'Z').join('')}));
 const span=Math.max(.5,x1-x0,y1-y0),pad=.035*span,geo={shapes,span,view:[x0-pad,y0-pad,x1-x0+2*pad,y1-y0+2*pad].join(' ')};geometryCache.set(st,geo);return geo
}
let mapMetric='rules';const metricNames={permits:'Distinct permits',rules:'Ordinance rules',active:'Active permits',historical:'Historical permits',unconfirmed:'Status not reported'};
const mapCountCache=new Map();
function countsFor(st,id='',name=''){
 const cacheKey=JSON.stringify([federalOnly,st,id,name]);if(mapCountCache.has(cacheKey))return mapCountCache.get(cacheKey);
 const scopedState=id&&places.get(id)?.[2]==='state',area=id&&!scopedState?norm(name||places.get(id)?.[3]||scoped.get(id)?.[1],st):'*';
 const rs=A.rules.filter(r=>ok(r)&&(!st||r.state===st)&&(!id||scopedState||jkey(r)===id));
 const source=federalOnly?H.federalMetrics:H.metrics;const result={rules:rs.length,active:0,historical:0,unconfirmed:0,hasHistory:!st||!!source[st]};
 for(const states of (st?[st]:Object.keys(source))){const t=source[states]?.[area]||{};for(const k of ['active','historical','unconfirmed'])result[k]+=t[k]||0}
 result.permits=result.active+result.historical+result.unconfirmed;mapCountCache.set(cacheKey,result);return result
}
function amount(ct,k){return (k==='rules'||ct.hasHistory)?ct[k].toLocaleString():'—'}
function updateMapCounts(st,id){
 const islands=$('outlying');islands.replaceChildren();islands.hidden=!!st;
 if(!st)for(const code of outlying){const island=countsFor(code);const b=el('button',code+' '+amount(island,mapMetric));b.title=sn.get(code)+' · '+metricNames[mapMetric]+': '+amount(island,mapMetric);b.setAttribute('aria-label','View '+sn.get(code));b.onclick=()=>choose(code);islands.append(b)}

 const ct=countsFor(st,id);
 for(const b of document.querySelectorAll('[data-metric]')){const k=b.dataset.metric;b.firstElementChild.textContent=amount(ct,k);b.setAttribute('aria-pressed',String(k===mapMetric));b.title='Show '+metricNames[k].toLowerCase()+' on the map and in the list'}
 $('maptitle').textContent=(id&&(scoped.get(id)?.[1]||places.get(id)?.[3]))||sn.get(st)||'All states';
 $('unknownCount').replaceChildren();if(ct.hasHistory&&ct.unconfirmed){const b=el('button',ct.unconfirmed.toLocaleString()+' more permits have no confirmed status');b.onclick=()=>{selectMetric('unconfirmed');mobileMap(false)};$('unknownCount').append(b)}else if(!ct.hasHistory)$('unknownCount').textContent=federalOnly?'No federal records collected for this area.':'No permit files collected for this state.';
 $('mapkey').replaceChildren(el('span',metricNames[mapMetric]),...['0 in atlas','1–9','10–99','100+'].map((x,i)=>el('span',x,'keybin bin'+i)))
}
function localSearchNote(g){if(!g)return '';const n=g[10]||0;
 if(n)return 'Read '+n+' local '+(n===1?'page':'pages')+(String(g[6]).includes('candidate')?'; a possible match still needs review.':'. No zoning rule is listed here.');
 if(g[6]==='retrieval failed')return 'The local website could not be read.';
 if(g[6]==='evidence held')return 'A possible rule still needs verification.';
 return 'No local zoning source on file.'}
function geoList(){const q=$('geosearch').value.toLowerCase().trim(),st=$('state').value,box=$('geolist');box.replaceChildren();const gs=A.geo.filter(g=>(!st||g[1]===st)&&(!q||g[3].toLowerCase().includes(q)||g[0]===q)).sort((a,b)=>(b[7]-a[7])||a[3].localeCompare(b[3]));for(const g of gs.slice(0,40)){const b=el('button'),ct=countsFor(g[1],g[0],g[3]),ruleLabel=ct.rules===1?' rule':' rules',permitLabel=(federalOnly?' federal':'')+(ct.permits===1?' permit':' permits');b.append(el('span',g[3]+' · '+g[1]),el('small',ct.rules+ruleLabel+' · '+(ct.hasHistory?ct.permits.toLocaleString()+permitLabel:'no '+(federalOnly?'federal ':'')+'permit files')));b.onclick=()=>selectMap(g[1],g[2]==='state'?'':g[0]);box.append(b)}if(gs.length>40)box.append(el('small','Type to narrow '+gs.length.toLocaleString()+' places.'))}
let lastMap='',lastState=null;
function selectMap(st,id){choose(st,id);if(id){mobileMap(false);$('resultTitle').focus({preventScroll:true})}}
function map(st,jid){
 const stamp=st+':'+jid+':'+mapMetric+':'+federalOnly;if(stamp===lastMap)return;lastMap=stamp;updateMapCounts(st,jid);
 const m=$('map'),tip=$('tip'),geo=geometry(st);tip.hidden=true;
 if(st+mapMetric+federalOnly===lastState){for(const x of m.querySelectorAll('[data-id]'))x.classList.toggle('active',x.dataset.id===jid);return}
 lastState=st+mapMetric+federalOnly;m.replaceChildren();if(!geo.shapes.length)return;m.setAttribute('viewBox',geo.view);
 const nodes=[],markers=[];function bind(shape,state,id,name,isNational,available){
   const g=places.get(id),ct=countsFor(state,isNational?'':id,g?.[3]||name),num=ct[mapMetric],bin=!num?0:num<10?1:num<100?2:3,labels=['rules','active','historical','unconfirmed'].map(k=>(federalOnly&&k!=='rules'?'Federal · ':'')+metricNames[k]+': '+amount(ct,k));
   shape.classList.add(available?'on':'back','countbin'+bin);if(jid===id)shape.classList.add('active');shape.dataset.id=id;shape.dataset.value=num;
   shape.setAttribute('aria-label',[name,...labels].join(' · '));shape.setAttribute('role',available?'button':'img');
   if(num>0){markers.push([num,shape,g])}
   const show=e=>{tip.replaceChildren(el('strong',name),...labels.map(s=>el('span',s)));tip.hidden=false;
    const box=m.parentElement.getBoundingClientRect(),r=shape.getBoundingClientRect(),x=e.clientX||r.x+r.width/2,y=e.clientY||r.y+r.height/2;
    tip.style.left=Math.max(3,Math.min(box.width-tip.offsetWidth-3,x-box.left+12))+'px';tip.style.top=Math.max(3,Math.min(box.height-tip.offsetHeight-3,y-box.top+10))+'px'};
   shape.onpointerenter=shape.onpointermove=shape.onfocus=show;shape.onpointerleave=shape.onblur=()=>{tip.hidden=true};
   if(available){shape.setAttribute('tabindex',nodes.length?'-1':'0');nodes.push(shape);const act=()=>{tip.hidden=true;selectMap(state,isNational?'':id)};
    shape.onclick=act;shape.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act()}else if(e.key==='Escape'){tip.hidden=true}else if(['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'].includes(e.key)){e.preventDefault();const v=['ArrowLeft','ArrowUp'].includes(e.key)?-1:1,next=nodes[(nodes.indexOf(shape)+v+nodes.length)%nodes.length];shape.setAttribute('tabindex','-1');next.setAttribute('tabindex','0');next.focus()}}}
   m.append(shape)
 }
 for(const f of geo.shapes)bind(f.point?svg('circle',{cx:f.point[0],cy:f.point[1],r:.018*geo.span,class:'dot'}):svg('path',{d:f.d,'fill-rule':'evenodd',class:'region'}),f.state,f.id,f.name,!st,sn.has(f.state));
 if(st){const ids=new Set(A.rules.filter(r=>r.state===st&&ok(r)).map(jkey));for(const name of Object.keys(H.areas[st]||{})){const g=matchPlace(st,name);if(g)ids.add(g[0])}
  for(const id of ids){const g=places.get(id);if(!g||!['place','cousubs','statistical place','territory subdivisions'].includes(g[2]))continue;const [cx,cy]=project([+g[5],+g[4]]);bind(svg('circle',{cx,cy,r:.012*geo.span,class:'dot'}),st,id,g[3],false,true)}}
 const used=[],fs=geo.span*.03;
 for(const [num,shape,g] of markers.sort((a,b)=>b[0]-a[0])){
    const bb=shape.getBBox();let x=bb.x+bb.width/2,y=bb.y+bb.height/2;
    if(g&&Number.isFinite(+g[4])&&Number.isFinite(+g[5]))[x,y]=project([+g[5],+g[4]]);
    const w=fs*.66*(String(num).length+1);if(used.some(([xx,yy,ww])=>Math.abs(xx-x)<(w+ww)/2&&Math.abs(yy-y)<fs*1.3))continue;
    used.push([x,y,w]);const label=svg('text',{x,y,'font-size':fs,'text-anchor':'middle','dominant-baseline':'central',class:'mapnumber','aria-hidden':'true'});label.textContent=num;m.append(label)
 }
}
