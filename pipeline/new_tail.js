// FL(): the web fonts are still loading. The page stays hidden until they have loaded and the fitters have run on them, and every
// fitter runs again on fonts.ready, so a fitter's first pass while they load is never seen: it is skipped (2026-11-04, WebKit memory).
const FL=()=>!!(document.fonts&&document.fonts.status==='loading');
const fn=n=>n;  // data files use full team names
const OPEN=new Set();
const MAX=Math.max(...Object.values(T).map(d=>d[3]));
const esc=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;");
const V=Object.values(T);
const MAXPA=Math.max(...V.map(d=>d[6]));
const MAXLUCK=Math.max(...V.map(d=>Math.abs(d[12])));
const ALLSC=Object.values(WK).flat().flatMap(g=>[g[2],g[3]]);
const SCHI=Math.max(...ALLSC),SCLO=30;
const rankOf=(v,i,low)=>1+V.filter(d=>low?d[i]<v-1e-9:d[i]>v+1e-9).length;
const tied=(v,i)=>V.filter(d=>Math.abs(d[i]-v)<1e-9).length>1;
const tone=r=>r==1?'gold':r<=3?'g':r>=NT?'b last':r>NT-3?'b':'';
const rkt=(v,dp)=>`<b class="rkb ${tone(Math.round(v))}">${dp?v.toFixed(dp):v}</b>`;
const dpR=(i,t)=>{const v=DP[t][i];return 1+Object.keys(DP).filter(u=>DP[u][i]<v-1e-9).length},dpT=(i,t)=>Object.keys(DP).filter(u=>u!==t&&Math.abs(DP[u][i]-DP[t][i])<1e-9).length>0;
const chip=(r,t)=>`<span class="ch ${tone(r)}"><span class="ct">${t?'T':''}${r}</span></span>`;
const luck=v=>`${v>0?'+':v<0?'−':''}${Math.abs(v).toFixed(2)}`;
const seg=r=>`<div class="seg10 ${tone(r)}" role="img" aria-label="Rank ${r} of ${NT}">${Array.from({length:NT},(_,k)=>`<i${k<NT+1-r?' class="on"':''}></i>`).join('')}</div>`;
const rankSk=t=>1+Object.values(SK).filter(v=>v[0]>SK[t][0]+1e-9).length;
const tiedSk=t=>Object.values(SK).filter(v=>Math.abs(v[0]-SK[t][0])<1e-9).length>1;
const rankEf=t=>1+Object.values(EF).filter(v=>v[0]>EF[t][0]+1e-9).length;
const tiedEf=t=>Object.values(EF).filter(v=>Math.abs(v[0]-EF[t][0])<1e-9).length>1;
const pct=x=>(Math.max(0,Math.min(1,x))*100).toFixed(1)+'%';

