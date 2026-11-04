import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Drafts tab: every league draft from the 2021 startup on (history/drafts.json, written by drafts.mjs).
# One button per year. Desktop (>=1100px): a draft board, one column per draft slot in the original (raw) order, headed
# by the team that owned the slot; one row per round. Each cell is filled in the player's position colour: first name,
# last name, points ("40 RPts"; startup "1,398 Pts", explained in the draft's subtitle), and a strip "1.01 · RB" + NFL team. A traded pick has a subtle gold banner at the top
# naming only the team that made the pick (current owner); when a draft has any traded pick, every cell keeps that row so names stay level.
# Below 1100px: the list, round by round: pick tile (position colour), player + NFL team on the left, a points button
# (number only; each round's header names the columns: R1 · Player · Rookie Pts · GM) whose left edge sits at 50% of
# the player cell (760px+), and the team that
# made the pick, with a "via <team>" box when the pick was traded. The team column has one fixed width behind a divider,
# so the avatars line up down the round.
# Points (career.json from career.mjs, CI only; absent offline; this league's current scoring): rookie drafts show the
# player's rookie season (first NFL regular season with a game; none for careers that began before 2009); the startup
# draft shows points from the draft season on.
# MFL drafts: the original owner comes from MFL's own note "Pick traded from <name>" (that season's team names).
# Writes draft_section.html and draft_css.css. Also importable: section(years=None) for the season archive pages.
import json,html,re
P=__DTP__
e=html.escape
D=json.load(open(P+'history/drafts.json',encoding='utf-8')) if _dt_os.path.exists(P+'history/drafts.json') else {}
TM=json.load(open(P+'history/teams.json',encoding='utf-8')) if _dt_os.path.exists(P+'history/teams.json') else {}
try:OWN=json.load(open(P+'owners.json',encoding='utf-8'))
except Exception:OWN={}
try:
    import sys;sys.path.insert(0,P);import lg as _lg;OWN=OWN or dict(getattr(_lg,'NICK',{}) or {})
except Exception:pass
# career points per drafted player (career.mjs -> career.json; built in CI, absent offline)
try:CAR=json.load(open(P+'career.json',encoding='utf-8'))
except Exception:CAR={}
def _nk(n):
    n=re.sub(r"[.'’`,]",'',str(n or '').lower()).replace('-',' ');n=re.sub(r'\b(jr|sr|ii|iii|iv|v)\b','',n);return re.sub(r'\s+',' ',n).strip()
def rookie(pl,pos):
    """(points, games, season) of the player's NFL rookie season, or None"""
    c=CAR.get(_nk(pl)+'|'+({'PK':'K','Def':'DEF'}.get(pos,pos) or ''))
    if not c or len(c)<9 or c[8] is None:return None
    return c[6],c[7],c[8]
def _rt(r):return f'Rookie season {r[2]}: {r[0]:,.1f} fantasy points in {r[1]} games (this league\'s scoring)'
def since(pl,pos,y0):
    """(points, games, first, last) from season y0 on (startup drafts), or None"""
    c=CAR.get(_nk(pl)+'|'+({'PK':'K','Def':'DEF'}.get(pos,pos) or ''))
    if not c or len(c)<10:return None
    s=[(int(k),v) for k,v in c[9].items() if int(k)>=y0]
    if not s:return 0.0,0,y0,y0
    return sum(v[0] for _,v in s),sum(v[1] for _,v in s),min(k for k,_ in s),max(k for k,_ in s)
def pts(pl,pos,y,d):
    """(value, label, title) for a pick: startup drafts = points from the draft season on, rookie drafts = rookie season"""
    if d.get('type')=='startup':
        y0=int(str(y)[:4]);r=since(pl,pos,y0)
        if not r:return None
        return r[0],f"pts since ’{y0%100:02d}",f'{r[0]:,.1f} fantasy points in {r[1]} games, {y0}-{r[3]} (this league\'s scoring)'
    r=rookie(pl,pos)
    return (r[0],'rookie pts',_rt(r)) if r else None
