import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Renders the Stats tab: sub-tab nav + Positions (existing POS_SECTION placeholder) + 10 modules.
import html,sys
P=__DTP__+''
import sys as _s0;_s0.path.insert(0,P);import lg
sys.path.insert(0,P)
import sx_data as D
from nfl_colors import badge_c as badge
e=html.escape
T,TEAMS,G,NOW,SHORT,CODE=D.T,D.TEAMS,D.G,D.NOW,D.SHORT,D.CODE
def rec(t):return f'{T[t][0]}-{T[t][1]}'
def nm(t):return f'<span class="sxn">{e(t)}</span>'
def sgn(x,d=1):return ('+' if x>=0.05 else '−' if x<=-0.05 else '')+f'{abs(x):.{d}f}'
def pct(x):
    v='0' if x==0 else '<0.1' if x<0.05 else '>99.9' if 99.95<=x<100 else f'{x:.1f}' if (x<10 or x>=99.5) and x<100 else f'{x:.0f}'
    return v+'<small>%</small>'
def pz(pos):return f'<i class="pz p-{pos.lower()}">{pos}</i>'
def dvb(v,mx):
    w=min(abs(v)/mx,1)*50 if mx else 0
    return f'<span class="dvb"><i class="{"up" if v>=0 else "dn"}" style="width:{w:.2f}%"></i></span>'
def hbar(v,mx,cls=''):return f'<span class="hbr"><i class="{cls}" style="width:{(min(v/mx,1)*100 if mx else 0):.2f}%"></i></span>'
def nmb(t,bar):return f'<span class="sxnb">{nm(t)}{bar}</span>'
def head(title,sub):return f'<div class="sxh"><b>{title}</b><span>{sub}</span></div>'
def table(cols,rows,cls=''):
    # cols: list of (label, width) ; first col is the team name (flex)
    tpl=' '.join(['minmax(0,1fr)']+[w for _,w in cols[1:]])
    hd=''.join(f'<span>{c}</span>' for c,_ in cols)
    return f'<div class="sxt {cls}" style="--cols:{tpl}"><div class="sxr sxhd">{hd}</div>'+''.join(f'<div class="sxr">{"".join(r)}</div>' for r in rows)+'</div>'
# ---------- 1 Odds
O,meta=D.odds()
import psim as _PS
PS=_PS.run()
def _otab(rows_src,title_col,old=False):
    rows=[];nc=5 if title_col else 4
    for t in sorted(TEAMS,key=lambda t:(-rows_src[t]['po'],-rows_src[t]['w'])):
        o=rows_src[t];a,b,c=o['top'],o['bye']-o['top'],o['po']-o['bye']
        bar='<span class="obar">'+''.join(f'<i class="{k}" style="width:{v:.2f}%"></i>' for k,v in (('o1',a),('o2',b),('o3',c)) if v>=1)+'</span>'
        tc=f'<span class="sxv c4">{pct(o["title"])}</span>' if title_col else ''
        rows.append(f'<div class="odr"><div class="odt">{nm(t)}<span class="sxv odn">{rec(t)}</span></div>{bar}'
                    f'<div class="odv" style="grid-template-columns:repeat({nc},minmax(0,1fr))"><span class="sxv">{o["w"]:.1f}</span><span class="sxv c1">{pct(o["top"])}</span><span class="sxv c2">{pct(o["bye"])}</span><span class="sxv b c3">{pct(o["po"])}</span>{tc}</div></div>')
    hd=(f'<div class="odv sxhd" style="grid-template-columns:repeat({nc},minmax(0,1fr))"><span>Proj W</span><span class="c1">#1 seed</span><span class="c2">Bye</span><span class="c3">Playoffs</span>'
        +('<span class="c4">Title</span>' if title_col else '')+'</div>')
    return '<div class="odx">'+hd+''.join(rows)+'</div>'
def m_odds():
    tit='title' in next(iter(PS['teams'].values()))
    lg='<div class="olg"><span class="o1">#1 seed</span><span class="o2">Bye</span><span class="o3">Playoffs</span></div>'
    wk=PS['weeks']
    sub=(f'{PS["n"]:,} simulated seasons, Weeks {wk[0]}–{wk[-1]}'+(' + playoffs' if tit else '') if wk else 'regular season complete · final seeds')
    sw=('<input type="radio" name="odm" id="odm-p" class="lr" checked><input type="radio" name="odm" id="odm-t" class="lr">'
        '<div class="odsw"><label for="odm-p">Player sim</label><label for="odm-t">Team average</label></div>')
    note=('<p class="odnote odn-p">Each starter drawn from his Sleeper projection with a position-fitted spread, teammates correlated, '
          'best projected lineup each week, live scores for the week in progress.</p>'
          '<p class="odnote odn-t">The earlier model: each team\'s score drawn from its season average (65%, with 35% league average) and spread. '
          'No rosters, injuries or byes.</p>')
    css=('<style>.odsw{display:inline-flex;gap:2px;padding:3px;border-radius:9px;background:var(--deck-2);box-shadow:inset 0 0 0 1px var(--hair);margin:2px 0 8px}'
         '.odsw label{padding:6px 12px;border-radius:7px;font-weight:600;font-size:13px;color:var(--steel);cursor:pointer}'
         '#odm-p:checked~.odsw label[for=odm-p],#odm-t:checked~.odsw label[for=odm-t]{background:var(--chalk);color:var(--ink)}'
         '.odm-t,.odn-t{display:none}#odm-t:checked~.odm-p,#odm-t:checked~.odn-p{display:none}#odm-t:checked~.odm-t,#odm-t:checked~.odn-t{display:block}'
         '.odnote{margin:0 0 10px;font-size:12px;line-height:1.45;color:var(--steel)}.sxv.c4,.sxhd .c4{color:var(--chalk)}</style>')
    return (head('Playoff odds',sub)+css+sw+note+lg+f'<div class="odm-p">{_otab(PS["teams"],tit)}</div><div class="odm-t">{_otab(O,False)}</div>')
