const FN={"Ram Rod":"Team Ram Rod","Block Party":"Bill's Block Party","Bill's":"Bill's Block Party","Homer's":"Homer's Heroes","RIPMFL":"Team RIPMFL","Cheating":"Cheating is Trying","Nuts":"Nuts in the Face","Apache":"Reverse Apache Master","Canton":"Canton waitlist"},fn=n=>FN[n]||n;  // full team names everywhere
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
const tone=r=>r<=3?'g':r>=8?'b':'';
const chip=(r,t)=>`<span class="ch ${tone(r)}"><span class="ct">${t?'T':'#'}${r}</span></span>`;
const luck=v=>`${v>0?'+':v<0?'−':''}${Math.abs(v).toFixed(2)}`;
const seg=r=>`<div class="seg10 ${tone(r)}" role="img" aria-label="Rank ${r} of 10">${Array.from({length:10},(_,k)=>`<i${k<11-r?' class="on"':''}></i>`).join('')}</div>`;
const rankSk=t=>1+Object.values(SK).filter(v=>v[0]>SK[t][0]+1e-9).length;
const tiedSk=t=>Object.values(SK).filter(v=>Math.abs(v[0]-SK[t][0])<1e-9).length>1;
const rankEf=t=>1+Object.values(EF).filter(v=>v[0]>EF[t][0]+1e-9).length;
const tiedEf=t=>Object.values(EF).filter(v=>Math.abs(v[0]-EF[t][0])<1e-9).length>1;
const pct=x=>(Math.max(0,Math.min(1,x))*100).toFixed(1)+'%';