const star=(cx,cy,R,r)=>Array.from({length:10},(_,k)=>{const a=-Math.PI/2+k*Math.PI/5,q=k%2?r:R;return (cx+q*Math.cos(a)).toFixed(2)+","+(cy+q*Math.sin(a)).toFixed(2)}).join(" ");
function season(t){
  // Columns: paired bars (team score: green win / red loss; opponent score: grey), week number, team score rank tile, opponent score rank tile.
  const N=14,S=25,L=44,bw=13,top=4,base=36,y=v=>base-(base-top)*Math.max(0,Math.min(1,(v-SCLO)/(SCHI-SCLO)));
  const WY=47,R1=61,R2=76,TW=19,TH=13,H=84;
  const bl=(cy,fs)=>(cy+0.349*fs).toFixed(2); // alphabetic baseline that centres cap-height glyphs on cy
  // Opponent tick: thin white line; week high = darker gold, week low = burgundy, both with a white frame.
  // Every tick sits on a thin navy keyline so it separates cleanly from the green/red bar behind it.
  const KL=.8;
  const tick=(x,yy,k)=>{const big=k!=='n',w=bw+(big?6.5:6),h=big?4:2,x0=x-(big?3.25:3),y0=yy-h/2;
    let o=`<rect x="${(x0-KL).toFixed(2)}" y="${(y0-KL).toFixed(2)}" width="${(w+2*KL).toFixed(2)}" height="${(h+2*KL).toFixed(2)}" rx="${big?1.6:.9}" fill="var(--deck)"/>`;
    if(k==='n')return o+`<rect x="${x0}" y="${y0.toFixed(2)}" width="${w}" height="${h}" fill="var(--chalk)"/>`;
    return o+`<rect x="${x0+.45}" y="${(y0+.45).toFixed(2)}" width="${w-.9}" height="${h-.9}" rx="1" fill="${k==='hi'?'#cf9a2c':'#a24253'}" stroke="var(--chalk)" stroke-width=".9"/>`};
  const tile=(cx,cy,r,mode)=>{const k=r===1?'gold':r<=3?'g':r===NT?'last':r>NT-3?'b':'n';
    const st={gold:['rgba(244,196,81,.16)','#f4c451','rgba(244,196,81,.5)'],g:['var(--win-bg)','var(--win)',''],b:['var(--loss-bg)','var(--loss)',''],last:['var(--loss-bg)','var(--loss)','rgba(255,93,115,.6)'],n:['var(--line)','var(--steel)','']}[k];
    return `<rect${mode==='opp'?' opacity=".55"':''} x="${cx-TW/2}" y="${cy-TH/2}" width="${TW}" height="${TH}" rx="3" fill="${st[0]}"${st[2]?` stroke="${st[2]}" stroke-width="1"`:''}/>`+
           `<text x="${cx}" y="${bl(cy,9.5)}" text-anchor="middle" font-size="9.5" font-weight="500" ${mode==='opp'?'style="fill:var(--text-dim)"':`fill="${st[1]}"`}>${r}</text>`};
  const played=Object.fromEntries(WK[t].map(g=>[g[0],g]));
  const lab=(cy,txt)=>`<text x="0" y="${bl(cy,12.5)}" font-family="var(--display)" font-size="12.5" font-weight="600" letter-spacing=".6" fill="var(--steel)">${txt}</text>`;
  let s=`<svg class="szn" viewBox="0 0 ${L+N*S} ${H}" role="img" aria-label="Season: ${WK[t].map(g=>`Wk ${g[0]} ${g[2]>g[3]?'W':'L'} ${g[2].toFixed(1)}-${g[3].toFixed(1)}, score rank ${g[4]}, opponent rank ${g[5]}`).join('; ')}">`+
    lab(WY,'WK')+lab(R1,'RANK')+lab(R2,'OPP');
  for(let wk=1;wk<=N;wk++){const cx=L+(wk-.5)*S,x=cx-bw/2,g=played[wk];
    if(g){const won=g[2]>g[3],LAST=NT,hi=g[4]===1,lo=g[4]===LAST,ohi=g[5]===1,olo=g[5]===LAST,
      // paired bars: the team (green win / red loss) beside its opponent (grey)
      c=won?'var(--win)':'var(--loss)',oc='var(--steel)',oo='.42',
      w1=7.5,w2=5,gp=1,xa=cx-(w1+w2+gp)/2,xb=xa+w1+gp;
      s+=`<rect x="${xa}" y="${y(g[2]).toFixed(1)}" width="${w1}" height="${(base-y(g[2])).toFixed(1)}" rx="1.2" fill="${c}"/>`+
         `<rect x="${xb}" y="${y(g[3]).toFixed(1)}" width="${w2}" height="${(base-y(g[3])).toFixed(1)}" rx="1.2" fill="${oc}" opacity="${oo}"/>`+
         `<text x="${cx}" y="${bl(WY,12)}" text-anchor="middle" font-size="12" fill="var(--steel)">${wk}</text>`+
         tile(cx,R1,g[4],'me')+tile(cx,R2,g[5],'opp');
    }else{
      s+=`<rect x="${x+.5}" y="${top+.5}" width="${bw-1}" height="${base-top-1}" rx="1.5" fill="none" stroke="var(--line)" stroke-dasharray="2 2"/>`+
         `<text x="${cx}" y="${bl(WY,12)}" text-anchor="middle" font-size="12" fill="var(--text-dim)">${wk}</text>`;}
  }
  return s+`</svg>`;
}
function draw(med){
  const o=med?M:H;
  const wl=x=>{const e=T[x];return med?[e[0]+e[2],e[1]+G-e[2]]:[e[0],e[1]]};
  document.getElementById('list').innerHTML=o.map((t,i)=>{
    const d=T[t],w=d[0],l=d[1],mw=d[2],[rw0,rl0]=wl(t);
    const refs=[[0,'1st'],[1,'Bye'],[5,'Play-Off']];
    const gbOf=k=>{const [rw,rl]=wl(o[k]);const g=((rw-rw0)+(rl0-rl))/2;return g%1?g.toFixed(1):String(g)};
    const rf=refs.filter(([k])=>i>k);
    const gbH='';  // Games back (and the leader's 'Leader' label) removed from the card 2026-11-02
    const sub=med?`<div class="chl">Breakdown</div><div class="cw">H2H <b>${w}-${l}</b></div><div class="cw">Top-${(typeof NT!=='undefined'?NT:10)/2} <b>${mw}-${G-mw}</b></div>`
                 :`<div class="chl">Could have</div><div class="cw">Won <b>${CH[t][0]}</b></div><div class="cw">Lost <b>${CH[t][1]}</b></div>`;
    const P=med?PM:PH,dl=P.indexOf(t)-i,a=(med?POS.M:POS.H)[t];
    const tri=p=>`<svg class="tri" viewBox="0 0 8 7" aria-hidden="true"><path d="${p}"/></svg>`;
    const mv=dl>0?`<span class="mv up">${tri('M4 0L8 7H0Z')}${dl}</span>`:dl<0?`<span class="mv dn">${tri('M0 0H8L4 7Z')}${-dl}</span>`:`<span class="mv eq">–</span>`;
    const r=WK[t].map(g=>g[2]>g[3]?'W':'L'),lastR=r[r.length-1];let n=0;for(let k=r.length-1;k>=0&&r[k]===lastR;k--)n++;
    const BYT=0;  // YILM has no byes (as on the league's own site): playoff line only, no Bye odds
    const tc=i<BYT?'tier-bye':i<PO?'tier-po':'tier-out';
    const th=i===0?['tier-po']:i===PO?['tier-out','po','Playoff line',`Top ${PO} in`]:null;  // YILM: no bye; one line under the last playoff seed
    // a cutoff line (YILM-site style: label, rule, count) under the last seed of a tier; no tier banners
    const tierHtml=th?`${i?`</section><div class="pline pl-${th[1]}" role="separator" aria-label="${th[2]}: ${th[3]}"><b>${th[2]}</b><i></i><span>${th[3]}</span></div>`:''}<section class="tcard ${th[0]}">`:'';
    const op=OPEN.has(t);
    const strip=WK[t].map(g=>{const won=g[2]>g[3];return `<div class="gm"><div class="h"><span>Wk ${g[0]}</span><span class="res ${won?'w':'l'}"><span class="ct">${won?'W':'L'}</span></span></div><div class="sc">${g[2].toFixed(2)}${chip(g[4])}</div><div class="vs">vs ${esc(fn(g[1]))}</div><div class="os">${g[3].toFixed(2)}${chip(g[5])}</div></div>`}).join('')
      +FUT[t].map(g=>`<div class="gm fut"><div class="h"><span>Wk ${g[0]}</span></div><div class="up">Upcoming</div><div class="vs">vs ${esc(fn(g[1]))}</div></div>`).join('');
    return tierHtml+`<div class="r ${tc}${AVR[t]?" hav":""}${i>=PO?' out':''}${op?' open':''}" data-t="${esc(t)}" tabindex="0" role="button" aria-expanded="${op}">
      <div class="rk">${i+1}</div>
      ${AVR[t]?`<i class="av rav av-${AVR[t]}" aria-hidden="true"></i>`:""}<div class="nm"><span class="tn">${esc(t)} ${mv}</span>${typeof FAAB!=='undefined'&&FAAB[t]!=null?`<label for="tab-wr" class="fab" title="FAAB left: $${FAAB[t]} of $${FAABB} (opens The Wire)"><b>$${FAAB[t]}</b><small>FAAB</small></label>`:''}</div>
      <span class="hl">${NIK[t]?`<em class="mgr">${esc(NIK[t])}</em>`:""}</span>
      <div class="sb s-pf"><div class="stx"><em class="lb">PF</em><span class="pf">${d[3].toFixed(2)}</span>${chip(d[4])} <i class="pw"><span class="pws">· </span><b class="pwv">${d[5].toFixed(1)}</b>/wk <b class="psd" title="Weekly spread: standard deviation of the team's weekly scores">±${SDV(t).toFixed(0)}</b></i></div>${seg(d[4])}</div>
      <div class="sb s-pa"><div class="stx"><em class="lb">PA</em><span class="v">${d[6].toFixed(2)}</span>${chip(d[7])} <i class="pw"><span class="pws">· </span><b class="pwv">${d[8].toFixed(1)}</b>/wk</i></div>${seg(d[7])}</div>
      <div class="sb s-lu"><div class="stx"><em class="lb">Tot Eff</em><span class="v">${EF[t][0].toFixed(0)}%</span>${chip(rankEf(t),tiedEf(t))} <i class="pw"><span class="pws">· </span><b class="lw">${EF[t][1].toFixed(1)}</b>/wk</i></div>${seg(rankEf(t))}</div>
      <div class="sb s-sk"><div class="stx spl dps"><span class="dpb dpd"><span class="dph"><em class="lb dpl">Dropped pts</em><i class="pw pu">/wk</i></span><span class="dpg">${['QB','RB','WR','TE'].map((k,i)=>LPOS.includes(k)?`<span class="dpc p-${k.toLowerCase()}"><b>${k}</b><span class="${DP[t][i]>=0.05?'':'z'}">${DP[t][i].toFixed(1)}</span>${chip(dpR(i,t),dpT(i,t))}</span>`:'').join('')}</span></span><span class="dpb dso"><span class="dph"><em class="lb dpl">Season sim</em></span><span class="dpg sog">${[['Finish',SO[t][0].toFixed(1)],['#1',pctS(SO[t][1])],['Bye',pctS(SO[t][2])],['Playoffs',pctS(SO[t][3])]].map(([k,v],i)=>k==='Bye'?'':`<span class="dpc so s${i}"><b>${k}</b><span class="${i&&v==='0%'?'z':''}">${i?v:`<span class="sof ${tone(Math.round(SO[t][0]))}">${v}</span>`}</span></span>`).join('')}</span></span></div></div>
      <div class="st s2"><span><em class="lb">Opp<i class="lrk"> rk</i></em><span class="v">${d[9].toFixed(1)}</span>${chip(rankOf(d[9],9,true),tied(d[9],9))}</span><span><em class="lb">All-play</em><span class="v">${d[10]}-${d[11]}</span>${chip(rankOf(d[10],10,false),tied(d[10],10))}</span><span><em class="lb">Luck</em><span class="v">${luck(d[12])}<i class="lku" title="Expected wins (xW): all-play win rate × games played. Luck = actual wins − xW">${(d[10]/(d[10]+d[11])*(d[0]+d[1])).toFixed(2)} xW</i></span>${chip(rankOf(d[12],12,false),tied(d[12],12))}</span></div>
      <div class="side"><div class="rr${(String(rw0)+String(rl0)).length>2?" rr4":""}"><b>${rw0}-${rl0}</b></div><div class="l5r"><span class="sk ${lastR==='W'?'w':'l'}"><span class="ct">${lastR}${n}</span></span><span class="l5d" aria-label="Last 5 results">${WK[t].slice(-5).map(g=>`<i class="${g[2]>g[3]?'w':'l'}"></i>`).join('')}</span></div>${gbH}<div class="subw">${sub}</div></div>
      <div class="szw">${season(t)}</div>
      <div class="strip"${op?'':' hidden'}>${strip}</div></div>`}).join('')+'</section>';  // each tier is its own card (section.tcard)
}
// sim odds as shown: whole percent, '<1%' / '>99%' instead of a rounded 0 or 100 that the sim did not actually reach
function pctS(x){return x<=0?'0%':x>=100?'100%':x<1?'<1%':x>99?'>99%':Math.round(x)+'%'}
// weekly spread: standard deviation of a team's weekly scores (completed weeks)
function SDV(t){const a=WK[t].map(g=>g[2]),m=a.reduce((x,y)=>x+y,0)/a.length;return Math.sqrt(a.reduce((x,y)=>x+(y-m)*(y-m),0)/a.length)}
// ---- desktop (wide screens only, see the @media block in the head): every team in one sortable table above the cards
function dtab(med){
  let box=document.getElementById('dtab');
  if(!box){box=document.createElement('div');box.id='dtab';box.className='dtab';const l=document.getElementById('list');l.parentNode.insertBefore(box,l)}
  const o=med?M:H,N=o.length,PN=typeof PO!=='undefined'?PO:6,BY=0;  // YILM: no bye tier in the table either
  const wl=x=>{const e=T[x];return med?[e[0]+e[2],e[1]+G-e[2]]:[e[0],e[1]]};
  const sd=t=>{const a=WK[t].map(g=>g[2]),m=a.reduce((x,y)=>x+y,0)/a.length;return Math.sqrt(a.reduce((x,y)=>x+(y-m)*(y-m),0)/a.length)};
  const pc=x=>x<=0?'0%':x>=100?'100%':x<1?'<1%':x>99?'>99%':Math.round(x)+'%';
  const so=t=>typeof SO!=='undefined'&&SO[t]?SO[t]:null;
  const av=t=>typeof AVR!=='undefined'&&AVR[t]?`<i class="av dav av-${AVR[t]}" aria-hidden="true"></i>`:'';
  const tier=i=>i<BY?'bye':i<PN?'po':'out';
  const rows=o.map((t,i)=>{const d=T[t],[w,l]=wl(t),r=WK[t].map(g=>g[2]>g[3]?'W':'L'),lr=r[r.length-1];let n=0;for(let k=r.length-1;k>=0&&r[k]===lr;k--)n++;
    return {t,i,w,l,hw:d[0],hl:d[1],mw:d[2],pf:d[3],pfr:d[4],pw:d[5],sd:sd(t),pa:d[6],par:d[7],paw:d[8],apw:d[10],apl:d[11],apr:rankOf(d[10],10,false),xw:d[10]/Math.max(1,d[10]+d[11])*G,lk:d[12],ef:EF[t][0],st:lr+n,l5:WK[t].slice(-5).map(g=>g[2]>g[3]),s:so(t)}});
  const cols=[['seed','',r=>r.i],['team','Team',r=>r.t],['wl','W-L',r=>r.w-r.l/100],['st','Strk',null],['l5','Last 5',null],['pf','PF',r=>r.pf],['pw','Per wk ±',r=>r.pw],
    ['pa','PA',r=>r.pa],['paw','PA/wk',r=>r.paw],['ap','All-play',r=>r.apw],['xw','xWins',r=>r.xw],['lk','Luck',r=>r.lk],['ef','Tot eff',r=>r.ef],['fin','Finish',r=>r.s?-r.s[0]:0],['top','#1',r=>r.s?r.s[1]:0],['po','Playoffs',r=>r.s?r.s[3]:0]];
  const key=box.dataset.k||'seed',dir=+(box.dataset.d||1);
  const f=cols.find(c=>c[0]===key)[2];
  const sorted=key==='seed'?rows:[...rows].sort((a,b)=>dir*((key==='team'?a.t.localeCompare(b.t):f(b)-f(a))));
  const tcls={bye:'Bye · seeds 1–'+BY,po:'Playoffs · seeds '+(BY+1)+'–'+PN,out:'Chasing · seeds '+(PN+1)+'–'+N};
  let h='<table class="dtt"><thead><tr class="dtg">'+cols.slice(0,-3).map(()=>'<th></th>').join('')+'<th colspan="3" class="dsim"><span>20k simulations</span></th></tr><tr>'+cols.map(c=>`<th data-k="${c[0]}"${c[2]?' class="srt'+(c[0]===key?' on':'')+(c[0]==='seed'?' rst'+(key!=='seed'?' act':''):'')+'"':''}${c[0]==='seed'?' title="Reset to standings order"':''}>${c[0]==='seed'?'<svg class="rsi" viewBox="0 0 16 16" aria-label="Reset sort"><path d="M3.2 8a4.8 4.8 0 1 0 1.5-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M2.6 1.9v3.4H6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>':c[1]}</th>`).join('')+'</tr></thead><tbody>',lt='';
  for(const r of sorted){
    if(key==='seed'&&tier(r.i)!==lt){const pv=lt;lt=tier(r.i);if(pv){const pl=pv==='bye'?['bye','Bye line','Top '+BY+' bye']:['po','Playoff line','Top '+PN+' in'];h+=`<tr class="dtl"><td colspan="${cols.length}"><div class="pline pl-${pl[0]}" role="separator"><b>${pl[1]}</b><i></i><span>${pl[2]}</span></div></td></tr>`}}
    const k_=(h.match(/class="dtr /g)||[]).length;
    h+=`<tr class="dtr ${tier(r.i)}${k_%2?'':' dra'}" data-t="${esc(r.t)}"><td class="dsd">${typeof RNI!=='undefined'&&RNI[r.i+1]?`<img class="rni dri" src="${RNI[r.i+1]}" alt="${r.i+1}" aria-label="Rank ${r.i+1}">`:r.i+1}</td><td class="dtm"><span>${av(r.t)}${esc(r.t)}</span></td>`+
       `<td class="dwl"><b>${r.w}-${r.l}</b>${med?`<small class="wlb" title="H2H ${r.hw}-${r.hl} · Top-${N/2} ${r.mw}-${G-r.mw}">${r.hw}-${r.hl} · ${r.mw}-${G-r.mw}</small>`:''}</td><td><i class="dsk ${r.st[0]==='W'?'w':'l'}">${r.st}</i></td><td><span class="dl5">${r.l5.map(x=>`<i class="${x?'w':'l'}"></i>`).join('')}</span></td>`+
       `<td>${r.pf.toFixed(1)}${chip(r.pfr)}</td><td><b>${r.pw.toFixed(1)}</b><small>±${r.sd.toFixed(0)}</small></td><td>${r.pa.toFixed(1)}${chip(r.par)}</td><td><b>${r.paw.toFixed(1)}</b></td>`+
       `<td>${r.apw}-${r.apl}${chip(r.apr)}</td><td><b>${r.xw.toFixed(2)}</b></td><td class="${r.lk>=0.05?'up':r.lk<=-0.05?'dn':''}">${(r.lk>=0?'+':'−')+Math.abs(r.lk).toFixed(2)}</td><td>${r.ef.toFixed(0)}%</td>`+
       (r.s?`<td class="dfin">${rkt(r.s[0],1)}</td><td class="c1">${pc(r.s[1])}</td><td class="c3">${pc(r.s[3])}</td>`:'<td class="dfin"></td><td></td><td></td>')+'</tr>'}
  box.innerHTML='<div class="dtp">'+h+'</tbody></table></div>';
  if(!box.dataset.w){box.dataset.w=1;box.addEventListener('click',e=>{
    const th=e.target.closest('th.srt');if(th){const k=th.dataset.k;box.dataset.d=box.dataset.k===k?-(+box.dataset.d||1):1;box.dataset.k=k===box.dataset.k&&+box.dataset.d===1?'seed':k;if(box.dataset.k==='seed')box.dataset.d=1;dtab(document.getElementById('bm').getAttribute('aria-pressed')==='true');return}
    const tr=e.target.closest('tr.dtr');if(!tr)return;const c=document.querySelector('#list .r[data-t="'+CSS.escape(tr.dataset.t)+'"]');
    if(c){c.scrollIntoView({behavior:'smooth',block:'start'});c.classList.remove('dfl');void c.offsetWidth;c.classList.add('dfl')}})}
}
const list=document.getElementById('list');
function toggle(row){const t=row.dataset.t;OPEN.has(t)?OPEN.delete(t):OPEN.add(t);const op=OPEN.has(t);row.classList.toggle('open',op);row.setAttribute('aria-expanded',op);row.querySelector('.strip').hidden=!op}
list.addEventListener('click',e=>{if(e.target.closest('.strip'))return;if(e.target.closest('.fab')){setTimeout(()=>{const n=document.querySelector('nav.tabs');n&&n.scrollIntoView({block:'start'})},0);return}const r=e.target.closest('.r');if(r)toggle(r)});
list.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('r')){e.preventDefault();toggle(e.target)}});
const bh=document.getElementById('bh'),bm=document.getElementById('bm');
function set(med){bh.setAttribute('aria-pressed',!med);bm.setAttribute('aria-pressed',med);draw(med);dtab(med)}
bh.onclick=()=>set(false);bm.onclick=()=>set(true);
draw(false);if(!FL())dtab(false);
if(typeof AVR!=='undefined')document.querySelectorAll('.pav[data-avt]').forEach(e=>{const r=AVR[e.dataset.avt];if(r)e.classList.add('av','av-'+r);else e.classList.add('nl')});
function pfit(){document.querySelectorAll('.pr .pav.av+.psn').forEach(el=>{if(!el.offsetParent)return;el.style.fontSize='';let f=parseFloat(getComputedStyle(el).fontSize);while((el.scrollHeight>el.clientHeight+1||el.scrollWidth>el.clientWidth+1)&&f>11){f-=0.5;el.style.fontSize=f+'px'}})}
pfit();document.addEventListener('change',()=>requestAnimationFrame(pfit));
// standings card names: shrink a long name just enough to show in full (never an ellipsis)
// cap-height centre of a text box's line, measured from the bottom of the line box (font metrics via canvas)
function capC(e){const c=getComputedStyle(e),fs=parseFloat(c.fontSize);_cv.font=`${c.fontWeight} ${fs}px ${c.fontFamily}`;const m=_cv.measureText('H'),a=m.fontBoundingBoxAscent,d=m.fontBoundingBoxDescent,lh=c.lineHeight==='normal'?a+d:parseFloat(c.lineHeight);
  return {lh,c:(lh-a-d)/2+d+m.actualBoundingBoxAscent/2}}
