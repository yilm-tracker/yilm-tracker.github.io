import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Drafts tab: every league draft from the 2021 startup on (history/drafts.json, written by drafts.mjs).
# One button per year; each draft is listed round by round: pick number (tile in the player's position colour), player,
# NFL team, career points chip (career.json), and the team that made the pick, with a "via <team>" box when the pick was
# traded (original owner). The team column has one fixed width behind a divider, so the avatars line up down the round.
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
def career(pl,pos):
    c=CAR.get(_nk(pl)+'|'+({'PK':'K','Def':'DEF'}.get(pos,pos) or ''))
    if not c:return ''
    pts,gp,ns,y0,y1,part=c
    t=(f'Career fantasy points in this league\'s scoring: {pts:,.1f} in {gp} games' + (f', {y0}-{y1}' if y0 else '') + (' (stats from 2009 on)' if part else ''))
    return f'<span class="dfcp{" z" if not gp else ""}" title="{e(t)}"><b>{pts:,.0f}</b><i>pts</i></span>'
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
            rows.append([rd,pk,slot,orig,by,pl,pos,NFLFIX.get(nfl,nfl)])
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
    out=[f'<div class="dfh"><b>{y} {kind}</b><span>{d.get("rounds") or max(r[0] for r in rows)} rounds · {"snake" if snake else "linear"} · {trd} traded picks · {src}</span></div>']
    # original order: round-1 slots and the team that held each slot before any trade
    r1=sorted([r for r in rows if r[0]==1],key=lambda r:r[2] or r[1])
    out.append('<div class="dfo"><span class="dfol">Original order</span><div class="dfos">'+''.join(f'<span class="dfoi"><em>{r[2] or r[1]}</em><i class="pav" data-avt="{e(r[3])}" aria-hidden="true"></i><b>{e(own(r[3]))}</b></span>' for r in r1)+'</div></div>')
    for rd in sorted({r[0] for r in rows}):
        rr=sorted([r for r in rows if r[0]==rd],key=lambda r:r[1])
        out.append(f'<div class="dfr"><div class="dfrh">Round {rd}</div>'+''.join(
            f'<div class="dfp" style="--pc:{PC.get(pos or "", "var(--hair)")}"><i class="dfn"><b>{rd}.{pk:02d}</b><span>{e(pos or "")}</span></i>'
            f'<div class="dfpl"><span class="dfpn"><b>{e(pl)}</b>{badge(nfl) if nfl else ""}</span>{career(pl,pos)}</div>'
            f'<div class="dfby"><i class="pav" data-avt="{e(by)}" aria-hidden="true"></i><span><b>{e(own(by))}</b>'+(f'<small class="dfvia"><i>via</i>{e(own(orig))}</small>' if orig!=by else '')+'</span></div></div>'
            for rd_,pk,slot,orig,by,pl,pos,nfl in rr)+'</div>')
    return ''.join(out)
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
.dfo{background:var(--deck);border:1px solid var(--hair);border-radius:12px;box-shadow:var(--dsh2);padding:10px 12px;margin:0 0 14px}
.dfol{display:block;font:700 11px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--label);margin-bottom:8px}
.dfos{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px 6px}
.dfoi{display:flex;flex-direction:column;align-items:center;gap:4px;min-width:0}
.dfoi em{font:700 12px/1 var(--display);font-style:normal;color:var(--steel)}
.dfoi .pav{width:30px;height:30px}
.dfoi b{max-width:100%;overflow:hidden;white-space:nowrap;font:700 12px/1.1 var(--display);letter-spacing:.02em;color:var(--label)}
.dfr{background:var(--deck);border:1px solid var(--hair);border-radius:12px;box-shadow:var(--dsh2);overflow:hidden;margin:0 0 12px}
.dfrh{padding:9px 12px 8px;font:700 12px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--label);border-bottom:1px solid var(--line-strong)}
.dfp{display:grid;grid-template-columns:46px minmax(0,1fr) auto;column-gap:10px;align-items:center;min-height:46px;border-top:1px solid var(--hair);padding-right:12px}
.dfrh+.dfp{border-top:0}
.dfn{align-self:stretch;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;background:var(--pc);color:#0b0e14;font-style:normal}
.dfn b{font:700 14px/1 var(--display);text-box:trim-both cap alphabetic}
.dfn span{font:700 10px/1 var(--display);letter-spacing:.06em;text-box:trim-both cap alphabetic;opacity:.8}
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
"""
if __name__=='__main__':
    s=section()
    if s:
        open(P+'draft_section.html','w',encoding='utf-8').write(s[0]+'<script>(function(){function f(){document.querySelectorAll(".dfpl b").forEach(function(b){if(!b.offsetParent)return;b.style.fontSize="";b.style.whiteSpace="";var p=b.parentElement,s0=parseFloat(getComputedStyle(b).fontSize),s=s0,o=function(){return b.scrollWidth>b.clientWidth+.5||p.scrollWidth>p.clientWidth+.5};while(o()&&s>13){s-=.5;b.style.fontSize=s+"px"}if(o()){b.style.fontSize="";b.style.whiteSpace="normal"}});document.querySelectorAll(".dfby").forEach(function(c){if(!c.offsetParent)return;c.style.removeProperty("--dfz");var z=1;while(c.scrollWidth>c.clientWidth+.5&&z>.7){z-=.04;c.style.setProperty("--dfz",z.toFixed(2))}})}f();addEventListener("resize",function(){requestAnimationFrame(f)});document.addEventListener("change",function(){requestAnimationFrame(f)});document.fonts&&document.fonts.ready.then(f)})()</script>')
        open(P+'draft_css.css','w',encoding='utf-8').write(CSS+s[1])
        print('drafts',len(D))
    else:print('no drafts')