def m_draft():
    tm=PS['teams'];rows=[]
    for t in sorted(TEAMS,key=lambda t:tm[t]['avgpick']):
        d=tm[t]['pick'];rows.append([f'<span>{nm(t)}</span>',f'<span class="sxv">{tm[t]["avgpick"]:.1f}</span>',f'<span class="sxv c1">{pct(d[0])}</span>',f'<span class="sxv">{pct(sum(d[:3]))}</span>'])
    return (head('Draft order odds','Next rookie draft, from the same simulated seasons')+
            '<p class="odnote">Assumes non-playoff teams pick by reverse standings (worst record first) and playoff teams by finish (champion last).</p>'+
            table([('Team',''),('Avg pick','64px'),('1.01','56px'),('Top 3','56px')],rows))
# ---------- 2 Schedule swap
M=D.schedswap()
def m_sched():
    order=D.PH
    hd='<span></span>'+''.join(f'<span>{CODE[b]}</span>' for b in order)
    rows=[]
    for a in order:
        cells=''.join(f'<span class="mx{" dg" if a==b else " up" if M[a][b]>M[a][a] else " dn" if M[a][b]<M[a][a] else ""}" tabindex="0" role="button" '
                      f'data-a="{e(a)}" data-b="{e(b)}" data-w="{M[a][b]}" data-o="{M[a][a]}">{M[a][b]}</span>' for b in order)
        rows.append(f'<div class="sxr"><span class="mxn">{e(SHORT[a])}</span>{cells}</div>')
    # tap a cell: who, whose schedule, own-schedule wins -> swapped wins, and the gain or loss
    mat=('<div class="ssb" aria-live="polite"><span class="ssh">Tap a cell to swap schedules</span>'
         '<span class="ssn"><b class="ssa"></b><span class="sso"></span></span>'
         '<span class="ssw"><span class="ssv"><i class="ss0"></i><i class="ssr">\u2192</i><b class="ss1"></b></span><small>wins</small></span>'
         '<span class="ssd"></span></div>'
         f'<div class="sxm ssm"><div class="sxr sxhd">{hd}</div>{"".join(rows)}</div>'
         '<script>(function(){var m=document.currentScript.previousElementSibling,b=m.previousElementSibling,cur=null;'
         'function q(c){return b.querySelector(c)}'
         'function pos(n){return n+(/s$/i.test(n)?"\u2019":"\u2019s")}'
         'm.addEventListener("click",function(e){var c=e.target.closest(".mx[data-w]");if(!c)return;if(cur)cur.classList.remove("on");'
         'if(c===cur){cur=null;b.className="ssb";return}cur=c;c.classList.add("on");'
         'var w=+c.dataset.w,o=+c.dataset.o,d=w-o,own=c.dataset.a===c.dataset.b;'
         'q(".ssa").textContent=c.dataset.a;q(".sso").textContent=own?"own schedule":"with "+pos(c.dataset.b)+" schedule";'
         'q(".ss0").textContent=own?"":o;q(".ss1").textContent=w;'
         'var p=q(".ssd");p.textContent=own?"Actual":d>0?"+"+d:d<0?"\u2212"+(-d):"\u00b10";'
         'p.title=own?"":(d>0?"Gains ":d<0?"Loses ":"No change, ")+(d?Math.abs(d)+(Math.abs(d)===1?" win":" wins"):"same wins");'
         'b.className="ssb on"+(own?" own":d>0?" up":d<0?" dn":" eq")});'
         'm.addEventListener("keydown",function(e){if((e.key==="Enter"||e.key===" ")&&e.target.dataset.w){e.preventDefault();e.target.click()}})})()</script>')
    av={a:sum(M[a][b] for b in TEAMS)/len(TEAMS) for a in TEAMS}
    lr=[[nmb(a,dvb(T[a][0]-av[a],1.2)),f'<span class="sxv">{T[a][0]}</span>',f'<span class="sxv">{av[a]:.1f}</span>',f'<span class="sxv b {"up" if T[a][0]-av[a]>=0.5 else "dn" if T[a][0]-av[a]<=-0.5 else ""}">{sgn(T[a][0]-av[a])}</span>'] for a in sorted(TEAMS,key=lambda a:-(T[a][0]-av[a]))]
    return (head('Schedule swap',f'Wins through Week {G} with each team\'s schedule')+mat+
            head('Schedule luck',f'Actual wins vs average across all {len(TEAMS)} schedules')+table([('Team',''),('Wins','42px'),('Avg','42px'),('Luck','46px')],lr))