function mvAl(){
  document.querySelectorAll('.board .r .nm').forEach(n=>{if(!n.offsetParent)return;const t=n.querySelector('.tn'),v=n.querySelector('.mv'),f=n.querySelector('.fab');if(!t)return;
  const cap=e=>{const c=getComputedStyle(e);_cv.font=`${c.fontWeight} ${c.fontSize} ${c.fontFamily}`;return _cv.measureText('H').actualBoundingBoxAscent};
  if(v)v.style.verticalAlign=((cap(t)-cap(v))/2)+'px';
  // top of the name's capitals level with the top of the team logo
  n.style.marginTop='0px';const lg=n.closest('.r').querySelector('.rav');if(lg&&lg.getBoundingClientRect().height>0){
    const c=getComputedStyle(t);_cv.font=`${c.fontWeight} ${c.fontSize} ${c.fontFamily}`;const m=_cv.measureText('H'),a=m.fontBoundingBoxAscent,d=m.fontBoundingBoxDescent,lh=parseFloat(c.lineHeight)||a+d;
    const off=(lh-a-d)/2+a-m.actualBoundingBoxAscent;n.style.marginTop=(lg.getBoundingClientRect().top-(t.getBoundingClientRect().top+off))+'px'}})}
function tnFit(){
  // FAAB tiles: one width (the widest balance), so the FAAB labels beside them line up down the board
  const fb=[...document.querySelectorAll('.board .r .nm .fab b')].filter(b=>b.offsetParent);fb.forEach(b=>b.style.width='');const fw=Math.max(0,...fb.map(b=>b.getBoundingClientRect().width));fb.forEach(b=>b.style.width=fw+'px');
  // names end 6px short of the widest record tile (W3 4-3) on the board, the same on every row
  const R=[...document.querySelectorAll('.board .r')].map(r=>[r.querySelector(':scope>.nm'),r.querySelector('.side .rr')]).filter(([n,k])=>n&&k&&n.offsetParent);
  R.forEach(([n])=>n.style.paddingRight='');const pr=Math.max(0,...R.map(([n,k])=>n.getBoundingClientRect().right-Math.min(...[...k.children].map(c=>c.getBoundingClientRect().left))+6));R.forEach(([n])=>n.style.paddingRight=pr+'px');
  document.querySelectorAll('.board .r .tn').forEach(e=>{if(!e.offsetParent)return;e.style.fontSize='';e.style.whiteSpace='nowrap';e.style.lineHeight='';
  const f0=parseFloat(getComputedStyle(e).fontSize),ov=()=>e.scrollWidth>e.clientWidth+.5;let f=f0;while(ov()&&f>f0*.85){f-=.5;e.style.fontSize=f+'px'}
  if(ov()){e.style.whiteSpace='normal';e.style.lineHeight='1.12';f=f0;e.style.fontSize=f+'px';
    const fit=n=>{let g=f0;const bad=()=>ov()||e.getBoundingClientRect().height>n*1.12*g+1||(n>2&&n*1.12*g>52);e.style.fontSize=g+'px';while(bad()&&g>11){g-=.5;e.style.fontSize=g+'px'}return g};
    f=fit(2);if(f<15){const g=fit(3);if(g<=f)e.style.fontSize=(f=fit(2))+'px'}}});if(typeof ravFit==='function')ravFit();mvAl()}
// tabs: one shared font size, shrunk just enough that the longest label keeps at least 8px from its frame on each side
function tabFit(){const L=[...document.querySelectorAll('nav.tabs label')].filter(l=>l.offsetParent);if(!L.length)return;L.forEach(l=>l.style.fontSize='');
let k=1;L.forEach(l=>{const rg=document.createRange();rg.selectNodeContents(l);const tw=rg.getBoundingClientRect().width;const ls=parseFloat(getComputedStyle(l).letterSpacing)||0;const room=l.getBoundingClientRect().width-2-16;const w=tw-ls;if(w>room)k=Math.min(k,room/w)});
if(k<1){const f=parseFloat(getComputedStyle(L[0]).fontSize)*k;L.forEach(l=>l.style.fontSize=(Math.floor(f*4)/4)+'px')}}
if(!FL())tabFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(tabFit);document.fonts&&document.fonts.addEventListener('loadingdone',()=>{tabFit();tnFit()});addEventListener('resize',()=>requestAnimationFrame(tabFit));
// standings logo: top on the team name's cap line, bottom on the Hi/Lo/Avg baseline (measured from the glyphs, per row)
const _cv=document.createElement('canvas').getContext('2d');
function _ink(el,txt){const c=getComputedStyle(el);_cv.font=c.fontStyle+' '+c.fontWeight+' '+c.fontSize+' '+c.fontFamily;const m=_cv.measureText(txt);const rg=document.createRange();rg.selectNodeContents(el);const r=rg.getClientRects()[0]||el.getBoundingClientRect();
  const base=r.top+(r.height-(m.fontBoundingBoxAscent+m.fontBoundingBoxDescent))/2+m.fontBoundingBoxAscent;return {cap:base-_cv.measureText('H').actualBoundingBoxAscent,base}}
