import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# THE WIRE tab: best available players (every player on no roster in this league) from pull_wire.json (node pull.mjs wire D).
# Rows are rendered here; a small script filters by position, searches by name and sorts (projection, season points,
# points per game, Sleeper-wide adds over 48 hours). The left tile carries the position and the season position rank.
# Writes wire_section.html and wire_css.css.
import json,html
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
P=__DTP__
e=html.escape
import sys;sys.path.insert(0,P)
from nfl_colors import badge_c as badge
X=json.load(open(P+'pull_wire.json',encoding='utf-8'))
N=X['N'];ROWS=X['W']
ORD=['QB','RB','WR','TE','K','DEF']
try:
    import lg as _lg;POS=[p for p in ORD if p in getattr(_lg,'POS',ORD)]
except Exception:POS=ORD
PC={'QB':'#f7739c','RB':'#3ddcc1','WR':'#5ec6f4','TE':'#fca95c','K':'#c491ff','DEF':'#c98a72'}
INJ={'Questionable':'Q','Doubtful':'D','Out':'O','IR':'IR','PUP':'PUP','Sus':'SUS','NA':'NA','COV':'COV'}
ET=ZoneInfo('America/New_York')
def kick(iso):
    if not iso:return ''
    try:t=datetime.fromisoformat(iso.replace('Z','+00:00')).astimezone(ET)
    except Exception:return ''
    return t.strftime('%a ')+t.strftime('%I:%M %p').lstrip('0')
def n1(v):return f'{v:.1f}'
def adds(v):
    if not v:return '–'
    return f'+{v/1000:.1f}k' if v>=1000 else f'+{v}'
rows=[]
for (pid,name,pos,team,inj,pts,gp,rk,proj,opp,home,ko,ad) in ROWS:
    if pos not in POS:continue
    ppg=pts/gp if gp else 0
    nm=name if pos!='DEF' else name
    parts=nm.split(' ',1)
    short=(parts[0][0]+'. '+parts[1]) if len(parts)==2 and pos!='DEF' else nm
    it=INJ.get(inj or '','')
    mu=''
    if opp:mu=f'<span class="wha">{"vs" if home else "@"}</span>{badge(opp)}'+(f'<span class="wko">· {kick(ko)}</span>' if ko else '')
    else:mu='<span class="wko">Bye</span>'
    rows.append((proj,pts,ppg,ad,f'<div class="wrr" data-p="{pos}" data-n="{e(nm.lower())}" data-s="{proj:.2f},{pts:.2f},{ppg:.3f},{ad}">'
      f'<i class="wpt" style="--pc:{PC[pos]}"><b>{pos}</b><span>{rk if rk else "–"}</span></i>'
      f'<div class="wnm"><b><span class="wn" data-f="{e(nm)}" data-s="{e(short)}">{e(nm)}</span>{badge(team).replace("<em class=\"nfl","<em class=\"nfl tm",1)}'
      +(f'<i class="winj" title="{e(inj)}">{it}</i>' if it else '')+f'</b><small>{mu}</small></div>'
      f'<span class="wv wpj">{n1(proj)}<small>pts</small></span><span class="wv wpt2">{pts:.0f}</span><span class="wv wpg">{n1(ppg) if gp else "–"}</span><span class="wv wad">{adds(ad)}</span></div>'))