EW=D.everyweek()
def _rec(r):return f'{r[0]}-{r[1]}'+(f'-{r[2]}' if r[2] else '')
def m_everyweek():
    order=D.PH
    hd='<span></span>'+''.join(f'<span>{CODE[b]}</span>' for b in order)
    rows=[]
    for a in order:
        cells=''.join('<span class="mx dg"></span>' if a==b else f'<span class="mx{" up" if EW[a][b][0]>EW[a][b][1] else " dn" if EW[a][b][0]<EW[a][b][1] else ""}" title="{e(a)} {_rec(EW[a][b])} vs {e(b)}" tabindex="0" role="button" data-a="{e(a)}" data-b="{e(b)}" data-w="{EW[a][b][0]}" data-l="{EW[a][b][1]}" data-t="{EW[a][b][2]}">{EW[a][b][0]}</span>' for b in order)
        rows.append(f'<div class="sxr"><span class="mxn">{e(SHORT[a])}</span>{cells}</div>')
    mat=(f'<div class="ewb" aria-live="polite"><span class="ewa"></span><b class="ewr">Tap a cell for the full record</b><span class="ewo"></span></div>'
         f'<div class="sxm ewm"><div class="sxr sxhd">{hd}</div>{"".join(rows)}</div>'
         '<script>(function(){var m=document.currentScript.previousElementSibling,b=m.previousElementSibling,cur=null,H=b.querySelector(".ewr").textContent;'
         'function set(a,r,o){b.querySelector(".ewa").textContent=a;b.querySelector(".ewr").textContent=r;b.querySelector(".ewo").textContent=o;b.classList.toggle("on",!!a)}'
         'm.addEventListener("click",function(e){var c=e.target.closest(".mx[data-w]");if(!c)return;if(cur)cur.classList.remove("on");'
         'if(c===cur){cur=null;set("",H,"");return}cur=c;c.classList.add("on");'
         'set(c.dataset.a,c.dataset.w+"\u2013"+c.dataset.l+(+c.dataset.t?"\u2013"+c.dataset.t:""),c.dataset.b)});'
         'm.addEventListener("keydown",function(e){if((e.key==="Enter"||e.key===" ")&&e.target.dataset.w){e.preventDefault();e.target.click()}})})()</script>')
    # the closest calls: pairs whose every-week record is within one win, and the most lopsided
    pr=sorted({tuple(sorted((a,b))) for a in TEAMS for b in TEAMS if a!=b},key=lambda p:(abs(EW[p[0]][p[1]][0]-EW[p[0]][p[1]][1]),p))
    def line(a,b):
        r=EW[a][b]
        if r[1]>r[0]:a,b=b,a;r=EW[a][b]
        return [nm(a),f'<span class="sxv b">{_rec(r)}</span>',nm(b)]
    lop=sorted(pr,key=lambda p:-abs(EW[p[0]][p[1]][0]-EW[p[0]][p[1]][1]))[:6]
    return (head('Every-week head to head',f'Row team wins if the row team had played the column team every week, Weeks 1–{G}')+mat+
            head('Most lopsided','Same opponent every week, better team first')+table([('Team',''),('Record','52px'),('vs','minmax(0,1fr)')],[line(*p) for p in lop],'ewl'))
# ---------- 3 Trades
def m_trades():
    out=[head('Trade scorecard',f'Points scored since each trade · through Week {G}')]
    for x in D.trades():
        SD=x['sides'];pend=x['eff']>G
        def side(s):
            win=(not pend) and all(s['tot']>o['tot']+0.05 for o in SD if o is not s)
            fp=lambda v:'–' if pend else f'{v:.1f}'
            pl=''.join(f'<div class="tpl"><span class="tpn">{e(p["name"])}<span class="tpb">{pz(p["pos"])}{badge(p["nfl"])}</span></span>{"" if pend else f"<b>{p['pts']:.1f}</b>"}</div>' for p in s['pl'])
            def pkh(k):
                y,rd,rest=k.split(' ',2);return f'<div class="tpk"><i class="pkc r{rd[0]}">{rd}</i><span class="pkt">{y} <em>{e(rest.strip("()"))}</em></span></div>'
            pk=''.join(pkh(k) for k in s['pk'])
            fb=f'<div class="tpk"><i class="pkc fb">${s["faab"]}</i>FAAB</div>' if s['faab'] else ''
            body=pl+pk+fb or '<div class="tpk">–</div>'
            tot='<span>No games yet</span>' if pend else ('<span>No players</span>' if not s['pl'] else f'<b>{s["tot"]:.1f}</b><span>pts since</span>')
            return f'<div class="tsd{" win" if win else ""}"><div class="tnm">{e(s["team"])}</div><div class="trc">receives</div>{body}<div class="ttot">{tot}</div></div>'
        when=f'{x["date"]} · counts from Week {x["eff"]}' if not pend else f'{x["date"]} · no games since'
        if x['eff']==1:when=f'{x["date"]} · before Week 1'
        out.append(f'<div class="trd"><div class="trw">{when}</div><div class="trg"{f' style="grid-template-columns:repeat({len(SD)},minmax(0,1fr))"' if len(SD)>2 else ''}>{''.join(side(s) for s in SD)}</div></div>')
    return ''.join(out)
# ---------- 4 Lineup calls
RW,PER=D.decisions()
def m_lineups():
    top=RW[:8];li=[]
    for r in top:
        flip='<i class="dtag">Cost the win</i>' if r['flip'] and r['bench']['pts']-r['start']['pts']>=r['them']-r['me'] else ''
        mx=40
        def ln(q,lab,cls):return f'<div class="dln dln2"><span class="dlb">{lab}</span><span class="dnm">{pz(q["pos"])}<b>{e(q["name"])}</b></span><em class="{cls}">{q["pts"]:.1f}</em></div>'
        li.append(f'<div class="dcl dcl2"><div class="dch dch2"><i class="dwk">Wk {r["w"]}</i><span class="dtm">{e(r["team"])}</span><span class="dsw"><b>+{r["swing"]:.1f}</b><small>pts lost</small></span></div>'
                  +ln(r['bench'],'Bench','up')+ln(r['start'],'Started','dn')+(f'<div class="dft">{flip}</div>' if flip else '')+'</div>')
    mxl=max(v['lost'] for v in PER.values())
    rows=[[nmb(t,hbar(PER[t]['lost'],mxl,'am')),f'<span class="sxv">{PER[t]["lost"]:.1f}</span>',f'<span class="sxv">{PER[t]["lost"]/G:.1f}</span>',f'<span class="sxv b {"dn" if PER[t]["flip"] else "z"}">{PER[t]["flip"]}</span>'] for t in sorted(TEAMS,key=lambda t:(-PER[t]['flip'],-PER[t]['lost']))]
    return (head('Costliest lineup calls','Biggest single bench-for-starter swaps')+''.join(li)+
            head('Winnable losses','Losses the best lineup on the roster would have won')+
            table([('Team',''),('Dropped','56px'),('Per wk','46px'),('Winnable','58px')],rows))