def career(pl,pos,y,d):
    r=pts(pl,pos,y,d)
    if not r:return ''
    return f'<span class="dfcq" title="{e(r[2])}"><span class="dfcp"><b>{r[0]:,.0f}</b></span></span>'
# NFL draft slot per player (nfl_draft.py -> nfl_draft.json, from nflverse draft_picks; committed, refreshed after each NFL draft)
try:NFD=json.load(open(P+'nfl_draft.json',encoding='utf-8'))
except Exception:NFD={}
def nflslot(pl,pos,y):
    """[season, round, overall pick], 'UDFA', or None (unknown / team defense)"""
    p={'PK':'K','Def':'DEF'}.get(pos,pos) or ''
    if p=='DEF' or not NFD:return None
    nk=_nk(pl);k=nk+'|'+p;c=CAR.get(k);rk=c[8] if c and len(c)>8 else None
    cand=NFD.get(k) or []
    if not cand:  # listed at another position (e.g. a QB playing TE): use it only when the name is unique
        alt=[v for kk,vv in NFD.items() if kk.split('|')[0]==nk for v in vv];cand=alt if len(alt)==1 else []
    if not cand and ' ' in nk:  # short first name in the NFL data (Cam / Cameron Ward): same last name and position, one first name a prefix of the other
        f0,l0=nk.split(' ',1)
        alt=[v for kk,vv in NFD.items() if kk.endswith('|'+p) and ' ' in kk.split('|')[0] and kk.split('|')[0].split(' ',1)[1]==l0 and (lambda f:f.startswith(f0) or f0.startswith(f))(kk.split('|')[0].split(' ',1)[0]) for v in vv]
        cand=alt
    yr=int(str(y)[:4])
    if rk:cand=[v for v in cand if rk-3<=v[0]<=rk]
    else:cand=[v for v in cand if v[0]<=yr]
    if cand:return cand[-1]
    return 'UDFA' if rk else None
def nslot(pl,pos,y):
    s=nflslot(pl,pos,y)
    if s=='UDFA':return '<span class="dfnl u" title="Undrafted free agent">UDFA</span>'
    if not s:return '<span class="dfnl z">–</span>'
    return f'<span class="dfnl" title="NFL draft {s[0]}: round {s[1]}, pick {s[2]} overall"><i>RD {s[1]}</i><i>PK {s[2]}</i></span>'
def tile(pl,pos,y,d,on):
    """list view (2026-11-03): points tile at the right of the player cell; '–' when the player has none yet;
    nothing when the draft has no points data at all (offline builds)"""
    if not on:return ''
    r=pts(pl,pos,y,d)
    if not r:return '<span class="dftl z" title="No points yet">–</span>'
    return f'<span class="dftl" title="{e(r[2])}">{r[0]:,.0f}</span>'
def board(y,d,rows,snake,T):
    """desktop draft board: columns = draft slots (round-1 original owner), rows = rounds"""
    T=max([T]+[r[2] or r[1] for r in rows]);rds=sorted({r[0] for r in rows})
    col={}
    for r in sorted(rows,key=lambda r:r[0]):col.setdefault(r[2] or r[1],r[3])
    at={(r[0],r[2] or r[1]):r for r in rows}
    trd=any(r[4]!=col.get(r[2] or r[1]) for r in rows)  # any traded pick: every cell keeps the banner row (names stay level)
    h=''.join(f'<span class="dfgt"><i class="pav" data-avt="{e(col.get(k,""))}" aria-hidden="true"></i><b>{e(own(col.get(k,"")))}</b></span>' for k in range(1,T+1))
    out=[f'<div class="dfg" style="--dft:{T}" role="table" aria-label="{y} draft board"><span class="dfgc"></span>{h}']
    for rd in rds:
        arr=('<i aria-hidden="true">'+('←' if rd%2==0 else '→')+'</i>') if snake else ''  # direction only matters in a snake draft
        out.append(f'<span class="dfgl"><small>RD</small><b>{rd}</b>{arr}</span>')
        for k in range(1,T+1):
            r=at.get((rd,k))
            if not r:out.append('<span class="dfc dfc0"></span>');continue
            _,pk,_,orig,by,pl,pos,nfl=r;nm=str(pl or '').split(' ',1);ro=pts(pl,pos,y,d);c0=col.get(k,'')
            out.append(f'<div class="dfc" style="--pc:{PC.get(pos or "", "var(--line)")}">'
                +(f'<span class="dfct" title="{e(own(c0))}\'s pick, made by {e(own(by))}"><b>{e(own(by))}</b></span>' if by!=c0 else '<span class="dfct dfce" aria-hidden="true"></span>' if trd else '')
                +f'<span class="dfcn"><small>{e(nm[0]) if len(nm)>1 else ""}</small><b>{e(nm[-1])}</b></span>'
                +(f'<span class="dfcr" title="{e(ro[2])}"><b>{ro[0]:,.0f}</b> {"Pts" if d.get("type")=="startup" else "RPts"}</span>' if ro else '')
                +f'<span class="dfcs"><b>{rd}.{pk:02d}</b><span>{e(pos or "")}</span>{badge(nfl) if nfl else ""}</span></div>')
    return ''.join(out)+'</div>'