rows.sort(key=lambda r:(-r[0],-r[1]))
btn=''.join(f'<button type="button" class="wpb{" on" if p=="ALL" else ""}" data-p="{p}"'+(f' style="--pc:{PC[p]}"' if p in PC else '')+f'>{p}</button>' for p in ['ALL']+POS)
srt=lambda k,lab,cls='':f'<button type="button" class="wsb{cls}" data-k="{k}">{lab}<i aria-hidden="true">▾</i></button>'
html_=(f'<section class="wrx" aria-labelledby="wrh"><div class="posh"><b id="wrh">The Wire</b><span class="wsub">Best available · not on any roster in the league</span></div>'
  f'<div class="wrc"><div class="wpf" role="group" aria-label="Position">{btn}</div><input class="wq" type="search" placeholder="Search player…" aria-label="Search player" autocomplete="off"></div>'
  f'<div class="wrt"><div class="wrhd"><span class="wh0">Player</span><span class="wh1">Matchup</span>'
  +srt(0,f'<em>Wk {N}</em>Proj',' on')+srt(1,'<em>Season</em>Fpts')+srt(2,'Ppg')+srt(3,'<em>48h</em>Adds')+'</div>'
  f'<div class="wrl">{"".join(r[4] for r in rows)}</div><div class="wmore"></div></div>'
  '<div class="key"><div><b>The Wire</b> every player on no roster in this league with season points or a projection this week. '
  f'<b>Tile</b> position and season rank at the position (league scoring, all players). <b>Proj</b> Sleeper projection for Week {N} in league scoring. '
  '<b>Fpts / Ppg</b> season points and points per game played. <b>Adds</b> times the player was added across all Sleeper leagues in the last 48 hours. '
  'Tap a column to sort; the top 50 for the filter are shown.</div></div></section>'
  """<script>(function(){const X=document.querySelector('.wrx');if(!X)return;const L=X.querySelector('.wrl'),R=[...L.children],M=X.querySelector('.wmore');let pos='ALL',k=0,q='';
const sv=r=>r._s||(r._s=r.dataset.s.split(',').map(Number));
function draw(){const v=R.filter(r=>(pos==='ALL'||r.dataset.p===pos)&&(!q||r.dataset.n.includes(q))).sort((a,b)=>sv(b)[k]-sv(a)[k]||sv(b)[0]-sv(a)[0]);
R.forEach(r=>r.hidden=true);v.slice(0,50).forEach((r,i)=>{r.hidden=false;r.style.order=i});M.textContent=v.length?(v.length>50?'Top 50 of '+v.length:v.length+' players'):'No players';X.classList.toggle('wk3',k===3);fit()}
function fit(){X.querySelectorAll('.wrr:not([hidden]) .wn').forEach(n=>{n.textContent=n.dataset.f;n.style.fontSize='';const b=n.parentElement;if(b.scrollWidth>b.clientWidth+.5)n.textContent=n.dataset.s;let f=parseFloat(getComputedStyle(n).fontSize);while(b.scrollWidth>b.clientWidth+.5&&f>11){f-=.5;n.style.fontSize=f+'px'}})}
X.querySelectorAll('.wpb').forEach(b=>b.onclick=()=>{pos=b.dataset.p;X.querySelectorAll('.wpb').forEach(x=>x.classList.toggle('on',x===b));draw()});
X.querySelectorAll('.wsb').forEach(b=>b.onclick=()=>{k=+b.dataset.k;X.querySelectorAll('.wsb').forEach(x=>x.classList.toggle('on',x===b));draw()});
X.querySelector('.wq').oninput=ev=>{q=ev.target.value.trim().toLowerCase();draw()};
draw();addEventListener('resize',()=>requestAnimationFrame(fit));document.addEventListener('change',()=>requestAnimationFrame(fit));document.fonts&&document.fonts.ready.then(fit)})()</script>""")
css="""
.wrx .posh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}
.wrx .wsub{font-size:12.5px;color:var(--steel)}
.wrc{display:flex;gap:10px;align-items:stretch;margin:14px 0 14px;flex-wrap:wrap}
.wpf{display:flex;gap:6px;flex-wrap:wrap}
.wpb{font:700 13px/1 var(--display);letter-spacing:.06em;padding:9px 12px 8px;border-radius:9px;border:1px solid var(--hair);background:var(--deck);color:var(--pc,var(--label));box-shadow:var(--dsh2);cursor:pointer;text-box:trim-both cap alphabetic}
.wpb.on{background:var(--pc,var(--chalk));color:var(--ink);border-color:transparent}
.wq{flex:1 1 180px;min-width:0;font:500 15px var(--body);color:var(--chalk);background:var(--deck);border:1px solid var(--hair);border-radius:9px;padding:9px 12px;box-shadow:var(--dsh2);outline:none}
.wq::placeholder{color:var(--steel)}.wq:focus{border-color:var(--line-strong)}
.wrt{background:var(--deck);border:1px solid var(--hair);border-radius:14px;box-shadow:var(--dsh);overflow:hidden}
.wrhd,.wrr{display:grid;grid-template-columns:44px minmax(0,1fr) 54px 42px 40px;column-gap:8px;align-items:center;padding-right:12px}
.wrhd{align-items:end;padding-top:10px;padding-bottom:8px;border-bottom:1px solid var(--line-strong);font:700 11px/1 var(--display);letter-spacing:.08em;text-transform:uppercase;color:var(--label)}
.wrhd .wh0{grid-column:2}.wrhd .wh1,.wrr .wad,.wrhd .wsb[data-k="3"]{display:none}
.wsb{all:unset;cursor:pointer;display:flex;flex-direction:column;align-items:flex-end;gap:3px;justify-self:end;font:inherit;letter-spacing:inherit;color:inherit;text-align:right}
.wsb em{font-style:normal;font-size:9.5px;color:var(--steel);letter-spacing:.06em}
.wsb i{font-style:normal;font-size:8px;color:transparent;margin-top:-1px}.wsb.on{color:var(--chalk)}.wsb.on i{color:var(--pylon)}
.wrl{display:flex;flex-direction:column}
.wrr{min-height:52px;border-top:1px solid var(--hair)}.wrr:first-child{border-top:0}
.wrr[hidden]{display:none}
.wpt{align-self:stretch;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;background:var(--pc);color:#0b0e14;font-style:normal}
.wpt b{font:700 11px/1 var(--display);letter-spacing:.04em;text-box:trim-both cap alphabetic}
.wpt span{font:700 16px/1 var(--display);text-box:trim-both cap alphabetic}
.wnm{min-width:0;padding:8px 0}
.wnm>b{display:flex;align-items:center;gap:6px;white-space:nowrap;overflow:hidden;font:600 15px/1.2 var(--body);color:var(--chalk)}
.wnm .wn{min-width:0}
.wnm .nfl{flex:none}
.winj{font:700 10.5px/1 var(--display);font-style:normal;color:var(--loss);letter-spacing:.04em}
.wnm small{display:flex;align-items:center;gap:5px;margin-top:4px;font:500 12px/1 var(--body);color:var(--steel);white-space:nowrap}
.wnm small .nfl{transform:scale(.85)}
.wha{color:var(--steel)}
.wv{justify-self:end;font:600 14px/1 var(--body);color:var(--label);font-variant-numeric:tabular-nums;white-space:nowrap}
.wv.wpj{font:700 17px/1 var(--display);color:var(--chalk)}
.wv.wpj small{font:600 9px/1 var(--display);letter-spacing:.08em;color:var(--steel);margin-left:2px;text-transform:uppercase}
.wv.wpt2{color:var(--chalk)}
.wmore{padding:10px 14px;font-size:12px;color:var(--steel);border-top:1px solid var(--hair)}
/* phones: Adds replaces Ppg when it is the sort */
.wrx.wk3 .wrr .wpg,.wrx.wk3 .wrhd .wsb[data-k="2"]{display:none}.wrx.wk3 .wrr .wad,.wrx.wk3 .wrhd .wsb[data-k="3"]{display:flex}
@media(max-width:380px){.wrhd,.wrr{grid-template-columns:40px minmax(0,1fr) 50px 36px 36px;column-gap:6px;padding-right:10px}.wpb{padding:8px 9px 7px;font-size:12px}.wnm>b{font-size:14px}.wv{font-size:13px}.wv.wpj{font-size:16px}}
@media(min-width:760px){
 .wrhd,.wrr{grid-template-columns:56px minmax(0,1.4fr) minmax(0,1fr) 72px 64px 56px 64px;column-gap:14px;padding-right:18px}
 .wrhd .wh1{display:block;grid-column:3}.wrhd .wsb[data-k="2"],.wrhd .wsb[data-k="3"]{display:flex!important}.wrr .wad,.wrr .wpg{display:block!important}
 .wnm{display:contents}.wnm>b{grid-column:2}.wnm small{grid-column:3;margin:0;font-size:13.5px}
 .wrr{min-height:58px}.wnm>b{font-size:16px}.wpt span{font-size:18px}
}
"""
open(P+'wire_section.html','w',encoding='utf-8').write(html_)
open(P+'wire_css.css','w',encoding='utf-8').write(css)
print('wire',len(rows),'rows, week',N)