function ravFit(){let mx=0;const bd=document.querySelector('.board');document.querySelectorAll('.board .r').forEach(r=>{const a=r.querySelector('.rav.av'),tn=r.querySelector('.tn'),lb=r.querySelector('.hl .lb');if(!a||!tn||!lb||!r.offsetParent)return;
  a.style.transform='';const z=a.currentCSSZoom||1;const top=_ink(tn,'H').cap,bot=_ink(lb,'H').base;const H=Math.max(12,bot-top)/z;mx=Math.max(mx,H);a.style.flex='0 0 '+H.toFixed(2)+'px';
  a.style.width=a.style.height=H.toFixed(2)+'px';const at=a.getBoundingClientRect().top;a.style.transform='translateY('+((top-at)/z).toFixed(2)+'px)'});if(bd&&mx)document.querySelectorAll('.board').forEach(b=>b.style.setProperty('--ravc',mx.toFixed(2)+'px'))}
// standings stat lines: one shared text scale (1 = 15px), lowered in small steps until no line is clipped
// desktop (>=1100px): only the left-hand lines (PF, PA) set the shared scale; Tot Eff sits in the wide right-hand column.
// If even the floor (0.68) cannot make a line fit, the scale goes back to 1: shrinking every line for a lost cause made the
// text and dots jump between full size and the floor on a 1px width change.
const SBQ=matchMedia('(min-width:1100px)');
function sbLines(bd){return [...bd.querySelectorAll('.sb .stx:not(.spl)')].filter(x=>x.offsetParent&&!(SBQ.matches&&x.closest('.s-lu')))}
// The scale and text column are set on the elements that use them (.sb / .st lines), not on the board (2026-11-04): a custom
// property or class on .board restyles all ~3,500 board elements at every step, and WebKit keeps that peak (Safari +400 MB on load).
// Same computed values: every consumer of --sbs / --stw2 / --s2s sits in one of these elements; .sbm is set on the .sb blocks themselves.
const sbEls=bd=>bd.querySelectorAll('.r .sb,.r .st'),sbBlk=bd=>bd.querySelectorAll('.r>.sb');
function sbSet(bd,k){bd.__sbs=k;const v=typeof k==='number'?k.toFixed(2):k;sbEls(bd).forEach(e=>e.style.setProperty('--sbs',v))}
function sbFit(){document.querySelectorAll('.board').forEach(bd=>{if(!bd.offsetParent)return;const B=sbBlk(bd);B.forEach(e=>e.classList.add('sbm'));sbSet(bd,'1');const L=sbLines(bd);let k=1;
  B.forEach(e=>{e.style.removeProperty('--stw2');e.classList.remove('sbw')});const ov=()=>L.some(x=>x.scrollWidth>x.clientWidth+.5);
  if(ov())B.forEach(e=>e.classList.add('sbw'))  // 2026-11-05 text floor: stat lines are never scaled below 1; the per-week part wraps under the figure instead
  // then the text column shrinks to the longest line, so the dots sit just after the text (all lines aligned)
  const mw=Math.max(0,...L.filter(x=>x.closest('.sb')).map(x=>{const rg=document.createRange();rg.selectNodeContents(x);const a=rg.getBoundingClientRect(),b=x.getBoundingClientRect();return a.right-b.left}));
  if(mw)B.forEach(e=>e.style.setProperty('--stw2',Math.ceil(mw+2)+'px'));B.forEach(e=>e.classList.remove('sbm'))});if(typeof tileFit==='function'){tileFit();
  // the rank tiles resize with the text: if a line now overflows, step the scale down again (a few passes at most)
  for(let n=0;n<4;n++){let again=false;document.querySelectorAll('.board').forEach(bd=>{if(!bd.offsetParent)return;const L=sbLines(bd);
    if(L.some(x=>x.scrollWidth>x.clientWidth+.5)){const B=sbBlk(bd);if(![...B].every(e=>e.classList.contains('sbw'))){B.forEach(e=>e.classList.add('sbw'));again=true}}});if(!again)break;tileFit()}}}
// Opp rk · All-play · Luck line: full size always; if it does not fit, Luck wraps to a second line (all rows together)
function s2Fit(){document.querySelectorAll('.board').forEach(bd=>{const A=bd.querySelectorAll('.r>.st.s2'),S=v=>A.forEach(e=>e.style.setProperty('--s2s',v));const L=[...A].filter(x=>x.offsetParent);S('1');L.forEach(x=>x.classList.remove('wrp'));let k=1;
  const over=()=>L.some(x=>x.scrollWidth>x.clientWidth+.5);  // 2026-11-05 text floor: never scaled below 1
  if(over())L.forEach(x=>x.classList.add('wrp'))});if(typeof tileFit==='function')tileFit()}