# ---------- 5 Projections
TM,HI,LO=D.projections()
def m_proj():
    rows=[[nmb(t,dvb(TM[t]['avg'],20)),f'<span class="sxv b {"up" if TM[t]["avg"]>=0.05 else "dn" if TM[t]["avg"]<=-0.05 else ""}">{sgn(TM[t]["avg"])}</span>',f'<span class="sxv">{TM[t]["beat"]}/{G}</span>'] for t in sorted(TEAMS,key=lambda t:-TM[t]['avg'])]
    def pl(lst,cls):
        return ''.join(f'<div class="ppl"><span class="pnm">{pz(r["pos"])}<b>{e(r["name"])}</b>{badge(r["nfl"])}<span class="pmt">{e(SHORT[r["team"]])} · {r["n"]} starts</span></span><b class="sxv {cls}">{sgn(r["avg"])}</b></div>' for r in lst)
    return (head('Vs projection','Starters\' points minus Sleeper projection, per week')+table([('Team',''),('Per wk','54px'),('Beat','44px')],rows)+
            head('Overachievers','Per start vs projection · min. 3 starts')+pl(HI,'up')+
            head('Underachievers','Per start vs projection · min. 3 starts')+pl(LO,'dn'))
# ---------- 6 Margins
CL,CLG,BLG=D.close()
def m_close():
    rows=[[nmb(t,dvb(CL[t]['avgm'],45)),f'<span class="sxv">{CL[t]["close"][0]}-{CL[t]["close"][1]}</span>',f'<span class="sxv">{CL[t]["blow"][0]}-{CL[t]["blow"][1]}</span>',f'<span class="sxv b {"up" if CL[t]["avgm"]>=0.05 else "dn"}">{sgn(CL[t]["avgm"])}</span>'] for t in sorted(TEAMS,key=lambda t:-CL[t]['avgm'])]
    def gl(gs,cls):return ''.join(f'<div class="gml"><span class="gwk">Wk {g["w"]}</span><span class="gtm"><span><b class="gln"><i class="wl w">W</i>{e(g["win"])}</b><em>{g["ws"]:.2f}</em></span><span><span class="gln"><i class="wl l">L</i>{e(g["lose"])}</span><em>{g["ls"]:.2f}</em></span></span><b class="gmv {cls}">{g["m"]:.2f}</b></div>' for g in gs)
    return (head('Margins',f'Close = under 10 pts · blowout = 30+ pts')+table([('Team',''),('Close','46px'),('Blowout','56px'),('Avg','46px')],rows)+
            head('Closest games','Winner on top · margin on the right')+gl(CLG,'cl')+head('Biggest blowouts','Winner on top · margin on the right')+gl(BLG,'bo'))
