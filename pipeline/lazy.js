/* On-demand tabs (2026-11-04). Builds a tab's pane from its chunk file (lazy.py) the first time it is opened.
   Matchups, Compare and Rosters are rebuilt on each visit and dropped ~1.5s after leaving (their switches, selections
   and scroll come back); the other tabs are built once, then moved out of the document while hidden (so the page's
   fitters, which query the whole document, only see the tab on screen). Matchups builds only the selected week.
   Also: radio state across reloads (was the inline restore script), prefetch on hover/touch, the loading frame
   (after 300ms) and "Couldn't load. Tap to retry". Every pane's own scripts run once, in order, as if parsed. */
(function(){
var Z=window.LZ,D=document,W=window;if(!Z)return;
var HV={},PS={},RAN={},SS={},SC=new Map(),TX={},cur=null,lastY=W.scrollY||0,K=Z.k;
Z.h.forEach(function(k){HV[k]=1});
/* ---- radio state (sessionStorage, as before: the tab and group are never restored) ---- */
var SEL=[];try{SEL=JSON.parse(sessionStorage.getItem(K)||'[]')}catch(e){}
function rest(root){SEL.forEach(function(id){var e=root===D?D.getElementById(id):root.querySelector('#'+CSS.escape(id));
  if(e&&e.type==='radio'&&e.name!=='tab'&&e.name!=='tgrp')e.checked=true})}
function save(){try{sessionStorage.setItem(K,JSON.stringify(SEL))}catch(e){}}
rest(D);
/* ---- panes ---- */
D.querySelectorAll('div.pane').forEach(function(el){var m=/\bpane-(\w+)/.exec(el.className);if(!m)return;var id=m[1];
  if(Z.p[id])PS[id]={el:el,st:'empty'};else if(id!=='st')PS[id]={el:el,st:'built'}});
for(var k in PS)if(PS[k].st==='built')RAN[k]=1;
function get(u){if(!TX[u])TX[u]=fetch(u).then(function(r){if(!r.ok){var e=new Error('HTTP '+r.status);e.status=r.status;throw e}return r.text()})
  .catch(function(e){delete TX[u];throw e});return TX[u]}
function run(root,key){  // re-create the inert <script>s in place; DOMContentLoaded/load handlers run right after
  if(RAN[key])return;RAN[key]=1;var q=[],od=D.hasOwnProperty('addEventListener'),ad=D.addEventListener,aw=W.addEventListener;
  function wr(orig){return function(t,f,o){if(t==='DOMContentLoaded'||t==='load'){q.push([this,f]);return}return orig.call(this,t,f,o)}}
  D.addEventListener=wr(ad);W.addEventListener=wr(aw);
  try{[].slice.call(root.querySelectorAll('script')).forEach(function(o){var ty=(o.type||'').toLowerCase();
    if(ty&&!/^(text|application)\/(java|ecma)script$/.test(ty))return;var n=D.createElement('script');
    for(var i=0;i<o.attributes.length;i++)n.setAttribute(o.attributes[i].name,o.attributes[i].value);n.text=o.text;o.parentNode.replaceChild(n,o)})}
  finally{if(od)D.addEventListener=ad;else delete D.addEventListener;W.addEventListener=aw}
  q.forEach(function(x){try{x[1].call(x[0],new Event('DOMContentLoaded'))}catch(e){setTimeout(function(){throw e})}})}
function init(root,key){  // what the page does at load for content that is in the HTML
  rest(root);run(root,key);subs(root);
  if(typeof AVR!=='undefined')root.querySelectorAll('.pav[data-avt]').forEach(function(e){var r=AVR[e.dataset.avt];if(r)e.classList.add('av','av-'+r);else e.classList.add('nl')});
  if(typeof RNI!=='undefined')root.querySelectorAll('.tqid .tqsd[data-rk]').forEach(function(el){var r=+el.dataset.rk;if(!RNI[r])return;el.className='tqsd rnh';
    el.innerHTML='<img class="rni '+(r<=2?'p':r<=6?'g':'w')+'" src="'+RNI[r]+'" alt="'+r+'" aria-label="Rank '+r+'">'})}
/* panels cut one level deeper (Playoffs bracket games, team panels): built when their radio is checked */
function subs(root){root.querySelectorAll('[data-lzs]').forEach(function(b){if(b.dataset.lzd)return;var r=root===D?D.getElementById(b.dataset.lzr):root.querySelector('#'+CSS.escape(b.dataset.lzr));if(r&&r.checked)sub(b)})}
function sub(b){if(b.dataset.lzd||b._pr)return b._pr;var u=b.dataset.lzs,tm=setTimeout(function(){if(!b.dataset.lzd)frame(b)},300);
  return b._pr=get(u).then(function(h){clearTimeout(tm);b._pr=null;
    if(b.dataset.lzx){var r=D.getElementById(b.dataset.lzr);if(r&&!r.checked){unhold(b);return}}  // another team was picked while this one loaded
    b.innerHTML=h;b.dataset.lzd='1';init(b,u);delete TX[u];drop(b);fits();putScroll(b,u);done(b,{panel:b.dataset.lzr})},
  function(e){clearTimeout(tm);b._pr=null;unhold(b);fail(b,function(){sub(b)},e)})}
/* Team Hub (data-lzx): one team's panel at a time; the others are emptied (inner scroll kept) and fetched again from the HTTP cache */
function drop(b){if(!b.dataset.lzx)return;var c=b.className.split(' ')[0];b.parentNode.querySelectorAll(':scope>.'+c+'[data-lzx][data-lzd]').forEach(function(x){if(x===b)return;
  var r=D.getElementById(x.dataset.lzr);if(r&&r.checked)return;saveScroll(x,x.dataset.lzs);x.textContent='';delete x.dataset.lzd})}
function fits(){if(W.__fitAll)W.__fitAll()}
/* scroll: inner scrollers are remembered by their path from the pane (or week); positions are read as they scroll,
   never on a tab switch (a layout read there would cut the page short before the new tab is held open) */
D.addEventListener('scroll',function(e){var t=e.target;if(t&&t.nodeType===1)SC.set(t,[t.scrollLeft,t.scrollTop]);else lastY=W.scrollY},{capture:true,passive:true});
// a radio is already checked when its click event runs: hold the new tab (or week) open right there, before any
// layout read can cut the page short (lastY comes from the scroll events, never read at this point)
D.addEventListener('click',function(e){var t=e.target;if(!t||t.type!=='radio')return;
  if(t.name==='tab'){var p=PS[t.id.slice(4)];if(p&&p.st==='empty')hold(p.el)}
  else if(t.name==='mwk'){var b=D.querySelector('.pane-mu .mwx-'+t.id.slice(3));if(b&&b.dataset.lz!=='1')hold(b)}
  if(t.id){var s=D.querySelector('[data-lzr="'+CSS.escape(t.id)+'"]');if(s&&!s.dataset.lzd)hold(s)}},true);
function path(root,el){var p=[];while(el&&el!==root){var par=el.parentElement;if(!par)return null;p.unshift([].indexOf.call(par.children,el));el=par}return el===root?p:null}
function at(root,p){var e=root;for(var i=0;i<p.length&&e;i++)e=e.children[p[i]];return e}
function keyOf(el){var w=el.closest&&el.closest('.pane-mu .mwx');return w?'w'+/mwx-(\d+)/.exec(w.className)[1]:null}
function saveScroll(root,key){var L=SS[key]=SS[key]||{};SC.forEach(function(v,el){if(!root.contains(el))return;var p=path(root,el);if(p)L[p.join('.')]=v;SC.delete(el)})}
function putScroll(root,key){var L=SS[key];if(!L)return;for(var p in L){var e=at(root,p.split('.').map(Number));if(e){e.scrollLeft=L[p][0];e.scrollTop=L[p][1]}}}
/* while a pane is being built the page keeps its height, so the scroll position is not cut short */
function hold(el){el.style.minHeight=(lastY+W.innerHeight)+'px'}
function unhold(el){el.style.removeProperty('min-height')}
function frame(el){if(el.querySelector(':scope>.lzf'))return;var f=D.createElement('div');f.className='lzf';el.appendChild(f);return f}
function fail(el,retry,e){var f=el.querySelector(':scope>.lzf')||frame(el);f.innerHTML='<button type="button" class="lze">Couldn’t load. Tap to retry</button>';
  f.firstChild.onclick=function(){if(e&&e.status===404){try{if(!sessionStorage.getItem('dt-lz404')){sessionStorage.setItem('dt-lz404','1');location.reload();return}}catch(_){}}
    f.remove();retry()}}
function done(el,ev){unhold(el);requestAnimationFrame(function(){D.dispatchEvent(new CustomEvent('panebuilt',{detail:ev}))})}
function park(id){var p=PS[id];if(p.st!=='built')return;saveScroll(p.el,id);var r=D.createRange();r.selectNodeContents(p.el);p.frag=r.extractContents();p.st='parked'}
function unpark(id){var p=PS[id];p.el.appendChild(p.frag);p.frag=null;p.st='built';putScroll(p.el,id);fits()}
function discard(id){var p=PS[id];if(p.st!=='built'||cur===id)return;saveScroll(p.el,id);
  if(id==='mu')p.el.querySelectorAll('.mwx').forEach(function(w){if(w.firstChild)saveScroll(w,keyOf(w))});
  p.el.textContent='';p.st='empty'}
function load(id){var p=PS[id],el=p.el;p.st='loading';hold(el);var tm=setTimeout(function(){if(p.st==='loading')frame(el)},300);
  return p.pr=get(Z.p[id]).then(function(h){clearTimeout(tm);
    if(cur!==id&&HV[id]){p.st='empty';el.textContent='';unhold(el);return}
    el.innerHTML=h;h=null;p.st='built';init(el,id);delete TX[Z.p[id]];  // no copy kept (2026-11-05): a dropped tab is fetched again, from the HTTP cache
    var wk=id==='mu'?week(true):null;fits();putScroll(el,id);
    var sp=[].slice.call(el.querySelectorAll('[data-lzx]')).map(function(b){return b._pr}).filter(Boolean);  // a restored team's panel is built before the tab is shown
    return Promise.all([wk].concat(sp.map(function(x){return x.catch(function(){})}))).then(function(){done(el,{pane:id});if(cur!==id){if(HV[id])leave(id);else park(id)}})},
  function(e){clearTimeout(tm);p.st='empty';fail(el,function(){if(cur===id)ensure(id)},e)})}
function ensure(id){var p=PS[id];if(!p)return Promise.resolve();clearTimeout(p.dt);
  if(p.st==='parked'){unpark(id);return Promise.resolve()}
  if(p.st==='loading')return p.pr;if(p.st==='built')return Promise.resolve();
  var f=p.el.querySelector(':scope>.lzf');if(f)f.remove();return load(id)}
function leave(id){var p=PS[id];if(!p||p.st!=='built')return;
  if(HV[id]){saveScroll(p.el,id);p.el.querySelectorAll('.mwx').forEach(function(w){if(w.firstChild)saveScroll(w,keyOf(w))});
    clearTimeout(p.dt);p.dt=setTimeout(function(){discard(id)},1500)}
  else park(id)}
function show(id){if(id===cur)return ensure(id);var prev=cur,p=PS[id];cur=id;if(p&&p.st==='empty')hold(p.el);if(prev)leave(prev);return ensure(id)}
/* Matchups: only the selected week is on the page */
function week(first){var mu=PS.mu;if(!mu||mu.st!=='built')return null;var r=mu.el.querySelector('input[name=mwk]:checked');if(!r)return null;
  var n=r.id.slice(3),b=mu.el.querySelector('.mwx-'+n);if(!b||!Z.w[n])return null;if(!first&&b.dataset.lz!=='1')hold(b);
  mu.el.querySelectorAll('.mwx').forEach(function(x){if(x!==b&&x.firstChild){saveScroll(x,keyOf(x));x.textContent='';delete x.dataset.lz}});
  if(b.dataset.lz==='1')return null;if(b._pr)return b._pr;
  var tm=setTimeout(function(){if(!b.dataset.lz)frame(b)},300);
  return b._pr=get(Z.w[n]).then(function(h){clearTimeout(tm);b._pr=null;if(!b.isConnected)return;
    var cr=mu.el.querySelector('input[name=mwk]:checked');if(!cr||cr.id.slice(3)!==n){b.textContent='';unhold(b);return}
    b.innerHTML=h;b.dataset.lz='1';init(b,'w'+n);delete TX[Z.w[n]];fits();putScroll(b,'w'+n);if(!first)done(b,{pane:'mu',week:+n})},
  function(e){clearTimeout(tm);b._pr=null;unhold(b);fail(b,function(){week(false)},e)})}
/* the radio listener: state, tab and week switches (capture: before the page's own change handlers) */
D.addEventListener('change',function(ev){var t=ev.target;if(!t||t.type!=='radio')return;
  if(t.id){D.querySelectorAll('input[type=radio][name="'+CSS.escape(t.name)+'"]').forEach(function(x){var i=SEL.indexOf(x.id);if(i>=0)SEL.splice(i,1)});SEL.push(t.id);save()}
  if(t.name==='tab'){try{sessionStorage.setItem('dt-tab',t.id)}catch(e){}show(t.id.slice(4))}
  else if(t.name==='mwk'&&t.closest('.pane-mu'))week(false);
  if(t.id){var b=D.querySelector('[data-lzr="'+CSS.escape(t.id)+'"]');if(b)sub(b)}},true);
/* anything that checks a tab without a change event still gets its pane */
D.addEventListener('click',function(){setTimeout(function(){var t=D.querySelector('input[name=tab]:checked');if(t&&t.id.slice(4)!==cur)show(t.id.slice(4))},0)});
W.addEventListener('hashchange',function(){setTimeout(function(){var t=D.querySelector('input[name=tab]:checked');if(t&&t.id.slice(4)!==cur)show(t.id.slice(4))},0)});
/* prefetch on hover / touch / focus of a tab or group button */
var GF={gd:Z.po?'po':'st',lab:'sx',fo:'ro'};
function pre(e){var l=e.target&&e.target.closest&&e.target.closest('label[for]');if(!l)return;var f=l.htmlFor,
  sb=f.indexOf('thx-')===0?D.querySelector('[data-lzx][data-lzr="'+CSS.escape(f)+'"]'):null;if(sb){if(!sb.dataset.lzd&&!sb._pr)get(sb.dataset.lzs).catch(function(){});return}
  var id=f.indexOf('tab-')===0?f.slice(4):f.indexOf('grp-')===0?GF[f.slice(4)]:null;
  var p=id&&PS[id];if(!p||p.st!=='empty'||!Z.p[id])return;get(Z.p[id]).catch(function(){});
  if(id==='mu'){var n=null;SEL.forEach(function(x){if(/^mw-\d+$/.test(x))n=x.slice(3)});n=n||Z.cw;if(Z.w[n])get(Z.w[n]).catch(function(){})}}
['pointerover','touchstart','focusin'].forEach(function(t){D.addEventListener(t,pre,{passive:true,capture:true})});
/* the tab shown on load (default or #hash) is built before the page is revealed */
subs(D);var t0=D.querySelector('input[name=tab]:checked');W.__pr=t0?show(t0.id.slice(4)):Promise.resolve();
try{sessionStorage.removeItem('dt-lz404')}catch(_){}
})();