if(!FL())s2Fit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(s2Fit);addEventListener('resize',()=>requestAnimationFrame(s2Fit));document.addEventListener('change',()=>requestAnimationFrame(s2Fit));document.fonts&&document.fonts.addEventListener('loadingdone',s2Fit);
// dropdown labels (Compare team pickers etc.): shrink a long name to fit instead of an ellipsis
function ddFit(){document.querySelectorAll('.dd summary .sv').forEach(v=>{if(!v.offsetParent)return;v.style.fontSize='';let f=parseFloat(getComputedStyle(v).fontSize);while(v.scrollWidth>v.clientWidth+.5&&f>11){f-=.5;v.style.fontSize=f+'px'}})}
if(!FL())ddFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(ddFit);addEventListener('resize',()=>requestAnimationFrame(ddFit));document.addEventListener('change',()=>requestAnimationFrame(ddFit));document.fonts&&document.fonts.addEventListener('loadingdone',ddFit);
if(!FL())sbFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(sbFit);addEventListener('resize',()=>requestAnimationFrame(sbFit));document.addEventListener('change',()=>requestAnimationFrame(sbFit));document.fonts&&document.fonts.addEventListener('loadingdone',sbFit);
if(!FL())ravFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(ravFit);addEventListener('resize',()=>requestAnimationFrame(ravFit));document.addEventListener('change',()=>requestAnimationFrame(ravFit));document.fonts&&document.fonts.addEventListener('loadingdone',ravFit);
if(!FL())tnFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(tnFit);addEventListener('resize',()=>requestAnimationFrame(tnFit));document.addEventListener('change',()=>requestAnimationFrame(tnFit));
// rank tiles never taller than the figure they rank: tile top = the figure's digit top, tile bottom = its baseline
(function(){
const FM={};
const FMC=document.createElement('canvas').getContext('2d');  // one canvas for all metric reads (2026-11-04: a new canvas per font, per run, was ~25 live canvases in Safari)
function fm(cs){const k=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;if(FM[k])return FM[k];const c=FMC;c.font=k;const m=c.measureText('0123456789');return FM[k]={cap:m.actualBoundingBoxAscent,asc:m.fontBoundingBoxAscent,desc:m.fontBoundingBoxDescent}}
function txt(n){if(n.nodeType===3)return n;const w=document.createTreeWalker(n,NodeFilter.SHOW_TEXT,{acceptNode:x=>x.textContent.trim()&&!x.parentElement.closest('.lku')?1:3});let l=null,x;while(x=w.nextNode())l=x;return l}
function ref(t){let n=t.previousSibling;while(n&&n.nodeType===3&&!n.textContent.trim())n=n.previousSibling;
  if(n&&n.nodeType===1&&n.matches('.ch,.rkb,svg,.av,.pav,.pz,.nfl,.pba,img'))return null;
  if(!n){if(t.classList.contains('rkb'))return {own:true,el:t.parentElement};const ps=t.parentElement.previousElementSibling;if(ps&&!t.previousElementSibling){const tn=txt(ps);if(tn&&/[0-9]/.test(tn.textContent))return {tn,el:tn.parentElement}}return null}
  const tn=txt(n);if(!tn||!/[0-9A-Za-z%]/.test(tn.textContent))return null;return {tn,el:tn.parentElement}}
function fit(){
  for(const k in FM)delete FM[k];  // font metrics are re-read each run: a run before the web fonts load must not leave the fallback font's metrics cached
  const tiles=[...document.querySelectorAll('.ch,.rkb')].filter(t=>t.offsetParent&&!t.closest('.gm,.sxm,.lbr,.hmx,.tqgrid,.mx,.bym,.pskey'));
  const jobs=[];
  for(const t of tiles)t.style.removeProperty('transform');  // clear old offsets first: a stale one makes a tile look off its line and it would be skipped for good
  // reads first, writes after (2026-11-04): a marker inserted or an attribute set between two tiles' reads forced a layout per tile,
  // ~1,900 layouts on load, and WebKit keeps the memory those passes use (Safari +400 MB)
  const oh=[];
  for(const t of tiles){const r=ref(t);if(!r)continue;const cs=getComputedStyle(r.el),m=fm(cs),z=t.currentCSSZoom||1;
    if(!t.dataset.oh){const ct0=t.querySelector('.ct')||t;oh.push([t,t.getBoundingClientRect().height/z,parseFloat(getComputedStyle(ct0).fontSize)])}
    let inline=false;
    if(r.tn){const g=document.createRange();g.selectNodeContents(r.tn);const rr=g.getBoundingClientRect(),tr=t.getBoundingClientRect();inline=tr.bottom>rr.top&&tr.top<rr.bottom}
    if(!inline)continue;jobs.push({t,cap:m.cap,tn:r.tn,zc:r.el.currentCSSZoom||z,z})}
  for(const [t,h,f] of oh){t.dataset.oh=h;t.dataset.of=f}
  for(const j of jobs){const pb=document.createElement('i');pb.style.cssText='display:inline-block;width:0;height:0;padding:0;margin:0;border:0;vertical-align:baseline';j.tn.after(pb);j.pb=pb}
  inkBatch(jobs.map(j=>[j.t,Math.floor(j.cap*4)/4]));  // as tall as the figure beside it and never taller: tile height = its cap height (to 0.25px)
  for(const j of jobs)j.t.style.removeProperty('transform');  // measure from the untransformed spot, so a re-run never stacks offsets
  for(const j of jobs){j.mid=j.pb.getBoundingClientRect().bottom-j.cap*j.zc/2}  // read after sizing, so the line has settled: the figure's real baseline (a zero-size marker on it), not one estimated from font metrics: those are rounded differently by layout
  for(const j of jobs)j.pb.remove();
  for(const j of jobs){  // centre every tile on the figure's cap height (a flex row centres on the line box, which sits lower)
    const tr=j.t.getBoundingClientRect(),d=(j.mid-(tr.top+tr.bottom)/2)/j.z;if(Math.abs(d)>0.01)j.t.style.setProperty('transform','translateY('+d.toFixed(2)+'px)','important')}
}
// size one rank tile from the digits' ink: outer height H, the same gap from ink to edge on top and bottom, the same on
// left and right, never closer than 1.75px to the frame (the number shrinks to make room); width fixed for two digits so a column lines up
const INK=document.createElement('canvas').getContext('2d');
function inkPlan(t,H){if(!(window.CSS&&CSS.supports('text-box','trim-both cap alphabetic')))return null;  // reads only
  const txt=t.textContent.trim();if(!txt)return null;const cs=getComputedStyle(t.querySelector('.ct')||t),fam=cs.fontFamily,wt=cs.fontWeight;
  const b=getComputedStyle(t),bw=(parseFloat(b.borderTopWidth)||0)+(parseFloat(b.borderBottomWidth)||0);const Ho=H;H-=bw;  // H is the outer height: a bordered (outlined) tile loses its border from it
  const P=Math.max(1.75,Math.min(3.5,(H-6)/2-1)),cap=H-2*P;  // gap from digit ink to frame: 1.75-3.5px, so the digits fill the tile
  INK.font=`${wt} 100px ${fam}`;const _d=INK.measureText('0123456789');const fs=Math.floor(cap/((_d.actualBoundingBoxAscent+_d.actualBoundingBoxDescent)/100)*4)/4;  // sized on the digits' ink (they can rise above the H cap), so the outer height never exceeds H
  INK.font=`${wt} ${fs}px ${fam}`;const m=INK.measureText(txt),m2=INK.measureText('88'),Hc=INK.measureText('H').actualBoundingBoxAscent;
  const m3=INK.measureText(t.dataset.ref||'88');const iw=m.actualBoundingBoxLeft+m.actualBoundingBoxRight,iw2=Math.max(m2.actualBoundingBoxLeft+m2.actualBoundingBoxRight,m3.actualBoundingBoxLeft+m3.actualBoundingBoxRight),W=Math.max(iw,iw2)+2*(P+0.5);
  return {t,Ho,P,fs,iw,W,gl:m.actualBoundingBoxLeft*-1,gr:m.width-m.actualBoundingBoxRight,gt:Hc-m.actualBoundingBoxAscent,gb:-m.actualBoundingBoxDescent,z:t.currentCSSZoom||1}}
function inkPad(p,e){return `${(p.P-p.gt+e).toFixed(2)}px ${((p.W-p.iw)/2-p.gr).toFixed(2)}px ${(p.P-p.gb+e).toFixed(2)}px ${((p.W-p.iw)/2-p.gl).toFixed(2)}px`}
function inkSet(p){const t=p.t,s=t.style,set=(k,v)=>s.setProperty(k,v,'important');  // writes only
  set('display','inline-block');set('text-box','trim-both cap alphabetic');set('line-height','1');set('height','auto');set('min-height','0');set('min-width','0');set('width','auto');
  set('box-sizing','content-box');set('font-size',p.fs+'px');set('letter-spacing','0');set('font-variant-numeric','normal');set('font-feature-settings','normal');set('top','0');set('transform','none');set('vertical-align','baseline');
  set('padding',inkPad(p,0));
  const ct=t.querySelector('.ct');if(ct){for(const [k,v] of [['font-size','inherit'],['line-height','1'],['display','inline'],['height','auto'],['letter-spacing','0'],['font-variant-numeric','normal'],['text-box','none']])ct.style.setProperty(k,v,'important')}}
// outer height exactly H: split the rounding error between top and bottom (frames are inset shadows, inside H)
function inkErr(p){return (p.Ho-p.t.getBoundingClientRect().height/p.z)/2}
function inkFix(p,e){if(Math.abs(e)>0.01)p.t.style.setProperty('padding',inkPad(p,e),'important')}
// many tiles at once: all reads, all writes, one layout for the heights, all corrections (each tile's height depends only on its own style)
function inkBatch(list){const ps=list.map(([t,H])=>inkPlan(t,H)).filter(Boolean);ps.forEach(inkSet);const es=ps.map(inkErr);ps.forEach((p,i)=>inkFix(p,es[i]));return ps.length}
function inkTile(t,H){const p=inkPlan(t,H);if(!p)return false;inkSet(p);inkFix(p,inkErr(p));return true}
// sim Finish tile: as tall as the projection figures beside it (the 2%), sitting level with them
function finFit(){document.querySelectorAll('.dso .rkb').forEach(k=>{if(!k.offsetParent)return;const v=k.closest('.dpc').nextElementSibling;const vs=v&&v.querySelector('span');if(!vs)return;
  const cs=getComputedStyle(vs),fm0=fm(cs),z=k.currentCSSZoom||1;if(!inkTile(k,Math.round(fm0.cap*2)/2))return;
  const g=document.createRange();g.selectNodeContents(vs);const rr=g.getBoundingClientRect(),zz=rr.height/(fm0.asc+fm0.desc),base=rr.top+fm0.asc*zz,mid=base-fm0.cap*zz/2;
  const kr=k.getBoundingClientRect(),d=(mid-(kr.top+kr.bottom)/2)/zz;k.style.setProperty('transform','translateY('+d.toFixed(2)+'px)','important')})}
// matchup points bar: pinned under the tabs while you scroll the lineups, and slimmed down once pinned
(function(){const nav=document.querySelector('nav.tabs');let h0=new WeakMap(),raf=0;
function navh(){const v=nav&&getComputedStyle(nav).position==='sticky'?Math.round(nav.getBoundingClientRect().height):0;document.documentElement.style.setProperty('--navh',v+'px');return v}
function upd(){raf=0;const nh=navh();document.querySelectorAll('.ltot').forEach(b=>{if(!b.offsetParent)return;const top=b.getBoundingClientRect().top;const pr=b.parentElement.getBoundingClientRect();
 const on=top<=nh+6.5&&pr.top<nh;if(on===b.classList.contains('stk'))return;
 if(on){const H=b.getBoundingClientRect().height;b.classList.add('stk');b.style.marginBottom=(parseFloat(getComputedStyle(b).marginBottom)||0)+(H-b.getBoundingClientRect().height)+'px'}
 else{b.classList.remove('stk');b.style.marginBottom=''}})}
const go=()=>{if(!raf)raf=requestAnimationFrame(upd)};addEventListener('scroll',go,{passive:true});addEventListener('resize',go);document.addEventListener('change',go);go()})();
// YILM title: one line, as large as fits the width (max 88px)
(function(){function f(){document.querySelectorAll('h1.yh').forEach(h=>{h.style.fontSize='';const m=parseFloat(getComputedStyle(h).fontSize);const w=h.clientWidth;if(!w)return;const R=document.createRange();R.selectNodeContents(h);let fs=Math.min(88,m*w/R.getBoundingClientRect().width);h.style.fontSize=fs.toFixed(2)+'px';let i=0;while(h.scrollWidth>h.clientWidth+0.5&&i++<20){fs-=0.5;h.style.fontSize=fs+'px'}})}
f();addEventListener('resize',f);if(document.fonts)document.fonts.ready.then(f)})();
let q=0;function sched(){if(q)return;q=requestAnimationFrame(()=>{q=0;fit();finFit();document.querySelectorAll('.tqt[data-h]:not([data-ok])').forEach(t=>{if(inkTile(t,+t.dataset.h))t.dataset.ok=1});document.querySelectorAll('.trc .tro2 b').forEach(el=>{if(!el.offsetParent)return;el.style.fontSize='';let f=parseFloat(getComputedStyle(el).fontSize);while((el.scrollWidth>el.clientWidth+0.5||el.scrollHeight>el.clientHeight+0.5)&&f>11){f-=0.5;el.style.fontSize=f+'px'}})})}
window.tileFit=fit;window.finFit=finFit;window.inkTile=inkTile;window.inkBatch=inkBatch;if(!FL())sched();addEventListener('resize',sched);document.addEventListener('change',()=>setTimeout(sched,0));document.addEventListener('click',()=>setTimeout(sched,0));
if(document.fonts){document.fonts.ready.then(()=>{for(const k in FM)delete FM[k];document.querySelectorAll('.tqt[data-ok]').forEach(t=>delete t.dataset.ok);sched()});document.fonts.addEventListener&&document.fonts.addEventListener('loadingdone',()=>{for(const k in FM)delete FM[k];sched()})}
})();
addEventListener('resize',()=>requestAnimationFrame(pfit));document.addEventListener('click',()=>requestAnimationFrame(pfit));
document.addEventListener('click',e=>{const l=e.target.closest('.ddm label');if(l)setTimeout(()=>{l.closest('details').open=false},0);const o=document.querySelectorAll('details.dd[open]');o.forEach(d=>{if(!d.contains(e.target))d.open=false})});
// FAAB tiles: the build's balances, then a fresh read from Sleeper (it allows any origin) so a balance spent since the last build shows at once
if(typeof FAABL!=='undefined'&&window.fetch)fetch('https://api.sleeper.app/v1/league/'+FAABL+'/rosters',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(ro=>{if(!Array.isArray(ro))return;let ch=0;
  for(const x of ro){const t=FAABR[x.roster_id];if(!t||!(t in FAAB))continue;const v=FAABB-(+((x.settings||{}).waiver_budget_used)||0);if(v!==FAAB[t]){FAAB[t]=v;ch=1}}
  if(!ch)return;document.querySelectorAll('.board .r').forEach(r=>{const t=r.dataset.t,f=r.querySelector('.fab');if(f&&t in FAAB){f.querySelector('b').textContent='$'+FAAB[t];f.title=`FAAB left: $${FAAB[t]} of $${FAABB} (opens The Wire)`}});tnFit()}).catch(()=>{});

// Rosters: season totals sit beside GP and bye; a row whose line would reach the points drops them onto their own line
(function(){function rslFit(){document.querySelectorAll('.rr2').forEach(r=>{const s=r.querySelector('.rsl');if(!s||!r.offsetParent)return;r.classList.remove('rsw');
  const v=r.querySelector('.rv'),sm=s.parentElement;if(s.getBoundingClientRect().right>v.getBoundingClientRect().left-8||sm.scrollWidth>sm.clientWidth+0.5)r.classList.add('rsw')})}
 const go=()=>requestAnimationFrame(rslFit);go();addEventListener('resize',go);document.addEventListener('change',go);document.addEventListener('click',go);
 if(document.fonts){document.fonts.ready.then(go);document.fonts.addEventListener&&document.fonts.addEventListener('loadingdone',go)}})();
// Standings card, right column (rrFit): the streak tile is the record's cap height, centred on it; "Could have" /
// "Breakdown" starts level with the top of the OPP line (cap tops). Record and dots sizes are CSS (readability.css, +15%).
(function(){const C=document.createElement('canvas').getContext('2d');
function capOf(el,s){const cs=getComputedStyle(el);C.font=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;return C.measureText(s||'0123456789').actualBoundingBoxAscent*(el.currentCSSZoom||1)}
function txt(el,last){const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let t=null,x;while(x=w.nextNode())if(x.textContent.trim()){t=x;if(!last)break}return t}
function base(tn){const p=document.createElement('i');p.style.cssText='display:inline-block;width:0;height:0;padding:0;margin:0;border:0;vertical-align:baseline';tn.after(p);const b=p.getBoundingClientRect().bottom;p.remove();return b}
function rrFit(){
  const rows=[...document.querySelectorAll('.board .r')].filter(r=>r.offsetParent&&r.querySelector('.side .rr b'));
  rows.forEach(r=>{const sb=r.querySelector('.side .subw');if(sb)sb.style.removeProperty('margin-top')});
  rows.forEach(r=>{const k=r.querySelector('.side .l5r .sk'),b=r.querySelector('.side .rr b');if(!k||!window.inkTile)return;k.style.removeProperty('transform');
    const cs=getComputedStyle(b);C.font=cs.fontStyle+' '+cs.fontWeight+(matchMedia('(max-width:380px)').matches?' 22px ':' 26px ')+cs.fontFamily;window.inkTile(k,Math.floor(C.measureText('0123456789').actualBoundingBoxAscent*4)/4)});
  rows.forEach(r=>{const sb=r.querySelector('.side .subw');if(!sb||!sb.offsetParent)return;const lt=txt(sb,0);if(!lt)return;const z=sb.currentCSSZoom||1;
    const ab=r.querySelector('.side .l5r')||r.querySelector('.side .l5d'),floor=ab.getBoundingClientRect().bottom+4*z,me=base(lt)-capOf(lt.parentElement,'HOPC');
    const lines=[...r.querySelectorAll(':scope>.st, :scope>.sb')].filter(e=>e.offsetParent&&!r.querySelector('.side').contains(e));let tgt=null;
    for(const L of lines){for(const el of L.querySelectorAll('.lb,em,b,span')){if(!el.offsetParent)continue;const t=txt(el,0);if(!t)continue;const top=base(t)-capOf(t.parentElement,'HOPC');if(top>=floor-0.5&&(tgt===null||top<tgt))tgt=top;break}}
    if(tgt===null)return;const m=parseFloat(getComputedStyle(sb).marginTop)||0;sb.style.setProperty('margin-top',(m+(tgt-me)/z).toFixed(2)+'px','important')});
  if(typeof tnFit==='function')tnFit()}
window.rrFit=rrFit;const go=()=>requestAnimationFrame(()=>requestAnimationFrame(rrFit));go();addEventListener('resize',go);document.addEventListener('change',go);document.addEventListener('click',go);
if(document.fonts){document.fonts.ready.then(go);document.fonts.addEventListener&&document.fonts.addEventListener('loadingdone',go)}})();
// desktop (>=1100px): stack the Nerd blocks of each standings row in its right-hand column (all share one grid cell)
(function(){const mq=matchMedia('(min-width:1100px)');
function nrdFit(){document.querySelectorAll('#list .r').forEach(r=>{const els=[...r.querySelectorAll(':scope>.s-lu,:scope>.s-sk,:scope>.szw')];
  els.forEach(e=>e.style.removeProperty('margin-top'));if(!mq.matches)return;let y=0;
  els.forEach(e=>{if(!e.offsetParent)return;e.style.setProperty('margin-top',y+'px','important');y+=e.getBoundingClientRect().height/(e.currentCSSZoom||1)+(e.classList.contains('s-lu')?12:16)})})}
window.nrdFit=nrdFit;const go=()=>requestAnimationFrame(()=>requestAnimationFrame(nrdFit));go();addEventListener('resize',go);document.addEventListener('change',go);document.addEventListener('click',go);
if(document.fonts){document.fonts.ready.then(go);document.fonts.addEventListener&&document.fonts.addEventListener('loadingdone',go)}})();

/* pcnFit: matrix row labels on phones (face + manager name): shrink a long manager name until it fits its label (floor 10px) */
(function(){function pcnFit(){document.querySelectorAll('.sxm .mxn .pcn').forEach(function(n){if(!n.offsetParent)return;n.style.fontSize='';var p=n.parentElement,s=parseFloat(getComputedStyle(n).fontSize);
 while((p.scrollWidth>p.clientWidth+.5||n.getBoundingClientRect().right>p.getBoundingClientRect().right+.5)&&s>11){s-=.5;n.style.fontSize=s+'px'}})}
 if(!FL())pcnFit();addEventListener('resize',function(){requestAnimationFrame(pcnFit)});document.addEventListener('change',function(){requestAnimationFrame(pcnFit)});document.fonts&&document.fonts.ready.then(pcnFit)})();

/* dtPanels (desktop table, standings order): each tier becomes its own raised panel. The table is first laid out whole so
   every column gets one natural width; those widths (visible header cells, CSS zoom removed) become a fixed colgroup on
   every panel's table, so columns line up across panels. Each panel: tier band across the non-sim columns, the sim
   columns' cell beside it (the first panel's carries the "20k simulations" label; the others stay plain), then rows; the
   first panel also carries the column headers under its band. The band's "Line" figure is dropped here. */
function dtPanels(box){
  const t=box.querySelector('table.dtt');if(!t)return;
  const hr=t.querySelector('thead tr:last-child'),hs=[...hr.children].filter(c=>c.offsetParent);if(!hs.length)return;
  const z=box.currentCSSZoom||1,TW=Math.floor(t.getBoundingClientRect().width/z),W=hs.map(c=>Math.floor(c.getBoundingClientRect().width/z)),NS=hs.length-3;W[1]+=TW-W.reduce((a,b)=>a+b,0);  // whole pixels; the team column takes the remainder, so every panel lays out identically
  const cg=()=>'<colgroup>'+W.map(w=>`<col style="width:${w}px">`).join('')+'</colgroup>';
  const hdr=hr.outerHTML,groups=[];
  for(const tr of t.tBodies[0].rows){if(tr.classList.contains('dtb'))groups.push({band:tr,rows:[]});else if(groups.length)groups[groups.length-1].rows.push(tr)}
  if(!groups.length)return;
  box.innerHTML=groups.map((g,i)=>{const b=g.band,bh=b.querySelector('.dtbh'),em=bh&&bh.querySelector('em');if(em)em.remove();
    const band=`<tr class="${b.className}"><td class="dtbb" colspan="${NS}">${bh?bh.outerHTML:''}</td><td class="dsc" colspan="3">${i?'':'<span>20k simulations</span>'}</td></tr>`;
    return `<div class="dtp"><table class="dtt dtf" style="width:${TW}px">${cg()}${i?'<tbody>'+band:'<thead>'+band+hdr+'</thead><tbody>'}${g.rows.map(r=>r.outerHTML).join('')}</tbody></table></div>`}).join('')}
addEventListener('resize',()=>{clearTimeout(window._dtR);window._dtR=setTimeout(()=>{const b=document.getElementById('bm');if(window.innerWidth>=1100&&typeof dtab==='function')dtab(!!b&&b.getAttribute('aria-pressed')==='true')},120)});
document.fonts&&document.fonts.ready.then(()=>{const b=document.getElementById('bm');if(typeof dtab==='function')dtab(!!b&&b.getAttribute('aria-pressed')==='true')});
// Desktop table: equal space either side of the simulations divider (Nicklaus, 2026-11-03). Proj finish gets 16px
// padding; the column before the divider (Tot eff) gets the padding-right that puts its glyph ink exactly as far from the
// divider as Proj finish's content is on the other side (judged by ink: canvas bearings on the last/first glyph).
const _sgc=document.createElement('canvas').getContext('2d');
function _sgBear(e,txt,side){const s=getComputedStyle(e);_sgc.font=s.fontStyle+' '+s.fontWeight+' '+s.fontSize+' '+s.fontFamily;
  if(s.letterSpacing&&s.letterSpacing!=='normal')try{_sgc.letterSpacing=s.letterSpacing}catch(_){}
  let ch=side==='r'?txt.slice(-1):txt[0];if(s.textTransform==='uppercase')ch=ch.toUpperCase();const m=_sgc.measureText(ch);
  return side==='r'?(m.width-m.actualBoundingBoxRight):(-m.actualBoundingBoxLeft)}  // blank space inside the text box on that side
function _sgEdge(cell,side){let v=side==='r'?-1e9:1e9;const w=document.createTreeWalker(cell,NodeFilter.SHOW_TEXT);let n;
  while(n=w.nextNode()){const t=n.textContent.replace(/\s+$/,'').replace(/^\s+/,'');if(!t)continue;const e=n.parentElement;if(!e.getClientRects().length)continue;
    const rg=document.createRange();rg.selectNodeContents(n);for(const r of rg.getClientRects()){if(!r.width)continue;
      if(side==='r')v=Math.max(v,r.right-_sgBear(e,t,'r'));else v=Math.min(v,r.left+_sgBear(e,t,'l'))}}
  if(side==='l')cell.querySelectorAll('*').forEach(e=>{const b=getComputedStyle(e).backgroundColor;if(b!=='rgba(0, 0, 0, 0)'&&!/, 0\)$/.test(b)){const r=e.getBoundingClientRect();if(r.width)v=Math.min(v,r.left)}});
  return v}
