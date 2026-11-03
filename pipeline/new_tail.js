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
    const st={gold:['rgba(244,196,81,.16)','#f4c451','rgba(244,196,81,.5)'],g:['var(--win-bg)','var(--win)',''],b:['var(--loss-bg)','var(--loss)',''],last:['var(--loss-bg)','var(--loss)','rgba(255,93,115,.6)'],n:['var(--hair)','var(--steel)','']}[k];
    return `<rect${mode==='opp'?' opacity=".55"':''} x="${cx-TW/2}" y="${cy-TH/2}" width="${TW}" height="${TH}" rx="3" fill="${st[0]}"${st[2]?` stroke="${st[2]}" stroke-width="1"`:''}/>`+
           `<text x="${cx}" y="${bl(cy,9.5)}" text-anchor="middle" font-size="9.5" font-weight="500" fill="${st[1]}"${mode==='opp'?' opacity=".9"':''}>${r}</text>`};
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
      s+=`<rect x="${x+.5}" y="${top+.5}" width="${bw-1}" height="${base-top-1}" rx="1.5" fill="none" stroke="var(--hair)" stroke-dasharray="2 2"/>`+
         `<text x="${cx}" y="${bl(WY,12)}" text-anchor="middle" font-size="12" fill="var(--dim)">${wk}</text>`;}
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
    const sub=med?`<div class="chl">Breakdown</div><div class="cw">H2H <b>${w}-${l}</b></div><div class="cw">Top-5 <b>${mw}-${G-mw}</b></div>`
                 :`<div class="chl">Could have</div><div class="cw">Won <b>${CH[t][0]}</b></div><div class="cw">Lost <b>${CH[t][1]}</b></div>`;
    const P=med?PM:PH,dl=P.indexOf(t)-i,a=(med?POS.M:POS.H)[t];
    const tri=p=>`<svg class="tri" viewBox="0 0 8 7" aria-hidden="true"><path d="${p}"/></svg>`;
    const mv=dl>0?`<span class="mv up">${tri('M4 0L8 7H0Z')}${dl}</span>`:dl<0?`<span class="mv dn">${tri('M0 0H8L4 7Z')}${-dl}</span>`:`<span class="mv eq">–</span>`;
    const r=WK[t].map(g=>g[2]>g[3]?'W':'L'),lastR=r[r.length-1];let n=0;for(let k=r.length-1;k>=0&&r[k]===lastR;k--)n++;
    const tc=i<BYN?'tier-bye':i<PO?'tier-po':'tier-out';
    const th=i===0?['tier-bye','Bye',`Seeds 1–${BYN}`,BYN-1]:i===BYN?['tier-po','Playoffs',`Seeds ${BYN+1}–${PO}`,PO-1]:i===PO?['tier-out','Chasing',`Seeds ${PO+1}–${NT}`,-1]:null;
    const tierHtml=th?`${i?'</section>':''}<section class="tcard ${th[0]}" aria-label="${th[1]}"><div class="tier ${th[0]}"><b>${th[1]}</b><span>${th[2]}</span>${th[3]>=0?`<em>Line ${wl(o[th[3]]).join('-')}</em>`:''}</div>`:'';
    const op=OPEN.has(t);
    const strip=WK[t].map(g=>{const won=g[2]>g[3];return `<div class="gm"><div class="h"><span>Wk ${g[0]}</span><span class="res ${won?'w':'l'}"><span class="ct">${won?'W':'L'}</span></span></div><div class="sc">${g[2].toFixed(2)}${chip(g[4])}</div><div class="vs">vs ${esc(fn(g[1]))}</div><div class="os">${g[3].toFixed(2)}${chip(g[5])}</div></div>`}).join('')
      +FUT[t].map(g=>`<div class="gm fut"><div class="h"><span>Wk ${g[0]}</span></div><div class="up">Upcoming</div><div class="vs">vs ${esc(fn(g[1]))}</div></div>`).join('');
    return tierHtml+`<div class="r ${tc}${AVR[t]?" hav":""}${i>=PO?' out':''}${op?' open':''}" data-t="${esc(t)}" tabindex="0" role="button" aria-expanded="${op}">
      <div class="rk">${i+1}</div>
      ${AVR[t]?`<i class="av rav av-${AVR[t]}" aria-hidden="true"></i>`:""}<div class="nm"><span class="tn">${esc(t)} ${mv}</span>${typeof FAAB!=='undefined'&&FAAB[t]!=null?`<label for="tab-wr" class="fab" title="FAAB left: $${FAAB[t]} of $${FAABB} (opens The Wire)"><b>$${FAAB[t]}</b><small>FAAB</small></label>`:''}</div>
      <span class="hl">${NIK[t]?`<em class="mgr">${esc(NIK[t])}</em>`:""}</span>
      <div class="sb s-pf"><div class="stx"><em class="lb">PF</em><span class="pf">${d[3].toFixed(2)}</span>${chip(d[4])} <i class="pw">· <b class="pwv">${d[5].toFixed(1)}</b>/wk <b class="psd" title="Weekly spread: standard deviation of the team's weekly scores">±${SDV(t).toFixed(0)}</b></i></div>${seg(d[4])}</div>
      <div class="sb s-pa"><div class="stx"><em class="lb">PA</em><span class="v">${d[6].toFixed(2)}</span>${chip(d[7])} <i class="pw">· <b class="pwv">${d[8].toFixed(1)}</b>/wk</i></div>${seg(d[7])}</div>
      <div class="sb s-lu"><div class="stx"><em class="lb">Tot Eff</em><span class="v">${EF[t][0].toFixed(0)}%</span>${chip(rankEf(t),tiedEf(t))} <i class="pw">· <b class="lw">${EF[t][1].toFixed(1)}</b>/wk</i></div>${seg(rankEf(t))}</div>
      <div class="sb s-sk"><div class="stx spl dps"><span class="dpb dpd"><span class="dph"><em class="lb dpl">Dropped pts</em><i class="pw pu">/wk</i></span><span class="dpg">${['QB','RB','WR','TE'].map((k,i)=>LPOS.includes(k)?`<span class="dpc p-${k.toLowerCase()}"><b>${k}</b><span class="${DP[t][i]>=0.05?'':'z'}">${DP[t][i].toFixed(1)}</span>${chip(dpR(i,t),dpT(i,t))}</span>`:'').join('')}</span></span><span class="dpb dso"><span class="dph"><em class="lb dpl">Season sim</em></span><span class="dpg sog">${[['Finish',SO[t][0].toFixed(1)],['#1',pctS(SO[t][1])],['Bye',pctS(SO[t][2])],['Playoffs',pctS(SO[t][3])]].map(([k,v],i)=>`<span class="dpc so s${i}"><b>${k}</b><span class="${i&&v==='0%'?'z':''}">${i?v:`<span class="sof ${tone(Math.round(SO[t][0]))}">${v}</span>`}</span></span>`).join('')}</span></span></div></div>
      <div class="st s2"><span><em class="lb">Opp<i class="lrk"> rk</i></em><span class="v">${d[9].toFixed(1)}</span>${chip(rankOf(d[9],9,true),tied(d[9],9))}</span><span><em class="lb">All-play</em><span class="v">${d[10]}-${d[11]}</span>${chip(rankOf(d[10],10,false),tied(d[10],10))}</span><span><em class="lb">Luck</em><span class="v">${luck(d[12])}<i class="lku" title="Expected wins (xW): all-play win rate × games played. Luck = actual wins − xW">${(d[10]/(d[10]+d[11])*(d[0]+d[1])).toFixed(2)} xW</i></span>${chip(rankOf(d[12],12,false),tied(d[12],12))}</span></div>
      <div class="side"><div class="rr${(String(rw0)+String(rl0)).length>2?" rr4":""}"><b>${rw0}-${rl0}</b></div><span class="l5d" aria-label="Last 5 results">${WK[t].slice(-5).map(g=>`<i class="${g[2]>g[3]?'w':'l'}"></i>`).join('')}</span><div class="skr"><span class="sk ${lastR==='W'?'w':'l'}"><span class="ct">${lastR}${n}</span></span></div>${gbH}<div class="subw">${sub}</div></div>
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
  const o=med?M:H,N=o.length,PN=typeof PO!=='undefined'?PO:6,BY=typeof BYN!=='undefined'?BYN:2;
  const wl=x=>{const e=T[x];return med?[e[0]+e[2],e[1]+G-e[2]]:[e[0],e[1]]};
  const sd=t=>{const a=WK[t].map(g=>g[2]),m=a.reduce((x,y)=>x+y,0)/a.length;return Math.sqrt(a.reduce((x,y)=>x+(y-m)*(y-m),0)/a.length)};
  const pc=x=>x<=0?'0%':x>=100?'100%':x<1?'<1%':x>99?'>99%':Math.round(x)+'%';
  const so=t=>typeof SO!=='undefined'&&SO[t]?SO[t]:null;
  const av=t=>typeof AVR!=='undefined'&&AVR[t]?`<i class="av dav av-${AVR[t]}" aria-hidden="true"></i>`:'';
  const tier=i=>i<BY?'bye':i<PN?'po':'out';
  const rows=o.map((t,i)=>{const d=T[t],[w,l]=wl(t),r=WK[t].map(g=>g[2]>g[3]?'W':'L'),lr=r[r.length-1];let n=0;for(let k=r.length-1;k>=0&&r[k]===lr;k--)n++;
    return {t,i,w,l,pf:d[3],pfr:d[4],pw:d[5],sd:sd(t),pa:d[6],par:d[7],paw:d[8],apw:d[10],apl:d[11],apr:rankOf(d[10],10,false),xw:d[10]/Math.max(1,d[10]+d[11])*G,lk:d[12],ef:EF[t][0],st:lr+n,l5:WK[t].slice(-5).map(g=>g[2]>g[3]),s:so(t)}});
  const cols=[['seed','',r=>r.i],['team','Team',r=>r.t],['wl','W-L',r=>r.w-r.l/100],['st','Strk',null],['l5','Last 5',null],['pf','PF',r=>r.pf],['pw','Per wk ±',r=>r.pw],
    ['pa','PA',r=>r.pa],['paw','PA/wk',r=>r.paw],['ap','All-play',r=>r.apw],['xw','xWins',r=>r.xw],['lk','Luck',r=>r.lk],['ef','Tot eff',r=>r.ef],['fin','Proj finish',r=>r.s?-r.s[0]:0],['top','#1',r=>r.s?r.s[1]:0],['bye','Bye',r=>r.s?r.s[2]:0],['po','Playoffs',r=>r.s?r.s[3]:0]];
  const key=box.dataset.k||'seed',dir=+(box.dataset.d||1);
  const f=cols.find(c=>c[0]===key)[2];
  const sorted=key==='seed'?rows:[...rows].sort((a,b)=>dir*((key==='team'?a.t.localeCompare(b.t):f(b)-f(a))));
  const tcls={bye:'Bye · seeds 1–'+BY,po:'Playoffs · seeds '+(BY+1)+'–'+PN,out:'Chasing · seeds '+(PN+1)+'–'+N};
  let h='<table class="dtt"><thead><tr>'+cols.map(c=>`<th data-k="${c[0]}"${c[2]?' class="srt'+(c[0]===key?' on':'')+(c[0]==='seed'?' rst'+(key!=='seed'?' act':''):'')+'"':''}${c[0]==='seed'?' title="Reset to standings order"':''}>${c[0]==='seed'?'<svg class="rsi" viewBox="0 0 16 16" aria-label="Reset sort"><path d="M3.2 8a4.8 4.8 0 1 0 1.5-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M2.6 1.9v3.4H6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>':c[1]}</th>`).join('')+'</tr></thead><tbody>',lt='';
  for(const r of sorted){
    if(key==='seed'&&tier(r.i)!==lt){lt=tier(r.i);h+=`<tr class="dtb ${lt}"><td colspan="${cols.length}">${tcls[lt]}</td></tr>`}
    h+=`<tr class="dtr ${tier(r.i)}" data-t="${esc(r.t)}"><td class="dsd">${r.i+1}</td><td class="dtm"><span>${av(r.t)}${esc(r.t)}</span></td>`+
       `<td><b>${r.w}-${r.l}</b></td><td><i class="dsk ${r.st[0]==='W'?'w':'l'}">${r.st}</i></td><td><span class="dl5">${r.l5.map(x=>`<i class="${x?'w':'l'}"></i>`).join('')}</span></td>`+
       `<td>${r.pf.toFixed(1)}${chip(r.pfr)}</td><td><b>${r.pw.toFixed(1)}</b><small>±${r.sd.toFixed(0)}</small></td><td>${r.pa.toFixed(1)}${chip(r.par)}</td><td><b>${r.paw.toFixed(1)}</b></td>`+
       `<td>${r.apw}-${r.apl}${chip(r.apr)}</td><td><b>${r.xw.toFixed(2)}</b></td><td class="${r.lk>=0.05?'up':r.lk<=-0.05?'dn':''}">${(r.lk>=0?'+':'−')+Math.abs(r.lk).toFixed(2)}</td><td>${r.ef.toFixed(0)}%</td>`+
       (r.s?`<td>${rkt(r.s[0],1)}</td><td class="c1">${pc(r.s[1])}</td><td class="c2">${pc(r.s[2])}</td><td class="c3">${pc(r.s[3])}</td>`:'<td></td><td></td><td></td><td></td>')+'</tr>'}
  box.innerHTML=h+'</tbody></table>';
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
draw(false);dtab(false);
if(typeof AVR!=='undefined')document.querySelectorAll('.pav[data-avt]').forEach(e=>{const r=AVR[e.dataset.avt];if(r)e.classList.add('av','av-'+r);else e.classList.add('nl')});
function pfit(){document.querySelectorAll('.pr .pav.av+.psn').forEach(el=>{if(!el.offsetParent)return;el.style.fontSize='';let f=parseFloat(getComputedStyle(el).fontSize);while((el.scrollHeight>el.clientHeight+1||el.scrollWidth>el.clientWidth+1)&&f>9){f-=0.5;el.style.fontSize=f+'px'}})}
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
    const fit=n=>{let g=f0;const bad=()=>ov()||e.getBoundingClientRect().height>n*1.12*g+1||(n>2&&n*1.12*g>52);e.style.fontSize=g+'px';while(bad()&&g>10){g-=.5;e.style.fontSize=g+'px'}return g};
    f=fit(2);if(f<15){const g=fit(3);if(g<=f)e.style.fontSize=(f=fit(2))+'px'}}});if(typeof ravFit==='function')ravFit();mvAl()}
// tabs: one shared font size, shrunk just enough that the longest label keeps at least 8px from its frame on each side
function tabFit(){const L=[...document.querySelectorAll('nav.tabs label')].filter(l=>l.offsetParent);if(!L.length)return;L.forEach(l=>l.style.fontSize='');
let k=1;L.forEach(l=>{const rg=document.createRange();rg.selectNodeContents(l);const tw=rg.getBoundingClientRect().width;const ls=parseFloat(getComputedStyle(l).letterSpacing)||0;const room=l.getBoundingClientRect().width-2-16;const w=tw-ls;if(w>room)k=Math.min(k,room/w)});
if(k<1){const f=parseFloat(getComputedStyle(L[0]).fontSize)*k;L.forEach(l=>l.style.fontSize=(Math.floor(f*4)/4)+'px')}}
tabFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(tabFit);document.fonts&&document.fonts.addEventListener('loadingdone',()=>{tabFit();tnFit()});addEventListener('resize',()=>requestAnimationFrame(tabFit));
// standings logo: top on the team name's cap line, bottom on the Hi/Lo/Avg baseline (measured from the glyphs, per row)
const _cv=document.createElement('canvas').getContext('2d');
function _ink(el,txt){const c=getComputedStyle(el);_cv.font=c.fontStyle+' '+c.fontWeight+' '+c.fontSize+' '+c.fontFamily;const m=_cv.measureText(txt);const rg=document.createRange();rg.selectNodeContents(el);const r=rg.getClientRects()[0]||el.getBoundingClientRect();
  const base=r.top+(r.height-(m.fontBoundingBoxAscent+m.fontBoundingBoxDescent))/2+m.fontBoundingBoxAscent;return {cap:base-_cv.measureText('H').actualBoundingBoxAscent,base}}
function ravFit(){let mx=0;const bd=document.querySelector('.board');document.querySelectorAll('.board .r').forEach(r=>{const a=r.querySelector('.rav.av'),tn=r.querySelector('.tn'),lb=r.querySelector('.hl .lb');if(!a||!tn||!lb||!r.offsetParent)return;
  a.style.transform='';const z=a.currentCSSZoom||1;const top=_ink(tn,'H').cap,bot=_ink(lb,'H').base;const H=Math.max(12,bot-top)/z;mx=Math.max(mx,H);a.style.flex='0 0 '+H.toFixed(2)+'px';
  a.style.width=a.style.height=H.toFixed(2)+'px';const at=a.getBoundingClientRect().top;a.style.transform='translateY('+((top-at)/z).toFixed(2)+'px)'});if(bd&&mx)document.querySelectorAll('.board').forEach(b=>b.style.setProperty('--ravc',mx.toFixed(2)+'px'))}
// standings stat lines: one shared text scale (1 = 15px), lowered in small steps until no line is clipped
function sbFit(){document.querySelectorAll('.board').forEach(bd=>{if(!bd.offsetParent)return;bd.classList.add('sbm');bd.style.setProperty('--sbs','1');const L=[...bd.querySelectorAll('.sb .stx:not(.spl)')].filter(x=>x.offsetParent);let k=1;
  bd.style.removeProperty('--stw2');while(k>.68&&L.some(x=>x.scrollWidth>x.clientWidth+.5)){k-=.02;bd.style.setProperty('--sbs',k.toFixed(2))}
  // then the text column shrinks to the longest line, so the dots sit just after the text (all lines aligned)
  const mw=Math.max(0,...L.filter(x=>x.closest('.sb')).map(x=>{const rg=document.createRange();rg.selectNodeContents(x);const a=rg.getBoundingClientRect(),b=x.getBoundingClientRect();return a.right-b.left}));
  if(mw)bd.style.setProperty('--stw2',Math.ceil(mw+2)+'px');bd.classList.remove('sbm')});if(typeof tileFit==='function'){tileFit();
  // the rank tiles resize with the text: if a line now overflows, step the scale down again (a few passes at most)
  for(let n=0;n<4;n++){let again=false;document.querySelectorAll('.board').forEach(bd=>{if(!bd.offsetParent)return;const L=[...bd.querySelectorAll('.sb .stx:not(.spl)')].filter(x=>x.offsetParent);
    if(L.some(x=>x.scrollWidth>x.clientWidth+.5)){const k=parseFloat(bd.style.getPropertyValue('--sbs')||'1')-.02;if(k>.66){bd.style.setProperty('--sbs',k.toFixed(2));again=true}}});if(!again)break;tileFit()}}}
// Opp rk · All-play · Luck line: its own scale (down to 86%); if it still does not fit, Luck wraps to a second line
function s2Fit(){document.querySelectorAll('.board').forEach(bd=>{const L=[...bd.querySelectorAll('.r>.st.s2')].filter(x=>x.offsetParent);bd.style.setProperty('--s2s','1');L.forEach(x=>x.classList.remove('wrp'));let k=1;
  const over=()=>L.some(x=>x.scrollWidth>x.clientWidth+.5);while(k>.81&&over()){k-=.02;bd.style.setProperty('--s2s',k.toFixed(2))}
  if(over()){bd.style.setProperty('--s2s','1');L.forEach(x=>x.classList.add('wrp'))}});if(typeof tileFit==='function')tileFit()}
s2Fit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(s2Fit);addEventListener('resize',()=>requestAnimationFrame(s2Fit));document.addEventListener('change',()=>requestAnimationFrame(s2Fit));document.fonts&&document.fonts.addEventListener('loadingdone',s2Fit);
// dropdown labels (Compare team pickers etc.): shrink a long name to fit instead of an ellipsis
function ddFit(){document.querySelectorAll('.dd summary .sv').forEach(v=>{if(!v.offsetParent)return;v.style.fontSize='';let f=parseFloat(getComputedStyle(v).fontSize);while(v.scrollWidth>v.clientWidth+.5&&f>9){f-=.5;v.style.fontSize=f+'px'}})}
ddFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(ddFit);addEventListener('resize',()=>requestAnimationFrame(ddFit));document.addEventListener('change',()=>requestAnimationFrame(ddFit));document.fonts&&document.fonts.addEventListener('loadingdone',ddFit);
sbFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(sbFit);addEventListener('resize',()=>requestAnimationFrame(sbFit));document.addEventListener('change',()=>requestAnimationFrame(sbFit));document.fonts&&document.fonts.addEventListener('loadingdone',sbFit);
ravFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(ravFit);addEventListener('resize',()=>requestAnimationFrame(ravFit));document.addEventListener('change',()=>requestAnimationFrame(ravFit));document.fonts&&document.fonts.addEventListener('loadingdone',ravFit);
tnFit();(document.fonts&&document.fonts.ready||Promise.resolve()).then(tnFit);addEventListener('resize',()=>requestAnimationFrame(tnFit));document.addEventListener('change',()=>requestAnimationFrame(tnFit));
// rank tiles never taller than the figure they rank: tile top = the figure's digit top, tile bottom = its baseline
(function(){
const FM={};
function fm(cs){const k=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;if(FM[k])return FM[k];const c=document.createElement('canvas').getContext('2d');c.font=k;const m=c.measureText('0123456789');return FM[k]={cap:m.actualBoundingBoxAscent,asc:m.fontBoundingBoxAscent,desc:m.fontBoundingBoxDescent}}
function txt(n){if(n.nodeType===3)return n;const w=document.createTreeWalker(n,NodeFilter.SHOW_TEXT,{acceptNode:x=>x.textContent.trim()&&!x.parentElement.closest('.lku')?1:3});let l=null,x;while(x=w.nextNode())l=x;return l}
function ref(t){let n=t.previousSibling;while(n&&n.nodeType===3&&!n.textContent.trim())n=n.previousSibling;
  if(n&&n.nodeType===1&&n.matches('.ch,.rkb,svg,.av,.pav,.pz,.nfl,.pba,img'))return null;
  if(!n){if(t.classList.contains('rkb'))return {own:true,el:t.parentElement};const ps=t.parentElement.previousElementSibling;if(ps&&!t.previousElementSibling){const tn=txt(ps);if(tn&&/[0-9]/.test(tn.textContent))return {tn,el:tn.parentElement}}return null}
  const tn=txt(n);if(!tn||!/[0-9A-Za-z%]/.test(tn.textContent))return null;return {tn,el:tn.parentElement}}
function fit(){
  for(const k in FM)delete FM[k];  // font metrics are re-read each run: a run before the web fonts load must not leave the fallback font's metrics cached
  const tiles=[...document.querySelectorAll('.ch,.rkb')].filter(t=>t.offsetParent&&!t.closest('.gm,.sxm,.lbr,.hmx,.tqgrid,.mx,.bym'));
  const jobs=[];
  for(const t of tiles)t.style.removeProperty('transform');  // clear old offsets first: a stale one makes a tile look off its line and it would be skipped for good
  for(const t of tiles){const r=ref(t);if(!r)continue;const cs=getComputedStyle(r.el),m=fm(cs),z=t.currentCSSZoom||1;
    if(!t.dataset.oh){const ct0=t.querySelector('.ct')||t;t.dataset.oh=t.getBoundingClientRect().height/z;t.dataset.of=parseFloat(getComputedStyle(ct0).fontSize)}
    let inline=false;
    if(r.tn){const g=document.createRange();g.selectNodeContents(r.tn);const rr=g.getBoundingClientRect(),tr=t.getBoundingClientRect();inline=tr.bottom>rr.top&&tr.top<rr.bottom}
    if(!inline)continue;const zz=r.el.currentCSSZoom||z;const pb=document.createElement('i');pb.style.cssText='display:inline-block;width:0;height:0;padding:0;margin:0;border:0;vertical-align:baseline';r.tn.after(pb);
    jobs.push({t,cap:m.cap,pb,zc:zz,z})}
  for(const j of jobs){const H=Math.floor(j.cap*4)/4;inkTile(j.t,H)}  // as tall as the figure beside it and never taller: tile height = its cap height (to 0.25px)
  for(const j of jobs)j.t.style.removeProperty('transform');  // measure from the untransformed spot, so a re-run never stacks offsets
  for(const j of jobs){j.mid=j.pb.getBoundingClientRect().bottom-j.cap*j.zc/2}  // read after sizing, so the line has settled: the figure's real baseline (a zero-size marker on it), not one estimated from font metrics: those are rounded differently by layout
  for(const j of jobs)j.pb.remove();
  for(const j of jobs){  // centre every tile on the figure's cap height (a flex row centres on the line box, which sits lower)
    const tr=j.t.getBoundingClientRect(),d=(j.mid-(tr.top+tr.bottom)/2)/j.z;if(Math.abs(d)>0.1)j.t.style.setProperty('transform','translateY('+d.toFixed(2)+'px)','important')}
}
// size one rank tile from the digits' ink: outer height H, the same gap from ink to edge on top and bottom, the same on
// left and right, never closer than 1.75px to the frame (the number shrinks to make room); width fixed for two digits so a column lines up
const INK=document.createElement('canvas').getContext('2d');
function inkTile(t,H){if(!(window.CSS&&CSS.supports('text-box','trim-both cap alphabetic')))return false;
  const txt=t.textContent.trim();if(!txt)return false;const cs=getComputedStyle(t.querySelector('.ct')||t),fam=cs.fontFamily,wt=cs.fontWeight;
  {const b=getComputedStyle(t);H-=(parseFloat(b.borderTopWidth)||0)+(parseFloat(b.borderBottomWidth)||0)}  // H is the outer height: a bordered (outlined) tile loses its border from it
  const P=Math.max(1.75,Math.min(3.5,(H-6)/2-1)),cap=H-2*P;  // gap from digit ink to frame: 1.75-3.5px, so the digits fill the tile
  INK.font=`${wt} 100px ${fam}`;const _d=INK.measureText('0123456789');const fs=Math.floor(cap/((_d.actualBoundingBoxAscent+_d.actualBoundingBoxDescent)/100)*4)/4;  // sized on the digits' ink (they can rise above the H cap), so the outer height never exceeds H
  INK.font=`${wt} ${fs}px ${fam}`;const m=INK.measureText(txt),m2=INK.measureText('88'),Hc=INK.measureText('H').actualBoundingBoxAscent;
  const m3=INK.measureText(t.dataset.ref||'88');const iw=m.actualBoundingBoxLeft+m.actualBoundingBoxRight,iw2=Math.max(m2.actualBoundingBoxLeft+m2.actualBoundingBoxRight,m3.actualBoundingBoxLeft+m3.actualBoundingBoxRight),W=Math.max(iw,iw2)+2*(P+0.5);
  const gl=m.actualBoundingBoxLeft*-1,gr=m.width-m.actualBoundingBoxRight,gt=Hc-m.actualBoundingBoxAscent,gb=-m.actualBoundingBoxDescent;
  const s=t.style,set=(k,v)=>s.setProperty(k,v,'important');
  set('display','inline-block');set('text-box','trim-both cap alphabetic');set('line-height','1');set('height','auto');set('min-height','0');set('min-width','0');set('width','auto');
  set('box-sizing','content-box');set('font-size',fs+'px');set('letter-spacing','0');set('font-variant-numeric','normal');set('font-feature-settings','normal');set('top','0');set('transform','none');set('vertical-align','baseline');
  set('padding',`${(P-gt).toFixed(2)}px ${((W-iw)/2-gr).toFixed(2)}px ${(P-gb).toFixed(2)}px ${((W-iw)/2-gl).toFixed(2)}px`);
  const ct=t.querySelector('.ct');if(ct){for(const [k,v] of [['font-size','inherit'],['line-height','1'],['display','inline'],['height','auto'],['letter-spacing','0'],['font-variant-numeric','normal'],['text-box','none']])ct.style.setProperty(k,v,'important')}
  {const z=t.currentCSSZoom||1,e=(H+((parseFloat(getComputedStyle(t).borderTopWidth)||0)+(parseFloat(getComputedStyle(t).borderBottomWidth)||0))-t.getBoundingClientRect().height/z)/2;  // outer height exactly H: split the rounding error between top and bottom (frames are inset shadows, inside H)
   if(Math.abs(e)>0.01)set('padding',`${(P-gt+e).toFixed(2)}px ${((W-iw)/2-gr).toFixed(2)}px ${(P-gb+e).toFixed(2)}px ${((W-iw)/2-gl).toFixed(2)}px`)}
  return true}
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
let q=0;function sched(){if(q)return;q=requestAnimationFrame(()=>{q=0;fit();finFit();document.querySelectorAll('.tqt[data-h]:not([data-ok])').forEach(t=>{if(inkTile(t,+t.dataset.h))t.dataset.ok=1});document.querySelectorAll('.trc .tro2 b').forEach(el=>{if(!el.offsetParent)return;el.style.fontSize='';let f=parseFloat(getComputedStyle(el).fontSize);while((el.scrollWidth>el.clientWidth+0.5||el.scrollHeight>el.clientHeight+0.5)&&f>10){f-=0.5;el.style.fontSize=f+'px'}})})}
window.tileFit=fit;window.finFit=finFit;window.inkTile=inkTile;sched();addEventListener('resize',sched);document.addEventListener('change',()=>setTimeout(sched,0));document.addEventListener('click',()=>setTimeout(sched,0));
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
  rows.forEach(r=>{const k=r.querySelector('.side .skr .sk'),b=r.querySelector('.side .rr b');if(!k||!window.inkTile)return;k.style.removeProperty('transform');
    const cs=getComputedStyle(b);C.font=cs.fontStyle+' '+cs.fontWeight+' 26px '+cs.fontFamily;window.inkTile(k,Math.floor(C.measureText('0123456789').actualBoundingBoxAscent*4)/4)});
  rows.forEach(r=>{const sb=r.querySelector('.side .subw');if(!sb||!sb.offsetParent)return;const lt=txt(sb,0);if(!lt)return;const z=sb.currentCSSZoom||1;
    const ab=r.querySelector('.side .skr')||r.querySelector('.side .l5d'),floor=ab.getBoundingClientRect().bottom+6*z,me=base(lt)-capOf(lt.parentElement,'HOPC');
    const lines=[...r.querySelectorAll(':scope>.st, :scope>.sb')].filter(e=>e.offsetParent&&!r.querySelector('.side').contains(e));let tgt=null;
    for(const L of lines){for(const el of L.querySelectorAll('.lb,em,b,span')){if(!el.offsetParent)continue;const t=txt(el,0);if(!t)continue;const top=base(t)-capOf(t.parentElement,'HOPC');if(top>=floor-0.5&&(tgt===null||top<tgt))tgt=top;break}}
    if(tgt===null)return;const m=parseFloat(getComputedStyle(sb).marginTop)||0;sb.style.setProperty('margin-top',(m+(tgt-me)/z).toFixed(2)+'px','important')});
  if(typeof tnFit==='function')tnFit()}
window.rrFit=rrFit;const go=()=>requestAnimationFrame(()=>requestAnimationFrame(rrFit));go();addEventListener('resize',go);document.addEventListener('change',go);document.addEventListener('click',go);
if(document.fonts){document.fonts.ready.then(go);document.fonts.addEventListener&&document.fonts.addEventListener('loadingdone',go)}})();
</script>