PC={'QB':'#f7739c','RB':'#3ddcc1','WR':'#5ec6f4','TE':'#fca95c','K':'#c491ff','DEF':'#c98a72','PK':'#c491ff','Def':'#c98a72'}
NFLFIX={'KCC':'KC','GBP':'GB','NOS':'NO','NEP':'NE','SFO':'SF','TBB':'TB','LVR':'LV','JAC':'JAX','WSH':'WAS','LA':'LAR','FA':None,'FA*':None}
from nfl_colors import badge_c as badge
def mfl_names(y):
    """that season's MFL franchise names -> current team names"""
    f=P+f'history/mfl_{y}.json';m={}
    for yy in (y,y-1):
        g=P+f'history/mfl_{yy}.json'
        if _dt_os.path.exists(g):
            for fid,nm in json.load(open(g,encoding='utf-8'))['fr']:m.setdefault(nm.replace('’',"'").strip().lower(),TM.get('mfl',{}).get(fid,nm))
    return m
def norm(d,y):
    """rows -> [round, pick, slot, orig, by, player, pos, nfl] with the original owner filled in"""
    rows=[];snake=False
    if d['src']=='mfl':
        nm=mfl_names(int(str(y)[:4]))
        r1=[p for p in d['picks'] if p[0]==1];r2=[p for p in d['picks'] if p[0]==2]
        snake=bool(r1 and r2 and r2[0][4]==r1[-1][4] and r1[0][4]!=r1[-1][4])
        T=d.get('teams') or 10
        for rd,pk,_,_,by,pl,pos,nfl,cm in d['picks']:
            m=re.search(r'Pick traded from (.+?)\.(\s|$|\n|\])',cm or '')
            orig=nm.get(m.group(1).replace('’',"'").strip().lower(),m.group(1)) if m else by
            slot=(T+1-pk) if snake and rd%2==0 else pk
            rows.append([rd,pk,slot,orig,by,pl,{'PK':'K','Def':'DEF'}.get(pos,pos),NFLFIX.get(nfl,nfl)])  # MFL position codes
    else:
        for r in d['picks']:
            rd,pk,slot,orig,by,pl,pos,nfl=r[:8];T=d.get('teams') or 10
            if not orig or orig.startswith('Team undefined'):orig=by
            rows.append([rd,(pk-1)%T+1 if pk>T else pk,slot,orig,by,pl,pos,nfl])
        snake=d.get('draft_type')=='snake'
    return rows,snake