const star=(cx,cy,R,r)=>Array.from({length:10},(_,k)=>{const a=-Math.PI/2+k*Math.PI/5,q=k%2?r:R;return (cx+q*Math.cos(a)).toFixed(2)+","+(cy+q*Math.sin(a)).toFixed(2)}).join(" ");
function season(t){
  // Columns: bar (team score, green win / red loss) + opponent tick, week number, team score rank tile, opponent score rank tile.
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
  const tile=(cx,cy,r,mode)=>{const k=r===1?'gold':r<=3?'g':r===10?'last':r>=8?'b':'n';
    const st={gold:['rgba(244,196,81,.16)','#f4c451','rgba(244,196,81,.5)'],g:['var(--win-bg)','var(--win)',''],b:['var(--loss-bg)','var(--loss)',''],last:['var(--loss-bg)','var(--loss)','rgba(255,93,115,.6)'],n:['var(--hair)','var(--steel)','']}[k];
    return `<rect${mode==='opp'?' opacity=".55"':''} x="${cx-TW/2}" y="${cy-TH/2}" width="${TW}" height="${TH}" rx="3" fill="${st[0]}"${st[2]?` stroke="${st[2]}" stroke-width="1"`:''}/>`+
           `<text x="${cx}" y="${bl(cy,9.5)}" text-anchor="middle" font-size="9.5" font-weight="500" fill="${st[1]}"${mode==='opp'?' opacity=".9"':''}>${r}</text>`};
  const played=Object.fromEntries(WK[t].map(g=>[g[0],g]));
  const lab=(cy,txt)=>`<text x="0" y="${bl(cy,12.5)}" font-family="var(--display)" font-size="12.5" font-weight="600" letter-spacing=".6" fill="var(--steel)">${txt}</text>`;
  let s=`<svg class="szn" viewBox="0 0 ${L+N*S} ${H}" role="img" aria-label="Season: ${WK[t].map(g=>`Wk ${g[0]} ${g[2]>g[3]?'W':'L'} ${g[2].toFixed(1)}-${g[3].toFixed(1)}, score rank ${g[4]}, opponent rank ${g[5]}`).join('; ')}">`+
    lab(WY,'WK')+lab(R1,'RANK')+lab(R2,'OPP');
  for(let wk=1;wk<=N;wk++){const cx=L+(wk-.5)*S,x=cx-bw/2,g=played[wk];
    if(g){const won=g[2]>g[3],c=won?'var(--win)':'var(--loss)',ohi=g[5]===1,olo=g[5]===10;
      s+=`<rect x="${x}" y="${y(g[2]).toFixed(1)}" width="${bw}" height="${(base-y(g[2])).toFixed(1)}" rx="1.5" fill="${c}" opacity=".9"/>`+
         tick(x,y(g[3]),ohi?'hi':olo?'lo':'n')+
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
    const tc=i<2?'tier-bye':i<6?'tier-po':'tier-out';
    const th=i===0?['tier-bye','Bye','Seeds 1–2',1]:i===2?['tier-po','Playoffs','Seeds 3–6',5]:i===6?['tier-out','Chasing','Seeds 7–10',-1]:null;
    const tierHtml=th?`<div class="tier ${th[0]}"><b>${th[1]}</b><span>${th[2]}</span>${th[3]>=0?`<em>Line ${wl(o[th[3]]).join('-')}</em>`:''}</div>`:'';
    const op=OPEN.has(t);
    const strip=WK[t].map(g=>{const won=g[2]>g[3];return `<div class="gm"><div class="h"><span>Wk ${g[0]}</span><span class="res ${won?'w':'l'}"><span class="ct">${won?'W':'L'}</span></span></div><div class="sc">${g[2].toFixed(2)}${chip(g[4])}</div><div class="vs">vs ${esc(fn(g[1]))}</div><div class="os">${g[3].toFixed(2)}${chip(g[5])}</div></div>`}).join('')
      +FUT[t].map(g=>`<div class="gm fut"><div class="h"><span>Wk ${g[0]}</span></div><div class="up">Upcoming</div><div class="vs">vs ${esc(fn(g[1]))}</div></div>`).join('');
    return tierHtml+`<div class="r ${tc}${i>=6?' out':''}${op?' open':''}" data-t="${esc(t)}" tabindex="0" role="button" aria-expanded="${op}">
      <div class="rk">${i+1}</div>
      <div class="nm"><span class="tn">${esc(t)}</span>${mv}</div>
      <span class="hl"><em class="lb">Hi</em><b>${Math.min(...a)}</b> · <em class="lb">Lo</em><b>${Math.max(...a)}</b> · <em class="lb">Avg</em><b>${(a.reduce((x,y)=>x+y,0)/a.length).toFixed(1)}</b></span>
      <div class="sb s-pf"><div class="stx"><em class="lb">PF</em><span class="pf">${d[3].toFixed(2)}</span>${chip(d[4])} <i class="pw">· ${d[5].toFixed(1)}/wk</i></div>${seg(d[4])}</div>
      <div class="sb s-pa"><div class="stx"><em class="lb">PA</em><span class="v">${d[6].toFixed(2)}</span>${chip(d[7])} <i class="pw">· ${d[8].toFixed(1)}/wk</i></div>${seg(d[7])}</div>
      <div class="sb s-lk"><div class="stx"><em class="lb">Luck</em><span class="v">${luck(d[12])}</span>${chip(rankOf(d[12],12,false),tied(d[12],12))} <i class="pw">· ${(d[10]/(d[10]+d[11])*G).toFixed(2)} xW</i></div><div class="trk div"><i class="${d[12]>=0?'g pos':'b neg'}" style="left:${d[12]>=0?'50%':pct(.5+d[12]/MAXLUCK/2)};width:${pct(Math.abs(d[12])/MAXLUCK/2)}"></i></div></div>
      <div class="sb s-lu"><div class="stx"><em class="lb">Tot Eff</em><span class="v">${EF[t][0].toFixed(0)}%</span>${chip(rankEf(t),tiedEf(t))} <i class="pw">· <b class="lw">${EF[t][1].toFixed(1)}</b>/wk</i></div>${seg(rankEf(t))}</div>
      <div class="sb s-sk"><div class="stx spl"><em class="lb dpl">Dropped pts</em><i class="pw pu">per wk</i><span class="brk"></span><span class="dpg">${['QB','RB','WR','TE','K','DEF'].map((k,i)=>`<span class="dpc p-${k.toLowerCase()}"><b>${k}</b><span class="${DP[t][i]>=0.05?'':'z'}">${DP[t][i].toFixed(1)}</span></span>`).join('')}</span></div></div>
      <div class="st s2"><span><em class="lb">Opp rk</em><span class="v">${d[9].toFixed(1)}</span>${chip(rankOf(d[9],9,true),tied(d[9],9))}</span><span><em class="lb">All-play</em><span class="v">${d[10]}-${d[11]}</span>${chip(rankOf(d[10],10,false),tied(d[10],10))}</span></div>
      <div class="side"><div class="rr${(String(rw0)+String(rl0)).length>2?" rr4":""}"><span class="sk ${lastR==='W'?'w':'l'}"><span class="ct">${lastR}${n}</span></span><b>${rw0}-${rl0}</b></div><span class="l5d" aria-label="Last 5 results">${WK[t].slice(-5).map(g=>`<i class="${g[2]>g[3]?'w':'l'}"></i>`).join('')}</span>${gbH}<div class="subw">${sub}</div></div>
      <div class="szw">${season(t)}</div>
      <div class="strip"${op?'':' hidden'}>${strip}</div></div>`}).join('');
}
const list=document.getElementById('list');
function toggle(row){const t=row.dataset.t;OPEN.has(t)?OPEN.delete(t):OPEN.add(t);const op=OPEN.has(t);row.classList.toggle('open',op);row.setAttribute('aria-expanded',op);row.querySelector('.strip').hidden=!op}
list.addEventListener('click',e=>{if(e.target.closest('.strip'))return;const r=e.target.closest('.r');if(r)toggle(r)});
list.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('r')){e.preventDefault();toggle(e.target)}});
const bh=document.getElementById('bh'),bm=document.getElementById('bm');
function set(med){bh.setAttribute('aria-pressed',!med);bm.setAttribute('aria-pressed',med);draw(med)}
bh.onclick=()=>set(false);bm.onclick=()=>set(true);
draw(false);
document.addEventListener('click',e=>{const l=e.target.closest('.ddm label');if(l)setTimeout(()=>{l.closest('details').open=false},0);const o=document.querySelectorAll('details.dd[open]');o.forEach(d=>{if(!d.contains(e.target))d.open=false})});
</script>