function simGap(){if(innerWidth<1100)return;const t=document.querySelector('.dtp .dtt');if(!t||!t.offsetParent)return;const pre=[],fin=[];
  t.querySelectorAll('tr').forEach(tr=>{const f=tr.querySelector('td.dfin,th[data-k="fin"]');if(!f||!f.offsetParent)return;let p=f.previousElementSibling;while(p&&!p.offsetParent)p=p.previousElementSibling;if(p){pre.push(p);fin.push(f)}});
  if(!pre.length)return;pre.forEach(p=>p.style.removeProperty('padding-right'));fin.forEach(f=>f.style.removeProperty('padding-left'));
  // the width the wider Tot eff column needs comes from TEAM only: pin every other column at its natural width first
  const hr=[...t.querySelectorAll('thead tr')].pop(),hs=hr?[...hr.children].filter(c=>c.offsetParent):[];hs.forEach(h=>h.style.removeProperty('width'));
  const keep=hs.filter(h=>!['team','fin'].includes(h.dataset.k)&&h!==pre[pre.length-1]&&!pre.includes(h)).map(h=>[h,h.getBoundingClientRect().width]);
  keep.forEach(([h,wd])=>{h.style.boxSizing='border-box';h.style.width=wd+'px'});
  fin.forEach(f=>f.style.setProperty('padding-left','16px','important'));  // 16px from the divider to Proj finish
  let R=1e9,L=1e9;fin.forEach((f,i)=>{const fb=f.getBoundingClientRect(),dl=fb.left,dr=dl+parseFloat(getComputedStyle(f).borderLeftWidth);
    R=Math.min(R,_sgEdge(f,'l')-dr);L=Math.min(L,dl-_sgEdge(pre[i],'r'))});
  if(!isFinite(R)||!isFinite(L))return;const np=parseFloat(getComputedStyle(pre[0]).paddingRight)+(R-L);
  pre.forEach(p=>p.style.setProperty('padding-right',Math.max(0,np).toFixed(2)+'px','important'));
  // one correction pass: a wider column can re-centre Proj finish
  let R2=1e9,L2=1e9;fin.forEach((f,i)=>{const fb=f.getBoundingClientRect(),dl=fb.left,dr=dl+parseFloat(getComputedStyle(f).borderLeftWidth);R2=Math.min(R2,_sgEdge(f,'l')-dr);L2=Math.min(L2,dl-_sgEdge(pre[i],'r'))});
  if(Math.abs(R2-L2)>.25)pre.forEach(p=>p.style.setProperty('padding-right',Math.max(0,np+(R2-L2)).toFixed(2)+'px','important'))}
