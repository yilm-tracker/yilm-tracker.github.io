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
    const gbH=rf.length?`<div class="chl gbh">Games back</div>${rf.map(([k,lab])=>`<div class="cw">${lab} <b>${gbOf(k)}</b></div>`).join('')}`:'<div class="chl gbh lead">Leader</div>';
    const sub=med?`<div class="chl">Breakdown</div><div class="cw">H2H <b>${w}-${l}</b></div><div class="cw">Top-5 <b>${mw}-${G-mw}</b></div>`
                 :`<div class="chl">Could have</div><div class="cw">Won <b>${CH[t][0]}</b></div><div class="cw">Lost <b>${CH[t][1]}</b></div>`;
    const P=med?PM:PH,dl=P.indexOf(t)-i,a=(med?POS.M:POS.H)[t];
    const tri=p=>`<svg class="tri" viewBox="0 0 8 7" aria-hidden="true"><path d="${p}"/></svg>`;
    const mv=dl>0?`<span class="mv up">${tri('M4 0L8 7H0Z')}${dl}</span>`:dl<0?`<span class="mv dn">${tri('M0 0H8L4 7Z')}${-dl}</span>`:`<span class="mv eq">–</span>`;
    const r=WK[t].map(g=>g[2]>g[3]?'W':'L'),lastR=r[r.length-1];let n=0;for(let k=r.length-1;k>=0&&r[k]===lastR;k--)n++;
    const tc=i<BYN?'tier-bye':i<PO?'tier-po':'tier-out';
    const th=i===0?['tier-bye','Bye',`Seeds 1–${BYN}`,BYN-1]:i===BYN?['tier-po','Playoffs',`Seeds ${BYN+1}–${PO}`,PO-1]:i===PO?['tier-out','Chasing',`Seeds ${PO+1}–${NT}`,-1]:null;
    const tierHtml=th?`<div class="tier ${th[0]}"><b>${th[1]}</b><span>${th[2]}</span>${th[3]>=0?`<em>Line ${wl(o[th[3]]).join('-')}</em>`:''}</div>`:'';
    const op=OPEN.has(t);
    const strip=WK[t].map(g=>{const won=g[2]>g[3];return `<div class="gm"><div class="h"><span>Wk ${g[0]}</span><span class="res ${won?'w':'l'}"><span class="ct">${won?'W':'L'}</span></span></div><div class="sc">${g[2].toFixed(2)}${chip(g[4])}</div><div class="vs">vs ${esc(fn(g[1]))}</div><div class="os">${g[3].toFixed(2)}${chip(g[5])}</div></div>`}).join('')
      +FUT[t].map(g=>`<div class="gm fut"><div class="h"><span>Wk ${g[0]}</span></div><div class="up">Upcoming</div><div class="vs">vs ${esc(fn(g[1]))}</div></div>`).join('');
    return tierHtml+`<div class="r ${tc}${AVR[t]?" hav":""}${i>=PO?' out':''}${op?' open':''}" data-t="${esc(t)}" tabindex="0" role="button" aria-expanded="${op}">
      <div class="rk">${i+1}</div>
      ${AVR[t]?`<i class="av rav av-${AVR[t]}" aria-hidden="true"></i>`:""}<div class="nm"><span class="tn">${esc(t)}</span>${mv}</div>
      <span class="hl">${NIK[t]?`<em class="mgr">${esc(NIK[t])}</em> · `:""}<em class="lb">Hi</em>${rkt(Math.min(...a))}<em class="lb">Lo</em>${rkt(Math.max(...a))}<em class="lb">Avg</em>${rkt(a.reduce((x,y)=>x+y,0)/a.length,1)}</span>
      <div class="sb s-pf"><div class="stx"><em class="lb">PF</em><span class="pf">${d[3].toFixed(2)}</span>${chip(d[4])} <i class="pw">· ${d[5].toFixed(1)} <b class="psd" title="Weekly spread: standard deviation of the team's weekly scores">±${SDV(t).toFixed(0)}</b></i></div>${seg(d[4])}</div>
      <div class="sb s-pa"><div class="stx"><em class="lb">PA</em><span class="v">${d[6].toFixed(2)}</span>${chip(d[7])} <i class="pw">· ${d[8].toFixed(1)}/wk</i></div>${seg(d[7])}</div>
      <div class="sb s-lk"><div class="stx"><em class="lb">Luck</em><span class="v">${luck(d[12])}</span>${chip(rankOf(d[12],12,false),tied(d[12],12))} <i class="pw">· ${(d[10]/(d[10]+d[11])*G).toFixed(2)} xW</i></div><div class="trk div"><i class="${d[12]>=0?'g pos':'b neg'}" style="left:${d[12]>=0?'50%':pct(.5+d[12]/MAXLUCK/2)};width:${pct(Math.abs(d[12])/MAXLUCK/2)}"></i></div></div>
      <div class="sb s-lu"><div class="stx"><em class="lb">Tot Eff</em><span class="v">${EF[t][0].toFixed(0)}%</span>${chip(rankEf(t),tiedEf(t))} <i class="pw">· <b class="lw">${EF[t][1].toFixed(1)}</b>/wk</i></div>${seg(rankEf(t))}</div>
      <div class="sb s-sk"><div class="stx spl dps"><span class="dpb dpd"><span class="dph"><em class="lb dpl">Dropped pts</em><i class="pw pu">/wk</i></span><span class="dpg">${['QB','RB','WR','TE'].map((k,i)=>LPOS.includes(k)?`<span class="dpc p-${k.toLowerCase()}"><b>${k}</b><span class="${DP[t][i]>=0.05?'':'z'}">${DP[t][i].toFixed(1)}</span>${chip(dpR(i,t),dpT(i,t))}</span>`:'').join('')}</span></span><span class="dpb dso"><span class="dph"><em class="lb dpl">Season sim</em></span><span class="dpg sog">${[['Finish',SO[t][0].toFixed(1)],['#1',pctS(SO[t][1])],['Bye',pctS(SO[t][2])],['Playoffs',pctS(SO[t][3])]].map(([k,v],i)=>`<span class="dpc so s${i}"><b>${k}</b><span class="${i&&v==='0%'?'z':''}">${i?v:rkt(SO[t][0],1)}</span></span>`).join('')}</span></span></div></div>
      <div class="st s2"><span><em class="lb">Opp rk</em><span class="v">${d[9].toFixed(1)}</span>${chip(rankOf(d[9],9,true),tied(d[9],9))}</span><span><em class="lb">All-play</em><span class="v">${d[10]}-${d[11]}</span>${chip(rankOf(d[10],10,false),tied(d[10],10))}</span></div>
      <div class="side"><div class="rr${(String(rw0)+String(rl0)).length>2?" rr4":""}"><span class="sk ${lastR==='W'?'w':'l'}"><span class="ct">${lastR}${n}</span></span><b>${rw0}-${rl0}</b></div><span class="l5d" aria-label="Last 5 results">${WK[t].slice(-5).map(g=>`<i class="${g[2]>g[3]?'w':'l'}"></i>`).join('')}</span>${gbH}<div class="subw">${sub}</div></div>
      <div class="szw">${season(t)}</div>
      <div class="strip"${op?'':' hidden'}>${strip}</div></div>`}).join('');
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
list.addEventListener('click',e=>{if(e.target.closest('.strip'))return;const r=e.target.closest('.r');if(r)toggle(r)});
list.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('r')){e.preventDefault();toggle(e.target)}});
const bh=document.getElementById('bh'),bm=document.getElementById('bm');
function set(med){bh.setAttribute('aria-pressed',!med);bm.setAttribute('aria-pressed',med);draw(med);dtab(med)}
bh.onclick=()=>set(false);bm.onclick=()=>set(true);
draw(false);dtab(false);
if(typeof AVR!=='undefined')document.querySelectorAll('.pav[data-avt]').forEach(e=>{const r=AVR[e.dataset.avt];if(r)e.classList.add('av','av-'+r);else e.classList.add('nl')});
function pfit(){document.querySelectorAll('.pr .pav.av+.psn').forEach(el=>{if(!el.offsetParent)return;el.style.fontSize='';let f=parseFloat(getComputedStyle(el).fontSize);while((el.scrollHeight>el.clientHeight+1||el.scrollWidth>el.clientWidth+1)&&f>9){f-=0.5;el.style.fontSize=f+'px'}})}
pfit();document.addEventListener('change',()=>requestAnimationFrame(pfit));
// rank tiles never taller than the figure they rank: tile top = the figure's digit top, tile bottom = its baseline
(function(){
const FM={};
function fm(cs){const k=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;if(FM[k])return FM[k];const c=document.createElement('canvas').getContext('2d');c.font=k;const m=c.measureText('0123456789');return FM[k]={cap:m.actualBoundingBoxAscent,asc:m.fontBoundingBoxAscent,desc:m.fontBoundingBoxDescent}}
function txt(n){if(n.nodeType===3)return n;const w=document.createTreeWalker(n,NodeFilter.SHOW_TEXT,{acceptNode:x=>x.textContent.trim()?1:3});let l=null,x;while(x=w.nextNode())l=x;return l}
function ref(t){let n=t.previousSibling;while(n&&n.nodeType===3&&!n.textContent.trim())n=n.previousSibling;
  if(n&&n.nodeType===1&&n.matches('.ch,.rkb,svg,.av,.pav,.pz,.nfl,.pba,img'))return null;
  if(!n){if(t.classList.contains('rkb'))return {own:true,el:t.parentElement};const ps=t.parentElement.previousElementSibling;if(ps&&!t.previousElementSibling){const tn=txt(ps);if(tn&&/[0-9]/.test(tn.textContent))return {tn,el:tn.parentElement}}return null}
  const tn=txt(n);if(!tn||!/[0-9A-Za-z%]/.test(tn.textContent))return null;return {tn,el:tn.parentElement}}
function fit(){
  const tiles=[...document.querySelectorAll('.ch,.rkb')].filter(t=>t.offsetParent&&!t.closest('.gm,.sxm,.lbr,.hmx,.tqgrid,.mx,.bym'));
  const jobs=[];
  for(const t of tiles){const r=ref(t);if(!r)continue;const cs=getComputedStyle(r.el),m=fm(cs),z=t.currentCSSZoom||1;
    if(!t.dataset.oh){const ct0=t.querySelector('.ct')||t;t.dataset.oh=t.getBoundingClientRect().height/z;t.dataset.of=parseFloat(getComputedStyle(ct0).fontSize)}
    let mid=null,inline=false,zz=z;
    if(r.tn){const g=document.createRange();g.selectNodeContents(r.tn);const rr=g.getBoundingClientRect(),tr=t.getBoundingClientRect();zz=rr.height>0?rr.height/(m.asc+m.desc):z;const base=rr.top+m.asc*zz;mid=base-m.cap*z/2;inline=tr.bottom>rr.top&&tr.top<rr.bottom}
    if(!inline)continue;jobs.push({t,cap:m.cap,mid,inline,z:(r.tn&&mid!=null)?zz:z})}
  for(const j of jobs){const s=j.t.style,oh=+j.t.dataset.oh,of=+j.t.dataset.of,c=Math.round(((j.cap+Math.max(oh,j.cap))/2)*2)/2;
    s.setProperty('display','inline-flex','important');s.setProperty('align-items','center');s.setProperty('justify-content','center');
    s.setProperty('height',c+'px','important');s.setProperty('min-height','0','important');s.setProperty('padding-top','0','important');s.setProperty('padding-bottom','0','important');
    s.setProperty('line-height','1','important');s.setProperty('box-sizing','border-box','important');s.setProperty('transform','none','important');s.setProperty('top','0','important');
    s.setProperty('min-width',Math.round(c*1.45)+'px','important');s.setProperty('padding-left','3px','important');s.setProperty('padding-right','3px','important');s.setProperty('vertical-align','baseline','important');
    const ct=j.t.querySelector('.ct')||j.t,fs=Math.round(((of||c)+Math.min(11,j.cap*1.02))/2*2)/2;
    if(ct!==j.t){ct.style.setProperty('font-size',fs+'px','important');ct.style.setProperty('line-height','1','important');ct.style.setProperty('display','block','important');ct.style.setProperty('height','auto','important')}
    else s.setProperty('font-size',fs+'px','important')}
  const moves=[];
  for(const j of jobs){if(!j.inline||j.mid==null)continue;const tr=j.t.getBoundingClientRect();moves.push([j.t,(j.mid-(tr.top+tr.bottom)/2)/j.z])}
  for(const [t,d] of moves)if(Math.abs(d)>0.2)t.style.setProperty('transform','translateY('+d.toFixed(2)+'px)','important');
}
// sim Finish tile: equal space from the digits' ink to the tile edge on all four sides
function finFit(){if(!(window.CSS&&CSS.supports('text-box','trim-both cap alphabetic')))return;const P=5;
document.querySelectorAll('.dso .rkb').forEach(k=>{if(!k.offsetParent)return;const cs=getComputedStyle(k);const c=document.createElement('canvas').getContext('2d');c.font=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;
 const m=c.measureText(k.textContent),H=c.measureText('H').actualBoundingBoxAscent;const s=k.style;
 const gl=-m.actualBoundingBoxLeft,gr=m.width-m.actualBoundingBoxRight,gt=H-m.actualBoundingBoxAscent,gb=-m.actualBoundingBoxDescent;
 s.setProperty('letter-spacing','0','important');s.setProperty('font-variant-numeric','normal','important');s.setProperty('font-feature-settings','normal','important');s.setProperty('padding',`${(P-gt).toFixed(2)}px ${(P-gr).toFixed(2)}px ${(P-Math.min(gb,P)).toFixed(2)}px ${(P-gl).toFixed(2)}px`,'important')})}
let q=0;function sched(){if(q)return;q=requestAnimationFrame(()=>{q=0;fit();finFit()})}
window.tileFit=fit;window.finFit=finFit;sched();addEventListener('resize',sched);document.addEventListener('change',()=>setTimeout(sched,0));document.addEventListener('click',()=>setTimeout(sched,0));
if(document.fonts){document.fonts.ready.then(()=>{for(const k in FM)delete FM[k];sched()});document.fonts.addEventListener&&document.fonts.addEventListener('loadingdone',()=>{for(const k in FM)delete FM[k];sched()})}
})();
addEventListener('resize',()=>requestAnimationFrame(pfit));document.addEventListener('click',()=>requestAnimationFrame(pfit));
document.addEventListener('click',e=>{const l=e.target.closest('.ddm label');if(l)setTimeout(()=>{l.closest('details').open=false},0);const o=document.querySelectorAll('details.dd[open]');o.forEach(d=>{if(!d.contains(e.target))d.open=false})});
</script>