# ---------- Consistency: how much each team's weekly score swings
import statistics as _st
def m_cons():
    N=len(TEAMS);rows=[]
    allp=[g[2] for t in TEAMS for g in D.WK[t]];lo=10*int(min(allp)//10);hi=10*int(-(-max(allp)//10))
    X=lambda v:6+(v-lo)/(hi-lo)*288
    S={}
    for t in TEAMS:
        a=[g[2] for g in D.WK[t]];m=sum(a)/len(a);sd=_st.pstdev(a)
        S[t]=dict(m=m,sd=sd,cv=sd/m*100,lo=min(a),hi=max(a),top=sum(1 for g in D.WK[t] if g[4]<=3),bot=sum(1 for g in D.WK[t] if g[4]>N-3),g=D.WK[t])
    rk={t:i+1 for i,t in enumerate(sorted(TEAMS,key=lambda t:S[t]['cv']))}
    for i,t in enumerate(sorted(TEAMS,key=lambda t:S[t]['cv'])):
        x=S[t]
        dots=''.join(f'<circle cx="{X(g[2]):.1f}" cy="13" r="4" class="{"w" if g[2]>g[3] else "l"}"/>' for g in x['g'])
        svg=(f'<svg class="csv" viewBox="0 0 300 26" preserveAspectRatio="none" aria-hidden="true"><line x1="6" x2="294" y1="13" y2="13" class="ax"/>'
             f'<rect x="{X(x["m"]-x["sd"]):.1f}" y="5" width="{X(x["m"]+x["sd"])-X(x["m"]-x["sd"]):.1f}" height="16" rx="3" class="bd"/>'
             f'<line x1="{X(x["m"]):.1f}" x2="{X(x["m"]):.1f}" y1="3" y2="23" class="mn"/>{dots}</svg>')
        rows.append(f'<div class="csr"><div class="cst"><span class="csl"><em class="csi">{i+1}</em>{nm(t)}</span><span class="csn"><b>±{x["sd"]:.1f}</b><i>{x["cv"]:.0f}%</i></span></div>{svg}'
                    f'<div class="csm"><span>Avg<b>{x["m"]:.1f}</b></span><span>Low<b>{x["lo"]:.1f}</b></span><span>High<b>{x["hi"]:.1f}</b></span>'
                    f'<span>Top-3<b>{x["top"]}</b></span><span>Bottom-3<b>{x["bot"]}</b></span></div></div>')
    css=('<style>.csr{padding:10px 0;border-bottom:1px solid var(--hair)}.sxc .cst{display:flex!important;flex-direction:row!important;justify-content:space-between!important;align-items:center;gap:10px}'
         '.csl{display:inline-flex;align-items:center;gap:8px;min-width:0}.csi{font-style:normal;font-family:var(--display);font-weight:700;font-size:13px;color:var(--dim);min-width:14px;text-align:right}'
         '.csn{display:inline-flex;align-items:baseline;gap:7px;font-family:var(--display);font-size:16px;color:var(--chalk);white-space:nowrap}.csn i{font-style:normal;font-size:13px;color:var(--steel)}'
         '.csv{display:block;width:100%;height:26px;margin:6px 0 4px}.csv .ax{stroke:var(--hair);stroke-width:1}.csv .bd{fill:rgba(238,240,244,.07);stroke:rgba(238,240,244,.18)}'
         '.csv .mn{stroke:var(--label);stroke-width:1.5}.csv circle.w{fill:var(--win)}.csv circle.l{fill:var(--loss)}.csv circle{stroke:var(--deck);stroke-width:1}'
         '.sxc .csm{display:flex!important;flex-direction:row!important;justify-content:space-between!important;flex-wrap:nowrap;gap:6px;font-size:11.5px;color:var(--steel);text-align:left}'
         '.csm span{white-space:nowrap}.csm b{font-family:var(--display);font-weight:600;color:var(--label);margin-left:4px}'
         '.cssc{display:flex;justify-content:space-between;font-size:10.5px;color:var(--dim);margin:2px 0 4px}'
         '.cskey{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:11.5px;color:var(--steel);margin:2px 0 8px}.cskey b{font-family:var(--display);font-weight:600;color:var(--label);margin-right:4px}</style>')
    scale=f'<div class="cssc"><span>{lo}</span><span>weekly points</span><span>{hi}</span></div>'
    key=('<div class="cskey"><span><b>±</b>spread (1 SD)</span><span><b>%</b>swing = spread ÷ avg, steadiest first</span>'
         '<span><b>▭</b>avg ± spread</span><span><b>●</b>weeks, green W · red L</span></div>')
    return head('Consistency',f'Weekly score swings · Weeks 1–{D.G}')+css+key+scale+''.join(rows)
# ---------- 7 Stars
ST=D.stars()
def m_stars():
    o=[head('Star dependence','Share of season points from the top 1 and top 3 scorers (as starters)')]
    for t in sorted(TEAMS,key=lambda t:-ST[t]['s3']):
        s=ST[t];a,b=s['s1'],s['s3']-s['s1']
        segs=''.join(f'<i class="p-{v[1].lower()}{" s1" if i==0 else ""}" style="width:{v[2]/s["tot"]*100:.2f}%"></i>' for i,v in enumerate(s['top3']))
        names=''.join(f'<span>{pz(v[1])}{e(v[0])} <em>{v[2]/s["tot"]*100:.0f}%</em></span>' for v in s['top3'])
        o.append(f'<div class="stb"><div class="stt">{nm(t)}<span><b>{s["s1"]:.0f}%</b> top 1 · <b>{s["s3"]:.0f}%</b> top 3</span></div>'
                 f'<div class="bar sbar">{segs}</div><div class="stn">{names}</div></div>')
    return ''.join(o)
# ---------- 8 Youth
YO=D.youth()
def m_youth():
    o=[head('Production by age','Share of starters\' points by player age '+('at season end' if _dt_os.environ.get('DT_PAST')=='1' else 'today')),'<div class="ylg"><span class="ay">25 and under</span><span class="ap">26–29</span><span class="ao">30+</span><span class="ad">DEF</span></div>']
    for t in sorted(TEAMS,key=lambda t:-YO[t]['pct'][0]):
        p=YO[t]['pct']
        o.append(f'<div class="stb"><div class="stt">{nm(t)}<span><b class="ay">{p[0]:.0f}%</b> · <b class="ap">{p[1]:.0f}%</b> · <b class="ao">{p[2]:.0f}%</b></span></div>'
                 f'<div class="bar ybar"><i class="y0" style="width:{p[0]:.2f}%"></i><i class="y1" style="width:{p[1]:.2f}%"></i><i class="y2" style="width:{p[2]:.2f}%"></i><i class="y3" style="width:{p[3]:.2f}%"></i></div></div>')
    return ''.join(o)
# ---------- 9 Ranks heatmap
HE=D.heat()
def m_heat():
    hd='<span></span>'+''.join(f'<span>W{w}</span>' for w in range(1,G+1))+'<span>Avg</span>'
    rows=[]
    for t in sorted(TEAMS,key=lambda t:sum(HE[t])):
        cells=''.join(f'<span class="hm r{r}">{r}</span>' for r in HE[t])
        rows.append(f'<div class="sxr"><span class="mxn">{e(SHORT[t])}</span>{cells}<span class="hav">{sum(HE[t])/G:.1f}</span></div>')
    return head('Weekly score rank','1 = highest score that week')+f'<div class="sxm hmx" style="--n:{G}"><div class="sxr sxhd">{hd}</div>{"".join(rows)}</div>'
# ---------- 10 Byes
BY=D.byes()
def m_byes():
    wk=list(range(NOW,15))
    hd='<span></span>'+''.join(f'<span>W{w}</span>' for w in wk)
    rows=[];notes=[]
    for t in D.PH:
        cells=''.join(f'<span class="bx b{min(len(BY[t][w]),3)}">{len(BY[t][w]) or "–"}</span>' for w in wk)
        rows.append(f'<div class="sxr"><span class="mxn">{e(SHORT[t])}</span>{cells}</div>')
        for w in wk:
            if len(BY[t][w])>=2:notes.append((w,t,BY[t][w]))
    HH=D._g('H');tone=lg.tone
    def opp(t,w):
        f=[x for x in D.FUT[t] if x[0]==w]
        if not f:return ''
        o=D.FROM_SHORT.get(f[0][1],f[0][1]);r=HH.index(o)+1
        return f'<small class="bop">vs <em class="{tone(r)}">{r}</em> {e(D.SHORT0.get(o,o))}</small>'
    nl=''.join(f'<div class="bnl"><span>Wk {w}</span><b class="bnt">{e(D.SHORT0.get(t,t))}{opp(t,w)}</b><i>{"".join(f'<span>{pz(p[2])}{e(p[3]+" DEF" if p[2]=="DEF" else p[1])}</span>' for p in ps)}</i></div>' for w,t,ps in sorted(notes))
    return head('Bye exposure','Core starters on bye each remaining week')+f'<div class="sxm bym" style="--n:{len(wk)}"><div class="sxr sxhd">{hd}</div>{"".join(rows)}</div>'+head('Two or more starters out','')+nl
# ---------- 11 Home / Road (starters' home or road games, Weeks 1..G, from hist.json)
import json as _json
def _hr_data():
    HS=_json.load(open(P+'hist.json',encoding='utf-8'));META=HS['m']
    RN={int(k):v for k,v in _json.load(open(P+'cmp_extra.json',encoding='utf-8'))['rn'].items()}
    tm={t:dict(h=0,r=0,lh=[0,0],lr=[0,0],ev=[0,0],ph=[],pr=[]) for t in TEAMS}
    pos={};starts=[]
    for w in sorted(HS['w'],key=int):
        if int(w)>G:continue
        byg={}
        for rid,v in HS['w'][w].items():byg.setdefault(v[0],[]).append((RN[int(rid)],v))
        for (ta,A),(tb,B) in byg.values():
            for t,X,O in ((ta,A,B),(tb,B,A)):
                h=r=0
                for sp in X[2].split(','):
                    pid,_,pj,act,o=sp.split('|')
                    if not o:continue  # starter on bye / no game
                    home=not o.startswith('@');pj=float(pj);act=float(act);ps=META[pid][0]
                    h+=home;r+=not home
                    (tm[t]['ph'] if home else tm[t]['pr']).append(act)
                    starts.append((home,ps,pj,act))
                tm[t]['h']+=h;tm[t]['r']+=r
                won=X[1]>O[1]
                k='lh' if h>r else 'lr' if r>h else 'ev'
                tm[t][k][0 if won else 1]+=1
    return tm,starts
HRT,HRS=_hr_data()
def _hrrec(a):return f'{a[0]}-{a[1]}'
def _pc(a):return f'{100*a[0]/(a[0]+a[1]):.0f}<small>%</small>' if a[0]+a[1] else '–'
def _avg(v):return sum(v)/len(v) if v else 0
def _hv(a,b,fmt='{:.1f}'):
    """home value / road value: the higher one bright and bold, the other muted"""
    f=lambda v:fmt.format(round(v,1)+0.0).replace('-','−') if abs(round(v,1))>=0.05 else fmt.format(0.0).replace('+','')
    return (f'<span class="sxv hx-n{" hi" if a>b+1e-9 else ""}">{f(a)}</span>',f'<span class="sxv hx-n{" hi" if b>a+1e-9 else ""}">{f(b)}</span>')
def _dv(d,fmt='{:+.1f}'):
    c='hx-h' if d>=0.05 else 'hx-r' if d<=-0.05 else ''
    t=fmt.format(d).replace("-","−") if c else '0.0'
    return f'<span class="sxv b hx-d {c}">{t}</span>'
def _split(h,r):
    return f'<span class="hx-bar"><i class="hx-bh" style="width:{100*h/(h+r):.2f}%"></i><i class="hx-br" style="width:{100*r/(h+r):.2f}%"></i></span>'
HT='<span class="hx-t hx-th">Home</span>';RT='<span class="hx-t hx-tr">Road</span>'
HXCSS=('.hx-t{display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;height:17px;padding:0 calc(5px - .06em) 1px 5px;border-radius:3px;'
       'font-family:var(--display);font-weight:700;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;line-height:1;vertical-align:middle}'
       '.hx-th{background:rgba(63,214,155,.14);color:#7fdcb6;box-shadow:inset 0 0 0 1px rgba(63,214,155,.5)}'
       '.hx-tr{background:rgba(150,160,255,.13);color:#b9c1ff;box-shadow:inset 0 0 0 1px rgba(150,160,255,.5)}'
       '.hx-lg{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin:2px 0 6px;font-size:12px;color:var(--steel)}.hx-lg span+.hx-t{margin-left:8px}'
       '.hx-bar{display:flex;height:6px;border-radius:3px;overflow:hidden;margin-top:6px;max-width:160px;background:var(--hair)}'
       '.hx-bar i{display:block;height:100%}.hx-bh{background:rgba(63,214,155,.75)}.hx-br{background:rgba(150,160,255,.7)}'
       '.hx-tb .sxhd span{display:flex;align-items:center;justify-content:flex-end}.hx-tb .sxhd span:first-child{justify-content:flex-start}'
       '.hx-tb .sxr>span:not(:first-child){text-align:right;justify-self:end}'
       '.hx-cn{color:var(--label)}.hx-tb .sxn{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;min-width:0}'
       '.hx-n{color:var(--steel);font-weight:500}.hx-n.hi{color:var(--chalk);font-weight:700}'
       '.hx-d.hx-h{color:#7fdcb6}.hx-d.hx-r{color:#b9c1ff}'
       '.hx-sum{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:4px 0 10px}'
       '.hx-card{display:grid;grid-template-columns:minmax(0,1fr) auto;min-width:0;grid-template-rows:auto auto;align-items:center;gap:6px 10px;padding:10px 12px;border:1px solid var(--hair);border-radius:8px;background:var(--ink)}'
       '.hx-card>.hx-t{grid-row:1;grid-column:1;justify-self:start}.hx-card>b{grid-row:1;grid-column:2;justify-self:end;font-family:var(--display);font-size:20px;font-weight:700;color:var(--chalk)}'
       '.hx-card>span.sxv{grid-row:2;grid-column:2;justify-self:end;font-family:var(--display);font-size:15px;font-weight:600;color:var(--label)}'
       '.hx-card>em{grid-row:2;grid-column:1;font-style:normal;font-size:12px;color:var(--steel);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}'
       '@media(max-width:389px){.hx-card{padding:10px 10px;column-gap:6px}.hx-card>em{font-size:11px}.hx-card>b{font-size:18px!important}}'
       '.hx-pl{display:inline-flex;align-items:center;gap:8px;white-space:nowrap}.hx-pl small{font-size:11px;color:var(--steel);font-variant-numeric:tabular-nums}'
       '.hx-all{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:17px;border-radius:3px;background:rgba(238,240,244,.09);font-family:var(--display);font-weight:700;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--chalk)}'
       '.hx-grp{display:grid;grid-template-columns:minmax(0,1fr) 102px 102px;column-gap:6px;margin:2px 0 2px;font-family:var(--display);font-weight:600;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--label)}'
       '.hx-grp span:not(:first-child){text-align:center;padding-bottom:4px;border-bottom:1px solid var(--line-strong,rgba(255,255,255,.14))}')
def m_homeroad():
    o=[head('Home / Road',f'Starters playing at home or on the road · Wk 1–{G} · starters on bye left out'),
       f'<div class="hx-lg">{HT}<span>home game</span>{RT}<span>road game</span></div>']
    # 1 league ranking by home share
    rows=[[nmb(t,_split(HRT[t]['h'],HRT[t]['r'])),f'<span class="sxv hx-cn">{HRT[t]["h"]}</span>',f'<span class="sxv hx-cn">{HRT[t]["r"]}</span>',
           f'<span class="sxv b">{100*HRT[t]["h"]/(HRT[t]["h"]+HRT[t]["r"]):.0f}<small>%</small></span>']
          for t in sorted(TEAMS,key=lambda t:(-HRT[t]['h']/(HRT[t]['h']+HRT[t]['r']),-HRT[t]['h']))]
    o.append(head('Most home starts','Ranked by share of starters playing at home'))
    o.append(table([('Team',''),(HT,'50px'),(RT,'50px'),('Home %','52px')],rows,'hx-tb'))
    # 2 record by lineup lean
    LH=[sum(HRT[t]['lh'][i] for t in TEAMS) for i in (0,1)];LR=[sum(HRT[t]['lr'][i] for t in TEAMS) for i in (0,1)];EV=[sum(HRT[t]['ev'][i] for t in TEAMS) for i in (0,1)]
    o.append(head('Record by lineup lean','Games where more starters were at home, or more on the road'+(f' · {sum(EV)} even split{"s" if sum(EV)!=1 else ""} left out' if sum(EV) else '')))
    o.append('<div class="hx-sum">'
             f'<div class="hx-card">{HT}<b class="sxv">{_hrrec(LH)}</b><span class="sxv">{_pc(LH)}</span><em>more at home</em></div>'
             f'<div class="hx-card">{RT}<b class="sxv">{_hrrec(LR)}</b><span class="sxv">{_pc(LR)}</span><em>more on road</em></div></div>')
    rows=[[nm(t),f'<span class="sxv">{_hrrec(HRT[t]["lh"])}</span>',f'<span class="sxv">{_hrrec(HRT[t]["lr"])}</span>'] for t in sorted(TEAMS,key=lambda t:-(HRT[t]['lh'][0]+HRT[t]['lr'][0]))]
    o.append(table([('Team',''),(HT,'64px'),(RT,'64px')],rows,'hx-tb'))
    # 3 scoring by position
    POS=list(lg.POS)
    def grp(f):
        hh=[x for x in HRS if x[0] and f(x)];rr=[x for x in HRS if not x[0] and f(x)];return hh,rr
    rows=[];rows2=[]
    for lab,f in [('All',lambda x:True)]+[(p_,lambda x,p_=p_:x[1]==p_) for p_ in POS]:
        hh,rr=grp(f)
        if not hh or not rr:continue
        tag=f'<span class="hx-pl">{"<b class=hx-all>All</b>" if lab=="All" else pz(lab)}<small>{len(hh)} · {len(rr)}</small></span>'
        ah,ar=_avg([x[3] for x in hh]),_avg([x[3] for x in rr])
        rows.append([tag,*_hv(ah,ar),_dv(ah-ar)])
        bh,br=100*sum(x[3]>x[2] for x in hh)/len(hh),100*sum(x[3]>x[2] for x in rr)/len(rr)
        vh,vr=_avg([x[3]-x[2] for x in hh]),_avg([x[3]-x[2] for x in rr])
        rows2.append([tag,*_hv(bh,br,'{:.0f}%'),*_hv(vh,vr,'{:+.1f}')])
    o.append(head('Points per start','Average points by position · small figures = home · road starts'))
    o.append(table([('Pos',''),(HT,'56px'),(RT,'56px'),('Diff','52px')],rows,'hx-tb hx-pt'))
    o.append(head('Against projection','Share of starts that beat the Sleeper projection, and average points over or under it'))
    o.append('<div class="hx-grp"><span></span><span>Beat proj</span><span>Pts vs proj</span></div>')
    o.append(table([('Pos',''),(HT,'48px'),(RT,'48px'),(HT,'48px'),(RT,'48px')],rows2,'hx-tb hx-pt hx-pj'))
    # 4 per team scoring
    rows=[]
    for t in sorted(TEAMS,key=lambda t:-(_avg(HRT[t]['ph'])-_avg(HRT[t]['pr']))):
        ah,ar=_avg(HRT[t]['ph']),_avg(HRT[t]['pr'])
        rows.append([nm(t),*_hv(ah,ar),_dv(ah-ar)])
    o.append(head('Points per start by team','Each team\'s starters at home and on the road · sorted by the gap'))
    o.append(table([('Team',''),(HT,'56px'),(RT,'56px'),('Diff','52px')],rows,'hx-tb'))
    return ''.join(o)
MODS=[('pos','Positions',None),('odds','Odds',m_odds),*([('drf','Draft',m_draft)] if 'pick' in next(iter(PS['teams'].values())) else []),('sch','Schedules',m_sched),('ew','Every week',m_everyweek),('trd','Trades',m_trades),('lu','Lineups',m_lineups),('prj','Projections',m_proj),
      ('mg','Margins',m_close),('cs','Consistency',m_cons),('st','Stars',m_stars),('yo','Age',m_youth),('rk','Ranks',m_heat),('by','Byes',m_byes),('hr','Home / Road',m_homeroad)]
if NOW>14:MODS=[m for m in MODS if m[0]!='by']  # regular season over: no byes ahead
def build():
    radios=''.join(f'<input type="radio" name="sxs" id="sx-{k}" class="lr"{" checked" if i==0 else ""}>' for i,(k,_,_) in enumerate(MODS))
    nav='<div class="lbc sxnav" role="tablist" aria-label="Stats">'+''.join(f'<label for="sx-{k}">{lab}</label>' for k,lab,_ in MODS)+'</div>'
    pans=''.join(f'<div class="sxp sxp-{k}">'+('POS_SECTION' if f is None else f'<section class="sxc">{f()}</section>')+'</div>' for k,_,f in MODS)
    css=''.join(f'#sx-{k}:checked~.sxnav label[for="sx-{k}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#sx-{k}:checked~.sxp-{k}{{display:block}}' for k,_,_ in MODS)
    css+=HXCSS+'.ssm{position:relative}.ssm .mx[data-w]{cursor:pointer;-webkit-tap-highlight-color:transparent}.ssm .mx.on{box-shadow:inset 0 0 0 1.5px var(--chalk)}.ssb{display:grid;grid-template-columns:minmax(0,1fr) auto auto;align-items:center;column-gap:14px;height:68px;margin:0 0 10px;padding:0 12px 0 14px;box-sizing:border-box;border-radius:8px;background:var(--ink);box-shadow:inset 0 0 0 1px var(--hair)}.ssb.on{box-shadow:inset 0 0 0 1px var(--line-strong)}.ssb .ssh{grid-column:1/-1;text-align:center;font-size:12.5px;font-weight:500;color:var(--dim)}.ssb .ssn,.ssb .ssw,.ssb .ssd{display:none}.ssb.on .ssh{display:none}.ssb.on .ssn,.ssb.on .ssw{display:flex}.ssb.on .ssd{display:inline-flex}.ssn{flex-direction:column;gap:4px;min-width:0}.ssn>*{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ssa{font-size:14.5px;font-weight:600;line-height:1.15;color:var(--chalk)}.ssn .sso{font-size:12px;font-weight:500;line-height:1.2;color:var(--steel);white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}.ssw{flex-direction:column;align-items:center;gap:4px}.ssw small{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;line-height:1;color:var(--dim)}.ssv{display:flex;align-items:baseline;gap:6px;font-family:var(--display);font-weight:700;font-variant-numeric:tabular-nums;line-height:1}.ssv i{font-style:normal}.ss0{font-size:16px;color:var(--steel)}.ssr{font-size:13px;color:var(--dim)}.ss1{font-size:20px;color:var(--chalk)}.ssb.own .ssr{display:none}.ssd{align-items:center;justify-content:center;min-width:46px;height:28px;padding:0 8px;box-sizing:border-box;border-radius:7px;font-family:var(--display);font-weight:700;font-size:15px;font-variant-numeric:tabular-nums;line-height:1;background:var(--hair);color:var(--steel)}.ssb.up .ssd{background:var(--win-bg);color:var(--win)}.ssb.dn .ssd{background:var(--loss-bg);color:var(--loss)}.ssb.own .ssd{font-family:var(--body);font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase}.ewm{position:relative}.ewm .mx[data-w]{cursor:pointer;-webkit-tap-highlight-color:transparent}.ewm .mx.on{box-shadow:inset 0 0 0 1.5px var(--chalk)}.ewb{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;column-gap:12px;height:42px;margin:0 0 10px;padding:0 12px;box-sizing:border-box;border-radius:8px;background:var(--ink);box-shadow:inset 0 0 0 1px var(--hair);font-size:13.5px;font-weight:600;line-height:1.2;color:var(--label)}.ewb .ewa,.ewb .ewo{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ewb .ewa{text-align:right}.ewb .ewo{text-align:left}.ewb .ewr{font-weight:500;font-size:12.5px;color:var(--dim);white-space:nowrap}.ewb.on{box-shadow:inset 0 0 0 1px var(--line-strong);color:var(--chalk)}.ewb.on .ewr{font-family:var(--display);font-weight:700;font-size:19px;letter-spacing:.02em;font-variant-numeric:tabular-nums;color:var(--chalk)}.sxm .sxr>span.ewd{background:var(--line-strong);opacity:.55}.ewl .sxr>span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}.ewl .sxr>span:nth-child(2){text-align:center}'+('.bnl .bnt{display:flex;flex-direction:column;gap:3px;white-space:nowrap;overflow:visible}'
      '.bnl .bop{font-size:11.5px;font-weight:500;color:var(--steel)}.bnl .bop em{font-style:normal;font-family:var(--display);font-weight:700;color:var(--label);margin:0 1px}'
      '.bnl .bop em{display:inline-flex;align-items:center;justify-content:center;width:20px;height:16px;padding-bottom:1px;box-sizing:border-box;margin:0 4px 0 3px;border-radius:3px;background:rgba(238,240,244,.08);font-size:11px;vertical-align:1px}'
      '.bnl .bop em.gold{color:#e8c15a;background:rgba(232,193,90,.14)}.bnl .bop em.g{color:var(--win);background:rgba(63,214,155,.12)}.bnl .bop em.b{color:#ff8a9a;background:rgba(255,93,115,.12)}'
      '.hm.r1{box-shadow:inset 0 0 0 1.5px #e8c15a}.hm.r10{box-shadow:inset 0 0 0 1.5px rgba(255,93,115,.85)}')
    return radios+nav+pans,css
if __name__=='__main__':
    h,c=build();open(P+'sx_section.html','w',encoding='utf-8').write(h);open(P+'sx_css.css','w',encoding='utf-8').write(c);print(len(h))