// every dtab render (load, fonts, resize, sort, H2H/Median): fit the new rank chips first, then simGap, so the pinned column widths
// are always measured on fitted chips (2026-11-04: a resize re-draw left the chips unfitted, 1-2px drift)
if(typeof dtab==='function'){const _dt0=dtab;dtab=function(){const r=_dt0.apply(this,arguments);requestAnimationFrame(()=>{if(typeof tileFit==='function')tileFit();simGap()});return r}}
(()=>{let q=0;new MutationObserver(ms=>{if(q||innerWidth<1100)return;if(!ms.some(m=>m.target.closest&&m.target.closest('.dtp')))return;q=requestAnimationFrame(()=>{q=0;simGap()})}).observe(document.body,{childList:true,subtree:true})})();
document.fonts&&document.fonts.ready.then(()=>requestAnimationFrame(simGap));addEventListener('resize',()=>setTimeout(simGap,200));
// Navigation groups (Nicklaus, 2026-11-03). Group follows the selected tab (labels, the FAAB tile, code, #hash);
// picking a group opens its first tab (Game Day opens Playoffs once Week 14 is done, current season only).
// Defaults: Game Day > Standings (Playoffs in the playoffs); a #hash deep link wins. The current tab is kept in the URL hash
// (2026-11-08, Nicklaus): every tab change after load writes its hash with replaceState (Back never steps through tabs), so a
// refresh reopens it; a plain URL opens the defaults. A year button carries the tab's hash when the URL has one.
(function(){const nav=document.querySelector('.tnav');if(!nav)return;
 const GR={gd:['tab-st','tab-mu','tab-po'],lab:['tab-sx','tab-lb','tab-cm','tab-th'],fo:['tab-ro','tab-pl','tab-wr','tab-df','tab-pt']};
 const has=id=>!!document.getElementById(id),grpOf=id=>Object.keys(GR).find(g=>GR[g].includes(id)),PO=nav.dataset.po==='1';
 const first=g=>(g==='gd'&&PO&&has('tab-po'))?'tab-po':GR[g].find(has);
 const SLUG={standings:'tab-st',matchups:'tab-mu',playoffs:'tab-po',stats:'tab-sx',leaderboards:'tab-lb',compare:'tab-cm','team-hub':'tab-th',teamhub:'tab-th',hub:'tab-th',rosters:'tab-ro',players:'tab-pl','the-wire':'tab-wr',wire:'tab-wr',drafts:'tab-df','paper-trail':'tab-pt',papertrail:'tab-pt'};
 const CANON={'tab-st':'standings','tab-mu':'matchups','tab-po':'playoffs','tab-sx':'stats','tab-lb':'leaderboards','tab-cm':'compare','tab-th':'team-hub','tab-ro':'rosters','tab-pl':'players','tab-wr':'the-wire','tab-df':'drafts','tab-pt':'paper-trail'};
 let live=false;
 function hBase(){let h='';try{h=decodeURIComponent(location.hash.slice(1)).trim().toLowerCase()}catch(_){}return h.split('/')[0]}
 // keep(): the tab's canonical hash, unless the URL already names this tab (an alias such as #wire, or a #paper-trail/... sheet)
 function keep(id){if(!live||!CANON[id])return;const h=hBase();if(h&&(SLUG[h]===id||h===id))return;
   try{history.replaceState(history.state,'',location.pathname+location.search+'#'+CANON[id])}catch(_){}}
 document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('.yrs a.yb[href]');if(!a||!location.hash)return;
   const t=document.querySelector('input[name=tab]:checked');if(t&&CANON[t.id])a.setAttribute('href',a.getAttribute('href').split('#')[0]+'#'+CANON[t.id])},true);
 function fromHash(){let h='';try{h=decodeURIComponent(location.hash.slice(1)).trim().toLowerCase()}catch(_){}if(!h)return null;h=h.split('/')[0];
   const id=SLUG[h]||(/^tab-[a-z]{2}$/.test(h)?h:null);return id&&has(id)&&grpOf(id)?id:null}
 const tabs=()=>[...nav.querySelectorAll('[role=tab]')];
 document.querySelectorAll('input.tabr,input.tgr').forEach(i=>{i.tabIndex=-1;i.setAttribute('aria-hidden','true')});
 function aria(){const rows=[nav.querySelector('nav.tabs'),nav.querySelector('.tsub')];
   rows.forEach(row=>{if(!row)return;const L=[...row.querySelectorAll('label')];L.forEach(l=>{const on=!!document.getElementById(l.htmlFor)?.checked;l.setAttribute('aria-selected',on);l.tabIndex=on?0:-1})})}
 function subFit(){const row=nav.querySelector('.tsub');if(!row)return;['--tsp','--tsl','--tsg','--tsv'].forEach(k=>row.style.removeProperty(k));row.classList.remove('tfl');
   // level 2 tabs = the H2H/Median toggle across the content width (2026-11-05): equal segments when the widest label plus its
   // padding fits an equal share; otherwise each segment follows its label (.tfl) and the row is still filled
   const L=[...row.querySelectorAll('label')].filter(l=>l.offsetParent);if(!L.length)return;
   {const g=nav.querySelector('nav.tabs label');if(g){const gh=g.getBoundingClientRect().height,rh=row.getBoundingClientRect().height,pv=parseFloat(getComputedStyle(L[0]).paddingTop);if(Math.abs(gh-rh)>.001){let v=Math.max(0,pv+(gh-rh)/2);row.style.setProperty('--tsv',v+'px');for(let i=0;i<6&&row.getBoundingClientRect().height>gh+.001;i++){v-=1/128;row.style.setProperty('--tsv',v+'px')}}}}
       const rs=getComputedStyle(row),inner=row.clientWidth-parseFloat(rs.paddingLeft)-parseFloat(rs.paddingRight),gap=parseFloat(rs.columnGap)||0,
     p0=parseFloat(getComputedStyle(L[0]).paddingLeft),R=document.createRange(),tw=L.map(l=>{R.selectNodeContents(l);return R.getBoundingClientRect().width});
   if(Math.max(...tw)+2*p0>(inner-gap*(L.length-1))/L.length)row.classList.add('tfl');
   // then the one-line fit rule (DESIGN.md §5), only if still needed: padding to 6px, the gap to 5px, padding to 4px
   const over=()=>row.scrollWidth>row.clientWidth+.5;let p=p0;
   while(over()&&p>6){p-=1;row.style.setProperty('--tsp',p+'px')}
   let g=gap;while(over()&&g>5){g-=1;row.style.setProperty('--tsg',g+'px')}
   while(over()&&p>4){p-=1;row.style.setProperty('--tsp',p+'px')}}
 function sync(){const t=document.querySelector('input[name=tab]:checked'),g=(t&&grpOf(t.id))||'gd',r=document.getElementById('grp-'+g);
   if(r&&!r.checked)r.checked=true;aria();subFit();rp();if(t)keep(t.id)}
 // rp (2026-11-06): repaint the whole level-2 row after a tab/group change. iOS Safari left the old pill's bottom pixel row
 // (Standings, after a refresh) unpainted beside the new, narrower pill until a scroll; a one-frame layer forces a full repaint.
 function rp(){const s=document.querySelector('.tnav .tsub');if(!s)return;s.style.transform='translateZ(0)';requestAnimationFrame(()=>requestAnimationFrame(()=>{s.style.transform=''}))}
 function pick(id){const t=id&&document.getElementById(id);if(!t)return;if(!t.checked){t.checked=true;t.dispatchEvent(new Event('change',{bubbles:true}))}sync()}
 document.addEventListener('change',e=>{const t=e.target;if(!t||t.type!=='radio')return;
   if(t.name==='tgrp'){const g=t.id.slice(4),cur=document.querySelector('input[name=tab]:checked');if(!cur||grpOf(cur.id)!==g)pick(first(g));else sync()}
   else if(t.name==='tab')sync()});
 nav.addEventListener('keydown',e=>{const l=e.target.closest&&e.target.closest('[role=tab]');if(!l)return;const row=[...l.parentElement.querySelectorAll('[role=tab]')].filter(x=>x.offsetParent);
   let i=row.indexOf(l),j=i;if(e.key==='ArrowRight')j=(i+1)%row.length;else if(e.key==='ArrowLeft')j=(i-1+row.length)%row.length;else if(e.key==='Home')j=0;else if(e.key==='End')j=row.length-1;
   else if(e.key==='Enter'||e.key===' '){e.preventDefault();l.click();requestAnimationFrame(()=>{const n=nav.querySelector('label[for="'+l.htmlFor+'"]');n&&n.focus()});return}else return;
   e.preventDefault();row[j].click();requestAnimationFrame(()=>{const sel=[...row[j].parentElement.querySelectorAll('[role=tab][aria-selected=true]')][0]||row[j];sel.focus()})});
 addEventListener('hashchange',()=>{const id=fromHash();if(id)pick(id)});
 addEventListener('resize',()=>requestAnimationFrame(subFit));document.fonts&&document.fonts.ready.then(subFit);
 try{history.scrollRestoration='manual'}catch(_){}
 pick(fromHash()||first('gd'));sync();live=true})();