def own(t):return OWN.get(t) or t
def year_panel(y,d):
    rows,snake=norm(d,y);T=d.get('teams') or 10
    kind={'startup':'Startup draft','rookie':'Rookie draft'}.get(d.get('type'),'Draft')
    src='MyFantasyLeague' if d['src']=='mfl' else 'Sleeper'
    trd=sum(1 for r in rows if r[3]!=r[4])
    pnote=f' · points from {int(str(y)[:4])} on' if d.get('type')=='startup' else ' · RPts = rookie-season points'
    out=[f'<div class="dfh"><b>{y} {kind}</b><span>{d.get("rounds") or max(r[0] for r in rows)} rounds · {"snake" if snake else "linear"} · {trd} traded picks · {src}{pnote}</span></div>']
    # original order: round-1 slots and the team that held each slot before any trade
    r1=sorted([r for r in rows if r[0]==1],key=lambda r:r[2] or r[1])
    out.append(board(y,d,rows,snake,T)+'<div class="dfl">')
    out.append('<div class="dfo"><span class="dfol">Original order</span><div class="dfos">'+''.join(f'<span class="dfoi"><em>{r[2] or r[1]}</em><i class="pav" data-avt="{e(r[3])}" aria-hidden="true"></i><b>{e(own(r[3]))}</b></span>' for r in r1)+'</div></div>')
    for rd in sorted({r[0] for r in rows}):
        rr=sorted([r for r in rows if r[0]==rd],key=lambda r:r[1])
        on=any(pts(r[5],r[6],y,d) for r in rows)
        tw=max([3]+[len(f'{pts(r[5],r[6],y,d)[0]:,.0f}') for r in rr if pts(r[5],r[6],y,d)])
        out.append(f'<div class="dfr" style="--dftw:{tw}"><div class="dfrh" role="row"><span>R{rd}</span><span class="dfhp"><i>Player</i>{"<i class=dfhn>NFL</i>" if NFD else ""}{("<i class=dfhr>"+("Pts" if d.get("type")=="startup" else "RPts")+"</i>") if on else ""}</span><span class="dfhg">GM</span></div>'+''.join(
            f'<div class="dfp" style="--pc:{PC.get(pos or "", "var(--line)")}"><i class="dfn"><b>{rd}.{pk:02d}</b><span>{e(pos or "")}</span></i>'
            f'<div class="dfpl"><span class="dfpn"><b>{e(pl.replace("FootballTeam","Football Team"))}</b>{badge(nfl) if nfl else ""}</span>{nslot(pl,pos,y) if NFD else ""}{tile(pl,pos,y,d,on)}</div>'
            f'<div class="dfby" title="{e(own(by))}{(" via "+e(own(orig))) if orig!=by else ""}"><i class="pav" data-avt="{e(by)}" aria-hidden="true"></i><span><b>{e(own(by))}</b>'+(f'<small class="dfvia"><i>via</i>{e(own(orig))}</small>' if orig!=by else '')+'</span></div></div>'
            for rd_,pk,slot,orig,by,pl,pos,nfl in rr)+'</div>')
    return ''.join(out)+'</div>'
def section(years=None,idp='df'):
    ys=sorted([y for y in D if (years is None or y in years)],key=lambda y:int(str(y)[:4]))
    if not ys:return ''
    radios=''.join(f'<input type="radio" name="{idp}y" id="{idp}-{y}" class="lr"{" checked" if y==ys[-1] else ""}>' for y in ys)
    btn=''.join(f'<label class="yb" for="{idp}-{y}"><b>{y}</b><small>{"Startup" if D[y].get("type")=="startup" else "Rookie"}</small></label>' for y in ys)
    pans=''.join(f'<div class="dfx dfx-{y}">{year_panel(y,D[y])}</div>' for y in ys)
    css=''.join(f'#{idp}-{y}:checked~.dfyb label[for="{idp}-{y}"] b{{background:var(--chalk);color:var(--ink)}}#{idp}-{y}:checked~.dfx-{y}{{display:block}}' for y in ys)
    if len(ys)==1:return f'<section class="dfs">{radios}{pans}</section>',css  # one season (archive pages): no year buttons
    return (f'<section class="dfs" aria-labelledby="{idp}h">{radios}<div class="posh"><b id="{idp}h">Drafts</b><span class="wsub">Every draft since the {ys[0]} startup · pick, player and who made it</span></div>'
            f'<div class="dfyb yrs n{len(ys)}" role="group" aria-label="Draft year">{btn}</div>{pans}</section>'),css
CSS="""
.dfs .posh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}
.dfs .wsub{font-size:12.5px;color:var(--steel)}
.dfs .dfyb{margin:14px 0 16px auto}
.dfs .dfyb .yb{cursor:pointer}
.dfx{display:none}
.dfh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap;margin:4px 0 10px}
.dfh b{font:700 18px/1.1 var(--display);letter-spacing:.04em;text-transform:uppercase;color:var(--chalk)}
.dfh span{font-size:12.5px;color:var(--steel)}
.dfo{background:var(--deck);border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh-hard);padding:10px 12px;margin:0 0 14px}
.dfol{display:block;font:700 11px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--label);margin-bottom:8px}
.dfos{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px 6px}
.dfoi{display:flex;flex-direction:column;align-items:center;gap:4px;min-width:0}
.dfoi em{font:700 12px/1 var(--display);font-style:normal;color:var(--steel)}
.dfoi .pav{width:30px;height:30px}
.dfoi b{max-width:100%;overflow:hidden;white-space:nowrap;font:700 12px/1.1 var(--display);letter-spacing:.02em;color:var(--label)}
.dfr{background:var(--deck);border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh-hard);overflow:hidden;margin:0 0 12px}
.dfrh{padding:9px 12px 8px;font:700 12px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--label);border-bottom:1px solid var(--line-strong)}
.dfp{display:grid;grid-template-columns:46px minmax(0,1fr) auto;column-gap:10px;align-items:center;min-height:46px;border-top:1px solid var(--line);padding-right:12px}
.dfrh+.dfp{border-top:0}
.dfn{align-self:stretch;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;background:var(--pc);color:#0b0e14;font-style:normal}
.dfn b{font:700 14px/1 var(--display);text-box:trim-both cap alphabetic}
.dfn span{font:700 10px/1 var(--display);letter-spacing:.06em;text-box:trim-both cap alphabetic}
.dfpl{display:flex;align-items:center;gap:6px;min-width:0}
.dfpl b{min-width:0;overflow:hidden;white-space:nowrap;text-overflow:clip;font:600 15px/1.2 var(--body);color:var(--chalk)}
.dfpl .nfl{flex:none}
.dfby{display:flex;align-items:center;gap:7px;justify-self:end;min-width:0}
.dfby .pav{width:26px;height:26px;flex:none}
.dfby span{display:flex;flex-direction:column;align-items:flex-start;gap:2px;white-space:nowrap}
.dfby b{font:700 13px/1.1 var(--display);letter-spacing:.02em;color:var(--label)}
.dfby small{font:500 11px/1.1 var(--body);color:#c9a15a}
.dfs .pav{display:block;border-radius:50%;background-color:var(--deck-2);background-position:center;background-size:cover;background-repeat:no-repeat;box-shadow:0 0 0 1px var(--line-strong)}
@media(max-width:380px){.dfp{grid-template-columns:42px minmax(0,1fr) auto;column-gap:8px;padding-right:10px}.dfpl b{font-size:14px}.dfby .pav{width:22px;height:22px}}
@media(min-width:760px){.dfos{grid-template-columns:repeat(10,minmax(0,1fr))}.dfr .dfp{min-height:50px}}
/* 2026-11-03: team column = one fixed width behind a divider (avatars line up down the round), "via" box for traded
   picks, career points chip after the NFL badge */
.dfp{grid-template-columns:46px minmax(0,1fr) var(--dfbw,140px);padding-right:0}
.dfpl{padding-right:10px;flex-direction:column;align-items:flex-start;justify-content:center;gap:5px;padding-top:7px;padding-bottom:7px}
.dfpn{display:flex;align-items:center;gap:6px;min-width:0;max-width:100%}
.dfpn b[style*="normal"]{line-height:1.15!important;overflow:visible!important}
@media(min-width:760px){.dfpl{flex-direction:row;align-items:center;gap:8px;padding-top:0;padding-bottom:0}}
.dfby{justify-self:stretch;align-self:stretch;justify-content:flex-start;gap:9px;padding:6px 10px 6px 12px;border-left:3px solid var(--pg,#0c1316);background:rgba(0,0,0,.13)}
.dfby .pav{width:28px;height:28px}
.dfby span{gap:4px;zoom:var(--dfz,1)}
.dfvia{display:inline-flex;align-items:baseline;gap:4px;padding:3px 6px 2px;border-radius:4px;background:rgba(201,161,90,.12);box-shadow:inset 0 0 0 1px rgba(201,161,90,.45);font:600 11px/1 var(--display)!important;letter-spacing:.04em;text-transform:uppercase;color:#d9b568!important}
.dfvia i{font-style:normal;font-weight:700;font-size:9.5px;color:rgba(217,181,104,.7)}
.dfcp{flex:none;display:inline-flex;align-items:baseline;gap:3px;padding:3px 6px 2px;border-radius:5px;background:var(--deck-2);box-shadow:inset 0 0 0 1px var(--line-strong),0 1px 0 rgba(0,0,0,.35);font-family:var(--display);line-height:1}
.dfcp b{font:700 12.5px/1 var(--display)!important;color:var(--chalk)!important;font-variant-numeric:tabular-nums}
.dfcp i{font-style:normal;font-weight:600;font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--steel)}
.dfcp.z b{color:var(--steel)!important}
@media(max-width:420px){.dfp{--dfbw:124px}.dfby{padding:6px 8px 6px 10px;gap:7px}.dfby .pav{width:26px;height:26px}}
@media(max-width:380px){.dfp{--dfbw:112px}.dfby{padding:6px 6px 6px 8px;gap:6px}.dfby .pav{width:22px;height:22px}.dfvia{font-size:10px!important;padding:2px 4px 1px}.dfcp b{font-size:11.5px!important}}
/* 2026-11-03: desktop draft board (>=1100px); the list stays below 1100px */
.dfg{display:none}
@media(min-width:1100px){
 .dfl{display:none}
 .dfg{display:grid;grid-template-columns:44px repeat(var(--dft),minmax(0,1fr));gap:5px;align-items:stretch;background:var(--deck);border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh-hard);padding:10px 10px 10px 6px;margin:0 0 14px}
 .dfgt{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:5px;min-width:0;padding:2px 0 6px}
 .dfgt .pav{width:32px;height:32px}
 .dfgt b{max-width:100%;text-align:center;font:700 12.5px/1.1 var(--display);letter-spacing:.03em;color:var(--label);white-space:nowrap}
 .dfgl{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;font-family:var(--display);color:var(--steel)}
 .dfgl small{font:700 10px/1 var(--display);letter-spacing:.1em}
 .dfgl b{font:700 19px/1 var(--display);color:var(--chalk)}
 .dfgl i{font-style:normal;font-size:12px;line-height:1}
 .dfc{display:flex;flex-direction:column;min-width:0;min-height:96px;border-radius:7px;overflow:hidden;background:var(--pc);color:#0b0e14;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
 .dfc0{background:rgba(238,240,244,.035);box-shadow:inset 0 0 0 1px var(--line)}
 .dfct{flex:none;display:flex;align-items:center;justify-content:center;gap:4px;box-sizing:border-box;height:17px;padding:1px 7px 0;background:#e6cf96;box-shadow:inset 0 -1px 0 rgba(140,104,40,.45);color:#5c4515;font:600 10px/1.1 var(--display);letter-spacing:.05em;text-transform:uppercase;white-space:nowrap}
 .dfct b{font-weight:700;color:#3b2a08}
 .dfct i{font-style:normal;opacity:.7}
 .dfce{background:transparent;box-shadow:none}
 .dfcn{display:flex;flex-direction:column;gap:1px;padding:6px 7px 0;min-width:0}
 .dfcn small{font:500 11.5px/1.15 var(--body);white-space:nowrap;opacity:.78}
 .dfcn b{font:700 16px/1.1 var(--display);letter-spacing:.01em;white-space:nowrap}
 .dfcr{padding:4px 7px 0;font:600 10px/1 var(--display);letter-spacing:.06em;text-transform:uppercase;opacity:.82;white-space:nowrap}
 .dfcr b{font-size:13px;letter-spacing:0;font-variant-numeric:tabular-nums}
 .dfcs{display:flex;align-items:center;gap:5px;margin-top:auto;box-sizing:border-box;height:29px;padding:0 5px 0 7px;background:rgba(0,0,0,.13);font:700 11.5px/1 var(--display);letter-spacing:.03em;white-space:nowrap}
 .dfcs>span{opacity:.75}
 .dfcs .nfl{margin-left:auto;flex:none}
}
/* 2026-11-03: list player cell: name on the left; the points button holds only the number and starts at 50% of the cell
   (so every button in the round lines up), its label outside it to the right */
.dfcq{flex:none;display:inline-flex;align-items:center;gap:6px}
.dfcq>i{font:600 10px/1 var(--display);font-style:normal;letter-spacing:.08em;text-transform:uppercase;color:var(--steel);white-space:nowrap}
.dfcq .dfcp{min-width:34px;justify-content:center}
@media(min-width:760px){
 .dfpl{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:center;justify-content:stretch;column-gap:0;padding-right:0}
 .dfpl .dfpn{justify-self:start;padding-right:12px}
 .dfpl .dfcq{justify-self:start}
}
/* 2026-11-03 (later): each round's header names the list columns (R1 · Player · Rookie Pts · GM); the points button
   holds only the number */
.dfrh{display:grid;grid-template-columns:46px minmax(0,1fr) var(--dfbw,140px);column-gap:10px;align-items:center;padding:9px 0 8px!important}
.dfrh>span:first-child{text-align:center}
.dfhp{display:flex;gap:6px;min-width:0}.dfhp i{font-style:normal;white-space:nowrap}
.dfhp i+i::before{content:"·";margin-right:6px;color:var(--steel)}
.dfhg{padding-left:15px}
@media(max-width:420px){.dfrh{--dfbw:124px}.dfhg{padding-left:13px}}
@media(max-width:380px){.dfrh{--dfbw:112px;grid-template-columns:42px minmax(0,1fr) var(--dfbw);column-gap:8px}.dfhg{padding-left:11px}}
@media(min-width:760px){.dfhp{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0}.dfhp i+i::before{content:none}}
"""
if __name__=='__main__':
    s=section()
    if s:
        open(P+'draft_section.html','w',encoding='utf-8').write(s[0]+'<script>(function(){function fz(b,m){b.style.fontSize="";b.style.whiteSpace="";var s=parseFloat(getComputedStyle(b).fontSize),o=function(){return b.scrollWidth>b.clientWidth+.5||b.parentElement.scrollWidth>b.parentElement.clientWidth+.5};while(o()&&s>m){s-=.5;b.style.fontSize=s+"px"}if(o()){b.style.fontSize="";b.style.whiteSpace="normal";s=parseFloat(getComputedStyle(b).fontSize);while(o()&&s>7){s-=.5;b.style.fontSize=s+"px"}}}function f(){document.querySelectorAll(".dfcn b,.dfcn small,.dfgt b").forEach(function(b){if(b.offsetParent)fz(b,11)});document.querySelectorAll(".dfct,.dfcr").forEach(function(b){if(b.offsetParent)fz(b,8.5)});document.querySelectorAll(".dfpl b").forEach(function(b){if(!b.offsetParent)return;b.style.fontSize="";b.style.whiteSpace="";var p=b.parentElement,s0=parseFloat(getComputedStyle(b).fontSize),s=s0,o=function(){return b.scrollWidth>b.clientWidth+.5||p.scrollWidth>p.clientWidth+.5};while(o()&&s>13){s-=.5;b.style.fontSize=s+"px"}if(o()){b.style.fontSize="";b.style.whiteSpace="normal";s=s0;while(o()&&s>10){s-=.5;b.style.fontSize=s+"px"}}});document.querySelectorAll(".dfby").forEach(function(c){if(!c.offsetParent)return;c.style.removeProperty("--dfz");var z=1;while(c.scrollWidth>c.clientWidth+.5&&z>.7){z-=.04;c.style.setProperty("--dfz",z.toFixed(2))}})}f();addEventListener("resize",function(){requestAnimationFrame(f)});document.addEventListener("change",function(){requestAnimationFrame(f)});document.fonts&&document.fonts.ready.then(f)})()</script>')
        open(P+'draft_css.css','w',encoding='utf-8').write(CSS+s[1])
        print('drafts',len(D))
    else:print('no drafts')