// 2026-11-06 (Nicklaus) lineup fit, Matchups + Playoffs lineups: never "…". Per lineup (.lus-a / .lus-o): one name size (--lnf, floor 12px)
// and one game-line size (--lgf, floor 11px), set on the lineup container. A game line that does not fit at 11px writes its time short
// ("9:30a", "Sat 8:20p"). A name that does not fit at 12px gets 11px on its own row, then letter-spacing down to -.02em, then its injury tag
// and then its team logo move to the end of the game line (kept only if the game line still fits), then a fixed approved abbreviation (LUA).
// A name with no approved form stays at 11px / -.02em and is reported (window.__luReport, needsForm). BN is a line in the position tile.
const LUA={'Croskey-Merritt':'Croskey-M.','McCaffrey':'McCaff.','Rodriguez':'Rodrig.','Monangai':'Monang.','Henderson':'Henders.'};  // approved by Nicklaus, 2026-11-06
const LUR=[];  // what the last pass did, for QA (window.__luReport)
const luOver=e=>e.scrollWidth>e.clientWidth+.5;
function luShort(g){const w=g.querySelector('.gwhen');if(!w||w.dataset.full)return false;const f=w.textContent,ab=f.replace(/(\d)(?::(\d\d))?\s?([AP])M/,(x,h,mm,ap)=>h+(mm?':'+mm:'')+ap.toLowerCase());
  if(ab===f)return false;w.dataset.full=f;w.dataset.ab=ab;w.textContent=ab;return true}
function luShared(C,prop,els,base,floor){  // largest size (0.25px steps) at which every element fits, floor..base; returns it
  const est=Math.min(base,...els.map(e=>luOver(e)?base*e.clientWidth/e.scrollWidth:base));let k=Math.min(base,Math.max(floor,Math.floor(est*4)/4));
  if(k<base)C.style.setProperty(prop,k+'px');
  while(k>floor&&els.some(luOver)){k=Math.max(floor,k-.25);C.style.setProperty(prop,k+'px')}
  return k}
function luFit(){LUR.length=0;
  document.querySelectorAll('.lus-a,.lus-o').forEach(C=>{if(!C.offsetParent)return;
  const cells=[...C.querySelectorAll('.cr.lu:not(.psr) .cnm')].filter(c=>c.offsetParent&&c.querySelector('b>span'));if(!cells.length)return;
  C.style.removeProperty('--lnf');C.style.removeProperty('--lgf');
  for(const c of cells){const s=c.querySelector('b>span'),b=c.querySelector('b'),sm=c.querySelector('small');
    if(s.dataset.full){s.textContent=s.dataset.full;delete s.dataset.full}
    s.style.removeProperty('font-size');s.style.removeProperty('letter-spacing');
    if(sm)[...sm.querySelectorAll(':scope>.lmv')].sort((x,y)=>(x.classList.contains('inj')?0:1)-(y.classList.contains('inj')?0:1)).forEach(x=>{x.classList.remove('lmv');if(x.classList.contains('inj'))b.appendChild(x);else b.insertBefore(x,b.querySelector(':scope>.inj'))});
    const w=c.querySelector('.gwhen');if(w&&w.dataset.full){if(w.textContent===w.dataset.ab)w.textContent=w.dataset.full;delete w.dataset.full;delete w.dataset.ab}}
  const S=cells.map(c=>c.querySelector('b>span')),G=cells.map(c=>c.querySelector('.gp')).filter(g=>g&&g.offsetParent);
  // A. names: one shared size (12px floor)
  const nb=parseFloat(getComputedStyle(cells[0].querySelector('b')).fontSize),k=luShared(C,'--lnf',S,nb,12);
  // B. game lines: one shared size (11px floor), then short times
  const gb=parseFloat(getComputedStyle(cells[0].querySelector('small')).fontSize),gk=G.length?luShared(C,'--lgf',G,gb,11):gb;
  for(const g of G){if(!luOver(g))continue;const r={lu:C.className,game:g.textContent.trim(),short:null};if(luShort(g))r.short=g.querySelector('.gwhen').textContent;r.over=luOver(g);LUR.push(r)}
  // C. names that do not fit at the shared size: 11px, letter-spacing, move tags (only if the game line still fits), abbreviate
  for(const s of S.filter(luOver)){const c=s.closest('.cnm'),sm=c.querySelector('small'),g=c.querySelector('.gp'),r={lu:C.className,name:s.textContent.trim(),size:11,ls:0,moved:[],abbr:null,needsForm:false};
    s.style.fontSize='11px';
    const ls=()=>{s.style.removeProperty('letter-spacing');r.ls=0;if(!luOver(s))return;const d=(s.clientWidth-s.scrollWidth)/s.textContent.length;s.style.letterSpacing=Math.max(-0.22,Math.floor(d*100)/100)+'px';r.ls=parseFloat(s.style.letterSpacing)};
    ls();
    for(const [sel,lab] of [['b>.inj','injury'],['b>.nfl.tm','logo']]){if(!luOver(s))break;const t=c.querySelector(sel);if(!t||!sm)continue;
      t.classList.add('lmv');sm.appendChild(t);let sh=false;if(g&&luOver(g))sh=luShort(g);
      if(g&&luOver(g)){t.classList.remove('lmv');const b=c.querySelector('b');if(lab==='injury')b.appendChild(t);else b.insertBefore(t,b.querySelector(':scope>.inj'));if(sh){const w=g.querySelector('.gwhen');w.textContent=w.dataset.full;delete w.dataset.full;delete w.dataset.ab}r.tried=(r.tried||[]).concat(lab)}
      else r.moved.push(lab);ls()}
    if(luOver(s)){const full=s.textContent.trim(),t=LUA[full];if(t){s.dataset.full=full;s.textContent=t;r.abbr=t;ls()}else r.needsForm=true}
    r.over=luOver(s);LUR.push(r)}
  LUR.push({lu:C.className,nameSize:parseFloat(C.style.getPropertyValue('--lnf'))||nb,base:nb,gameSize:parseFloat(C.style.getPropertyValue('--lgf'))||gb,gbase:gb,rows:cells.length,
    gameOver:G.filter(luOver).map(g=>g.textContent.trim())})})
  window.__luReport=LUR.slice()}
window.luFit=luFit;
if(!FL())luFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(luFit);addEventListener('resize',()=>requestAnimationFrame(luFit));document.addEventListener('change',()=>requestAnimationFrame(luFit));document.addEventListener('panebuilt',()=>requestAnimationFrame(luFit));
// Remaining schedule (Stats matrix and Team Hub, 2026-11-10): the opponents' points-for rank chips are sized by the rank-tile
// sizer at 16px (digits ink-centred, 3.5px from the frame, one width for one or two digits) where they sit beside the picture with
// the average under them. In the one-line desktop cell (Stats, >=1100px) the chip sits beside the average, so its height is that
// figure's cap height (Barlow Condensed .7em), like the Standings stat-line tiles.
(function(){function sosFit(){if(!window.inkBatch)return;const c=[...document.querySelectorAll('.sosm .sox .ch')].filter(t=>t.offsetParent);if(!c.length)return;
  const one=innerWidth>=1100,H=new Map();c.forEach(t=>{let h=16;if(one&&t.closest('.sos1:not(.tqgrid)')){const a=t.parentNode.querySelector('.soa');if(a)h=Math.round(parseFloat(getComputedStyle(a).fontSize)*70)/100}H.set(t,h)});
  inkBatch(c.map(t=>[t,H.get(t)]))}
let q=0;function sch(){if(q)return;q=requestAnimationFrame(()=>{q=0;sosFit()})}
if(!FL())sosFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(sosFit);addEventListener('resize',sch);document.addEventListener('change',sch);document.addEventListener('panebuilt',sch);window.sosFit=sosFit})();
</script>
