import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Matchups section: one option per game this week (5). Each shows a side-by-side card for both teams,
# then a switch between the two teams' results so far and remaining schedule (with NFL bye counts from current rosters).
import json,re,html
P=__DTP__+''
import sys as _s0;_s0.path.insert(0,P);import lg
s=open(P+'data_block.js',encoding='utf-8').read()
g=lambda n:json.loads(re.search(r'const '+n+r'=(.*?);\n',s).group(1))
T,H,WK,FUT=g('T'),g('H'),g('WK'),g('FUT')
R=json.load(open(P+'rosters.json',encoding='utf-8'));BYE=json.load(open(P+'ro_ranks.json'))['_bye']
def norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip(); return {'RIPMFL':'Team RIPMFL'}.get(n,n)
R={norm(k):v for k,v in R.items()}
SHORT=dict(lg.SHORT)
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
FULL=dict(lg.FULL)
e=html.escape;DONE=len(WK[H[0]]);W=DONE+1
seed=lambda t:H.index(t)+1
tone=lg.tone
chip=lambda r:f'<i class="ch {tone(r)}"><span class="ct">#{r}</span></i>'
def rec(t):return f'{T[t][0]}-{T[t][1]}'
ORD=['QB','RB','WR','TE','K','DEF']
def byes(t,w):return sorted([p for p in R[t] if not p[7] and BYE.get(p[3])==w],key=lambda p:(ORD.index(p[2]),-p[4]))
def form(t,n=5):return ''.join(f'<i class="fm {"w" if x[2]>x[3] else "l"}"></i>' for x in WK[t][-n:])
# this week's games, ordered by the better seed in each game
FIN=not any(FUT.values())  # regular season over (a past season, or the playoffs): no current week, the latest week is a final
WT=DONE if FIN else W        # top of the week menu
games=[];seen=set()
for t in ([] if FIN else H):
    if t in seen: continue
    o=FULL[FUT[t][0][1]];assert FULL[FUT[o][0][1]]==t;seen|={t,o};games.append((t,o))
assert FIN or len(games)==lg.N//2
import sx_data as _SD
def card(a,b):
    def side(x,cl):
        bl=byes(x,W)
        lst=''.join(f'<div class="mbr"><i class="pp sm p-{p[2].lower()}"><span class="ct">{p[2]}</span></i><span>{e(p[1])}</span></div>' for p in bl) or '<div class="mbr none">None</div>'
        return (f'<div class="mus {cl}">{chip(seed(x))}<b>{e(x)}</b><span class="mrec">{rec(x)}</span><span class="mform">{form(x)}</span></div>',
                f'<div class="mbl {cl}">{lst}</div>')
    sa,ba=side(a,'msl');sb,bb=side(b,'msr')
    ma,mb,pw=_SD.simgame(a,b);pa=round(pw*100);pb=100-pa
    rows=[('Sim pts',f'{ma:.1f}',f'{mb:.1f}',ma,mb),('Sim win',f'{pa}%',f'{pb}%',pa,pb),
          ('PF / wk',f'{T[a][5]:.1f}',f'{T[b][5]:.1f}',T[a][5],T[b][5]),
          ('PF rank',f'#{T[a][4]}',f'#{T[b][4]}',-T[a][4],-T[b][4]),
          ('All-play',f'{T[a][10]}-{T[a][11]}',f'{T[b][10]}-{T[b][11]}',T[a][10],T[b][10]),
          ('Every-week H2H',*(lambda w,l:(f'{w}-{l}',f'{l}-{w}',w,l))(sum(p[2]>q[2] for p,q in zip(WK[a],WK[b])),sum(p[2]<q[2] for p,q in zip(WK[a],WK[b])))),
          ('Luck',f'{T[a][12]:+.2f}',f'{T[b][12]:+.2f}',None,None),
          ('On bye',str(len(byes(a,W))),str(len(byes(b,W))),-len(byes(a,W)),-len(byes(b,W))),
          (HRLAB,*[hrval(hr_count(LW['out'][str(RID[x])]['st']),hr_count(optimal(_rpool(LW['out'][str(RID[x])])))) for x in (a,b)],None,None)]
    cmp=''.join(f'<div class="mcr"><span class="{"up" if va is not None and va>vb else ""}">{x}</span><em>{l}</em><span class="{"up" if va is not None and vb>va else ""}">{y}</span></div>' for l,x,y,va,vb in rows)
    prev=[x for x in WK[a] if FULL[x[1]]==b]
    pv=''.join(f'<div class="mprev">Week {x[0]}: <b class="{"w" if x[2]>x[3] else "l"}">{e(a) if x[2]>x[3] else e(b)}</b> won {max(x[2],x[3]):.1f}–{min(x[2],x[3]):.1f}</div>' for x in prev)
    return (f'<div class="mcard"><div class="mch"><span>Week {W}</span></div>'
            f'<div class="mvs">{sa}<span class="mv2">vs</span>{sb}</div><div class="mcmp">{cmp}</div>{pv}<div class="mbys">{ba}{bb}</div></div>')
def sched(t):
    o=['<div class="msh"><span>Results</span></div>'];ww=wl=0
    for x in WK[t]:
        won=x[2]>x[3];ww+=won;wl+=not won;op=FULL[x[1]]
        tag='<i class="mt hi" title="Week high score">HI</i>' if x[4]==1 else '<i class="mt lo" title="Week low score">LO</i>' if x[4]==10 else ''
        o.append(f'<div class="mrow"><span class="mwk">Wk {x[0]}</span><i class="mres {"w" if won else "l"}"><span class="ct">{"W" if won else "L"}</span></i>'
                 f'<span class="mmid"><span class="mop"><span>{e(op)}</span><i class="mrc" title="Record going into Week {x[0]}">{_rw(op,x[0]-1)}</i>{tag}</span><span class="msc">{f"<b>{x[2]:.1f}</b><span>–</span>{x[3]:.1f}" if won else f"{x[2]:.1f}<span>–</span><b>{x[3]:.1f}</b>"}<i class="mdf {"w" if won else "l"}">{"+" if won else "−"}{abs(x[2]-x[3]):.1f}</i></span></span><span class="mrun">{ww}-{wl}</span></div>')
    o.append('<div class="msh"><span>Remaining</span></div>')
    for x in FUT[t]:
        op=FULL[x[1]];bl=len(byes(t,x[0]))
        bt=f'<i class="mby">{bl} on bye</i>' if bl else ''
        o.append(f'<div class="mrow fut{" now" if x[0]==W else ""}"><span class="mwk">Wk {x[0]}</span><i class="mres u"></i>'
                 f'<span class="mmid"><span class="mop">{chip(seed(op))}<span>{e(op)}</span></span><span class="mor">{rec(op)} · {T[op][5]:.1f} PF/wk</span></span>{bt}</div>')
    return ''.join(o)

# ---------- Lineups (Sleeper starters + projections, league scoring)
import sys as _s;_s.path.insert(0,P)
from nfl_colors import team_tiles, badge_c as _badge
from datetime import date as _d
LW=json.load(open(P+f'wk{W}.json'));DONEG=set(LW['done']);LIVEG=set(LW.get('live',[]));HOME=set(LW['home'])
_X=json.load(open(P+'cmp_extra.json',encoding='utf-8'));RID={v:int(k) for k,v in _X['rn'].items()};RN2={int(k):v for k,v in _X['rn'].items()}
_K=json.load(open(P+'ro_ranks.json'));_K.pop('_bye',None);_PG=json.load(open(P+'ro_pg.json'))
# Opponent in the game line ("@ NYJ", "vs CLE"): show the team logo when pipeline/logos/{CODE}.png|svg|webp exists
# (same files rebuild.py embeds as CSS for the .nfl.tm badges); otherwise keep the plain text code.
_NICK={'ARI':'Cardinals','ATL':'Falcons','BAL':'Ravens','BUF':'Bills','CAR':'Panthers','CHI':'Bears','CIN':'Bengals','CLE':'Browns',
'DAL':'Cowboys','DEN':'Broncos','DET':'Lions','GB':'Packers','HOU':'Texans','IND':'Colts','JAX':'Jaguars','KC':'Chiefs',
'LV':'Raiders','LAC':'Chargers','LAR':'Rams','MIA':'Dolphins','MIN':'Vikings','NE':'Patriots','NO':'Saints','NYG':'Giants',
'NYJ':'Jets','PHI':'Eagles','PIT':'Steelers','SF':'49ers','SEA':'Seahawks','TB':'Buccaneers','TEN':'Titans','WAS':'Commanders'}
_LOGOS={f.rpartition('.')[0] for f in (_dt_os.listdir(P+'logos') if _dt_os.path.isdir(P+'logos') else []) if f.rpartition('.')[2].lower() in('svg','png','webp')}
HATILE=False  # (old) vertical HOME / ROAD strip beside the points; home/road is now the vs / @ tile in the game line
def _hax(p):
    """'vs' (home) / '@' (road) for a lineup entry, '' when the player has no game"""
    if not p or not p[6]:return ''
    return ((p[9] if len(p)>9 else ('vs' if p[3] in HOME else '@')) or '').strip()
HRLAB='<span class="hrt hrt-h">Home</span><i class="hrd">·</i><span class="hrt hrt-r">Road</span>'
def _hrv(c):
    h,r_=c;return f'<b class="hrn{" hi" if h>r_ else ""}">{h}</b><i class="hrd">·</i><b class="hrn{" hi" if r_>h else ""}">{r_}</b>'
def hrval(c,co=None):
    """home · road count for the actual lineup; with co, the optimal lineup's count too (shown when Optimal is picked)"""
    if co is None:return _hrv(c)
    return f'<span class="hrv-a">{_hrv(c)}</span><span class="hrv-o">{_hrv(co)}</span>'
def _rpool(X):return X['st']+[p for p in X['bn'] if _TAG.get(p[0],'') not in('IR','TX') and (p[4]>0 or p[5]!=0)]
def hr_count(st):
    hs=[_hax(p) for p in st if p];return sum(x=='vs' for x in hs),sum(x=='@' for x in hs)
def _gline(ha,opp):
    ha=(ha or '').strip()
    if not opp:return ha
    if False and HATILE and ha in('vs','@'):
        tile=f'<span class="hat {"h" if ha=="vs" else "r"}" title="{"Home" if ha=="vs" else "Road"}">{"H" if ha=="vs" else "R"}</span>'
        if opp in _LOGOS and opp in _NICK:
            lab=('at ' if ha=='@' else 'vs ')+_NICK[opp]
            return f'{tile}<em class="nfl opp n-{opp}" role="img" aria-label="{lab}" title="{lab}"><span class="ct">{opp}</span></em>'
        return tile+opp
    # home game: green "vs" tile; road game: blue "@" tile (same colours as the HOME / ROAD tiles)
    pre=(f'<span class="gha ht {"h" if ha=="vs" else "r"}" title="{"Home" if ha=="vs" else "Road"}">{ha}</span>' if ha in('vs','@') else
         f'<span class="gha" aria-hidden="true">{ha}</span>' if ha else '')
    if opp not in _LOGOS or opp not in _NICK:return pre+opp
    lab=('at ' if ha=='@' else 'vs ' if ha else '')+_NICK[opp]
    return f'{pre}<em class="nfl opp n-{opp}" role="img" aria-label="{lab}" title="{lab}"><span class="ct">{opp}</span></em>'
_TAG={p[0]:p[7] for t in R for p in R[t]}
def _age(pid):
    b=_X['age'].get(pid)
    if not b:return None
    y,m,dd=map(int,b.split('-'));return (_d.today()-_d(y,m,dd)).days/365.25
SLOTS=[lg.SLAB.get(x,x) for x in lg.SLOTS]
INJ={'Questionable':'Q','Doubtful':'D','Out':'O','IR':'IR'}
from statline import statline as _sl, fumbles as _fl, fumbles_kept as _fk, detail as _dx
def lval(p):
    done=p[8] if len(p)>8 else p[3] in DONEG
    return (p[5],True) if done else (p[4],False)
def _when(p,done):
    """second-line game status: Final, Live, or kickoff day and time (ET)"""
    if done:return 'Final'
    w=p[10] if len(p)>10 else W
    if w==W and p[3] in LIVEG:return 'Live'
    k=json.load(open(P+'kick.json')).get(str(w),{}).get(p[3]) if '_KJ' not in globals() else _KJ.get(str(w),{}).get(p[3])
    if not k:return 'TBD'
    from zoneinfo import ZoneInfo;from datetime import datetime
    d=datetime.fromisoformat(k[0]).astimezone(ZoneInfo('America/New_York'))
    t=f'{d.hour%12 or 12}'+(f':{d.minute:02d}' if d.minute else '')+(' PM' if d.hour>=12 else ' AM')
    if d.hour>=19 and d.weekday() in (0,3,6):return {0:'MNF',3:'TNF',6:'SNF'}[d.weekday()]
    return t if d.weekday()==6 else f'{d:%a} {t}'
_KJ=json.load(open(P+'kick.json'))
def _dif(a,j):
    d=round(a-j,1);return ('+' if d>=0 else '−')+f'{abs(d):.1f}'  # points vs projection, on the FINAL tile
def lcell(p,side):
    if p is None:return f'<span class="cn {side}"></span><span class="cv {side}"></span>'
    pid,pos,name,tm,proj,act,opp,inj=p[:8]
    r=_K[pid][0] if _K.get(pid) and _K[pid][2]>0 else None
    big=r and (r>=100 or (pos=='DEF' and r>=10))
    g=(_PG.get(pid) or [None])[0]  # points-per-game rank (players with 3+ games)
    big3=lambda x:x and (x>=100 or (pos=='DEF' and x>=10))
    rk=(f'<b class="rkt{" b3" if big3(r) else ""}">{r}</b>' if r else '<b class="rkt"></b>')+(f'<b class="rkg{" b3" if big3(g) else ""}">{g}</b>' if g else '<b class="rkg"></b>')
    sq=f'<i class="pq p-{pos.lower()} t-{tm or "FA"}"><span class="pqi"><span>{pos}</span>{rk}</span></i>'
    a=_age(pid);acl='ay' if a and a<27 else 'ap' if a and a<31 else 'ao'
    ag=f'<em class="pag {acl}">{a:.1f}</em>' if a else ''
    nm=name.split(' ')[-1] if pos!='DEF' else name.split(' ')[-1]
    if nm in('Jr.','Sr.','II','III','IV'):nm=name.split(' ')[-2]
    if pos!='DEF' and len(name.split(' '))>2 and name.split(' ')[-2]=='St.':nm='St. '+nm
    ij=f'<i class="inj i-{INJ[inj]}">{INJ[inj]}</i>' if inj in INJ else ''
    _f=_fl(p[10] if len(p)>10 else W,pid,pos) if lval(p)[1] else 0
    _k=_fk(p[10] if len(p)>10 else W,pid) if lval(p)[1] and pos not in('K','DEF') else 0
    _fl_=f'<i class="flg">{_f if _f>1 else ""}FL</i>' if _f else ''  # lost fumble (red)
    _fk_=f'<i class="flg fk">{_k if _k>1 else ""}FK</i>' if _k else ''  # fumble kept by the offense (grey, no points lost)
    flg=(f'<span class="flgs">{_fl_}{_fk_}</span>' if _f and _k else _fl_ or _fk_)
    v,done=lval(p)
    ha=_gline((p[9] if len(p)>9 else ('vs' if tm in HOME else '@')),opp)
    # finished games: the points tile already says FINAL, so the game line is just home/away + opponent
    st='BYE' if not opp else ha if done else f'{ha}<i class="gsep">·</i><span class="gwhen">{_when(p,done)}</span>'
    mk=_badge(tm).replace('<em class="nfl','<em class="nfl tm',1) if tm else ''
    cur=(p[10] if len(p)>10 else W)==W and tm and opp  # current week, has a game: the page's live updater may patch it
    dp=f' data-p="{pid}" data-j="{proj:.2f}"' if cur else ''
    dt=f' data-t="{tm}"' if cur else ''
    hb=''
    if HATILE and opp and _hax(p) in('vs','@'):  # playoffs: vertical HOME / ROAD strip on the inner edge, next to the points
        wd="HOME" if _hax(p)=="vs" else "ROAD"
        hb=f'<i class="hab {"hab-h" if _hax(p)=="vs" else "hab-r"}" aria-label="{wd.title()}">'+''.join(f'<span>{c}</span>' for c in wd)+'</i>'
    return (f'<span class="cn {side}{" hbx" if hb else ""}">{sq}{flg}<span class="cnm"><b><span>{e(nm)}</span>{mk}{ij}</b>'
            f'<small><span class="gp{" fin" if done else ""}"{dt}>{st}</span></small></span>{hb}</span>'+
            (f'<span class="cv {side} act"{dp}><span class="fs {"up" if act>=proj else "dn"}" title="Projected {proj:.1f}"><em class="fdf">{_dif(act,proj)}</em>{v:.1f}<small>FINAL</small></span></span>' if done else f'<span class="cv {side} pjc"{dp}><span class="fs pj"><em class="fdf"></em>{v:.1f}<small>PROJ</small></span></span>'))
def lrow(pa,pb,slot):
    w=''
    if pa and pb:
        va,vb=lval(pa)[0],lval(pb)[0];w=' wa' if va>vb+1e-9 else ' wb' if vb>va+1e-9 else ''
    def sl(p,side):
        if p and not lval(p)[1] and (p[10] if len(p)>10 else W)==W and p[6]:return f'<span class="slz sl{side}" data-sp="{p[0]}" data-pos="{p[1]}"></span>'
        if not p or not lval(p)[1]:return ''
        t=_sl(p[10] if len(p)>10 else W,p[0],p[1])
        return f'<span class="sln sl{side}">{t}</span>' if t else ''
    def dx(p,side):
        if not p or not lval(p)[1]:return ''
        t=_dx(p[10] if len(p)>10 else W,p[0],p[1])
        return f'<span class="sdx sdx{side}">{t}</span>' if t else ''
    return f'<div class="cr lu{w}">{lcell(pa,"a")}{lcell(pb,"b")}{sl(pa,"a")}{sl(pb,"b")}{dx(pa,"a")}{dx(pb,"b")}</div>'

def optimal(pool):return lg.optimal(pool,pos=lambda p:p[1],pts=lambda p:lval(p)[0])

# ---------- slate view: group starters by kickoff window (ET)
from zoneinfo import ZoneInfo as _Z
from datetime import datetime as _dt
KICK=json.load(open(P+'kick.json'))
_PO={'QB':0,'RB':1,'WR':2,'TE':3,'K':4,'DEF':5}
def _slate(w,tm):
    if str(w) not in KICK:return ('8','TBD'),'Kickoff TBD'
    k=KICK.get(str(w),{}).get(tm)
    if not k:return None
    d=_dt.fromisoformat(k[0]).astimezone(_Z('America/New_York'))
    late=d.weekday()==6 and 15<=d.hour<17
    key=(d.date().isoformat(),'16:00' if late else f'{d.hour:02d}:{d.minute:02d}')
    t='4 PM' if late else (d.strftime('%-I:%M %p').replace(':00 ',' '))
    return key,f'{d:%a} {t}'
def _pw(p):return p[10] if len(p)>10 else W
def sview(sa,sb,sid_a=None,sid_b=None):
    """Starters grouped by slate. sa/sb: player lists (None allowed). Shows per-slate actual (projected) and running totals."""
    groups={}
    for side,L in (('a',sa),('b',sb)):
        for p in L:
            if not p:continue
            s=_slate(_pw(p),p[3]);k=s[0] if s else ('9','~');lab=s[1] if s else 'No game'
            g=groups.setdefault(k,{'lab':lab,'a':[],'b':[]});g[side].append(p)
    o=[];ca=cb=pa=pb=0.0;strip=[];rda=[0.0,False];rdb=[0.0,False]
    # Needs over projection, on every slate: going into the slate, how far the trailing team's starters from this slate on
    # must beat their projections to catch up, if the leader's do exactly theirs. Earlier slates count actual scores (live:
    # max(actual, projection)). Filled for finished slates and the next one to finish; later slates keep an empty line.
    def _ev(p):
        if lval(p)[1]:return p[5]
        if p[3] in LIVEG and _pw(p)==W:return max(p[4],p[5])
        return p[4]
    KS=sorted(groups)
    nxt=next((k for k in KS if groups[k]['lab']!='No game' and not all(lval(p)[1] for p in groups[k]['a']+groups[k]['b'])),None)
    upto=KS.index(nxt) if nxt is not None else len(KS)-1
    def need_row(ki):
        cell=['','']
        if ki<=upto:
            ea=sum(_ev(p) for k2 in KS[:ki] for p in groups[k2]['a'])+sum(p[4] for k2 in KS[ki:] for p in groups[k2]['a'])
            eb=sum(_ev(p) for k2 in KS[:ki] for p in groups[k2]['b'])+sum(p[4] for k2 in KS[ki:] for p in groups[k2]['b'])
            tr=0 if ea<eb-0.05 else 1 if eb<ea-0.05 else None
            if tr is not None:
                cell[tr]=f'<i class="dlt dn">+{abs(ea-eb):.1f}</i>' if any(groups[k2]['ab'[tr]] for k2 in KS[ki:]) else '–'
        return f'<div class="mcr slc sltw"><span>{cell[0]}</span><em>Needs over proj</em><span>{cell[1]}</span></div>'
    for ki,k in enumerate(KS):
        g=groups[k]
        for sd in 'ab':g[sd].sort(key=lambda p:(_PO.get(p[1],9),-p[4]))
        done=[lval(p)[1] for p in g['a']+g['b']]
        st='Final' if all(done) else ('Live' if any(done) else 'Upcoming')
        if g['lab']=='No game':st='Bye'
        xa=sum(p[5] for p in g['a'] if lval(p)[1]);xb=sum(p[5] for p in g['b'] if lval(p)[1])
        ja=sum(p[4] for p in g['a']);jb=sum(p[4] for p in g['b'])
        ca+=xa;cb+=xb;pa+=ja;pb+=jb
        da=[p for p in g['a'] if lval(p)[1]];db=[p for p in g['b'] if lval(p)[1]]
        sda=sum(p[5]-p[4] for p in da) if da else None;sdb=sum(p[5]-p[4] for p in db) if db else None
        if sda is not None:rda[0]+=sda;rda[1]=True
        if sdb is not None:rdb[0]+=sdb;rdb[1]=True
        started=st in('Final','Live')
        def dl(v):
            if v is None:return ''
            c='up' if v>=0.05 else 'dn' if v<=-0.05 else 'ev'
            return f'<i class="dlt {c}">{"+" if v>=0.05 else "−" if v<=-0.05 else "±"}{abs(v):.1f}</i>'
        fa=lambda x,j:(f'{x:.1f}' if started else '–')+f' <small>({j:.1f})</small>'
        o.append(f'<div class="slx sx-{st.lower()}"><div class="slg"><b>{g["lab"]}</b><em>{len(g["a"])}<u>·</u>{len(g["b"])} starters</em><i class="ss {st.lower()}">{st}</i></div><div class="mcr slh"><span class="{"up" if started and xa>xb else ""}">{fa(xa,ja)}{dl(sda)}</span><em>Slate</em><span class="{"up" if started and xb>xa else ""}">{dl(sdb)}{fa(xb,jb)}</span></div>'
                 f'<div class="mcr slc"><span>{ca:.1f} <small>({pa:.1f})</small>{dl(rda[0] if rda[1] else None)}</span><em>Running total</em><span>{dl(rdb[0] if rdb[1] else None)}{cb:.1f} <small>({pb:.1f})</small></span></div>'+need_row(ki))
        for i in range(max(len(g['a']),len(g['b']))):
            x=g['a'][i] if i<len(g['a']) else None;y=g['b'][i] if i<len(g['b']) else None;r=lrow(x,y,'')
            if sid_a is not None and x and x[0] not in sid_a:r=r.replace('<span class="cn a">','<span class="cn a swp">',1)
            if sid_b is not None and y and y[0] not in sid_b:r=r.replace('<span class="cn b">','<span class="cn b swp">',1)
            o.append(r)
        o.append('</div>')
        strip.append(f'<span class="stc {st.lower()}"><b>{g["lab"].split(" ",1)[0]}</b><i>{g["lab"].split(" ",1)[1] if " " in g["lab"] else ""}</i><em>{len(g["a"])}<u>·</u>{len(g["b"])}</em></span>')
    return '<div class="lsv"><div class="stl">'+''.join(strip)+'</div>'+''.join(o)+'</div>'
VSW='<div class="lvw pseg" role="group" aria-label="Lineup order"><label for="lv-p">Position</label><label for="lv-s">Slate</label></div>'
LSW='<div class="lsw pseg" role="group" aria-label="Lineup"><label for="lo-a">Actual</label><label for="lo-o">Optimal</label></div>'
LDW='<div class="ldw pseg" role="group" aria-label="Stats"><label for="ld-l">Lean</label><label for="ld-d">Detailed</label></div>'
RKW='<div class="lrw pseg" role="group" aria-label="Position rank by"><label for="rk-t">Pts</label><label for="rk-g">/ Gm</label></div>'
LCW='<div class="lcw pseg" role="group" aria-label="Tile colors"><label for="lc-p">Position</label><label for="lc-t">Team</label></div>'
def CTL(rows):
    """lineup switches in one grid: switch | its title | title | switch per row, titles meeting in the middle"""
    return '<div class="lctl lgrid">'+''.join(f'{a}<i class="lt">{ta}</i><i class="lt ltr">{tb}</i>{b}' for a,ta,tb,b in rows)+'</div>'
def ptsrow(sa,sb,big=True,ra=None,rb=None):
    """Points (projected): tally of players whose game has started, '–' if none; original projection in brackets."""
    sa=[p for p in sa if p];sb=[p for p in sb if p]
    pl=lambda X:any(lval(p)[1] or (p[3] in LIVEG and (len(p)<11 or p[10]==W)) or p[5]!=0 for p in X)
    va,vb=sum(p[5] for p in sa),sum(p[5] for p in sb);a_,b_=pl(sa),pl(sb)
    pa,pb=sum(p[4] for p in sa),sum(p[4] for p in sb)
    fa=f'{va:.1f}' if a_ else '–';fb=f'{vb:.1f}' if b_ else '–'
    ua=big and (a_ or b_) and va>vb;ub=big and (a_ or b_) and vb>va
    da=f' data-r="{ra}"' if ra else '';db=f' data-r="{rb}"' if rb else ''
    return (f'<div class="mcr {"ltot" if big else "ltot2"}"><span class="{"up" if ua else ""}"{da}><b class="lt-v">{fa}</b> <small>({pa:.1f})</small></span>'
            f'<em>Points <i class=pj>(projected)</i></em><span class="{"up" if ub else ""}"{db}><small>({pb:.1f})</small> <b class="lt-v">{fb}</b></span></div>')
BH_CUR='<div class="msh lbh">Bench<small>active players with a game</small></div>'
BH_HIST='<div class="msh lbh">Bench<small>points left on the bench</small></div>'
def optblock(sa,sb,pool_a,pool_b,ta,tb,proj=False,bhead='',bkeep=lambda p:True,bsl=''):
    oa,ob=optimal(pool_a),optimal(pool_b)
    sid_a={p[0] for p in sa};sid_b={p[0] for p in sb}
    va=sum(lval(p)[0] for p in oa if p);vb=sum(lval(p)[0] for p in ob if p)
    lab='Optimal'
    flip=(va>vb)!=(ta>tb)
    sg=lambda d:('+' if d>=0 else '−')+f'{abs(d):.1f}'
    res=f'<div class="mcr ltot2"><span>{sg(va-ta)}</span><em>Points gained</em><span>{sg(vb-tb)}</span></div>'
    o=[f'<div class="mcr ltot"><span class="{"up" if va>vb else ""}">{va:.1f}</span><em>{lab}</em><span class="{"up" if vb>va else ""}">{vb:.1f}</span></div>',
       ptsrow(sa,sb,False),res]
    o.append('<div class="lpv">')
    for x,y in zip(oa,ob):
        r=lrow(x,y,'')
        if x and x[0] not in sid_a:r=r.replace('<span class="cn a">','<span class="cn a swp">',1)
        if y and y[0] not in sid_b:r=r.replace('<span class="cn b">','<span class="cn b swp">',1)
        o.append(r)
    sv=sview([x for x in oa if x],[y for y in ob if y],sid_a,sid_b)
    o.append('</div>'+sv)
    oid_a={p[0] for p in oa if p};oid_b={p[0] for p in ob if p}
    ba=sorted([p for p in pool_a if p[0] not in oid_a and (bkeep(p) or p[0] in sid_a)],key=lambda p:-lval(p)[0])
    bb=sorted([p for p in pool_b if p[0] not in oid_b and (bkeep(p) or p[0] in sid_b)],key=lambda p:-lval(p)[0])
    if ba or bb:
        o.append(bhead)
        o+=[lrow(ba[k] if k<len(ba) else None,bb[k] if k<len(bb) else None,bsl) for k in range(max(len(ba),len(bb)))]
    return '<div class="lus-o">'+''.join(o)+'</div>'
def lineups(a,b):
    A,B=LW['out'][str(RID[a])],LW['out'][str(RID[b])]
    tot=lambda X:sum(lval(p)[0] for p in X['st'])
    sc=lambda X:sum(p[5] for p in X['st'])
    ta,tb=tot(A),tot(B)
    oa_,ob_=sum(p[4] for p in A['st']),sum(p[4] for p in B['st'])
    hdr=f'<div class="msh lsh">Lineups</div>{CTL([(VSW,'Order','Lineup',LSW),(LDW,'Stats','Rank',RKW),(LCW,'Colors','','')])}<div class="lnote">boxed = final · grey = projected</div>'
    o=[ptsrow(A['st'],B['st'],True,RID[a],RID[b])]
    o+=['<div class="lpv">']+[lrow(pa,pb,sl if sl!='FLEX' else 'FLX') for pa,pb,sl in zip(A['st'],B['st'],SLOTS)]+['</div>',sview(A['st'],B['st'])]
    keep=lambda p:_TAG.get(p[0],'')=='' and p[4]>0 or (p[3] in DONEG and p[5]>0)
    bn=lambda X:sorted([p for p in X['bn'] if keep(p)],key=lambda p:-lval(p)[0])
    ba,bb=bn(A),bn(B)
    if ba or bb:
        o.append(BH_CUR)
        for k in range(max(len(ba),len(bb))):
            o.append(lrow(ba[k] if k<len(ba) else None,bb[k] if k<len(bb) else None,'BN'))
    pool=lambda X:X['st']+[p for p in X['bn'] if _TAG.get(p[0],'') not in('IR','TX') and (p[4]>0 or p[5]!=0)]
    return '<div class="lus">'+hdr+'<div class="lus-a">'+''.join(o)+'</div>'+optblock(A['st'],B['st'],pool(A),pool(B),ta,tb,True,BH_CUR,keep,'BN')+'</div>'
def panel(i,a,b):
    return (f'<div class="mup mup-{i}">{card(a,b)}{lineups(a,b)}'
            f'<input type="radio" name="mt{i}" id="mt{i}a" class="lr msa" checked><input type="radio" name="mt{i}" id="mt{i}b" class="lr msb">'
            f'<div class="msw"><label for="mt{i}a">{e(a)}</label><label for="mt{i}b">{e(b)}</label></div>'
            f'<div class="msch msch-a">{sched(a)}</div><div class="msch msch-b">{sched(b)}</div></div>')
radios=''.join(f'<input type="radio" name="mus" id="mu-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(lg.N//2))
def _rw(t,w):
    g=WK[t][:w];return f'{sum(x[2]>x[3] for x in g)}-{sum(x[2]<x[3] for x in g)}'
def streak(t,upto=None):
    g=WK[t][:upto] if upto else WK[t];res=['W' if x[2]>x[3] else 'L' for x in g]
    if not res:return ''
    k=1
    while k<len(res) and res[-k-1]==res[-1]:k+=1
    return f'{res[-1]}{k}'
def nmx(t):
    full=e(SHORT[t]);sh=e(SHORT0.get(t,t))
    return f'<span class="nf">{full}</span><span class="ns">{sh}</span>'
def prow_(fr,a,b,ra,rb,ta,tb,va,vb,final=False,ca='',cb='',pa=None):
    """one game in the picker, full width, teams stacked: rank, name, record, streak (or result), sim win % (this
    week only), score"""
    ua,ub=(va>vb,vb>va) if final else (False,False)
    line=lambda t,r,tg,v,hi,rc,pw:(f'<span class="pr2"><em class="mrk {tone(r) if not final else ""}">{r}</em><b>{nmx(t)}</b><span class="prc">{rc}</span>'
                             f'<i class="stk {tg[:1].lower()}">{tg}</i>'+(f'<span class="pwp{" hi" if pw>50 else ""}" title="Sim win chance">{pw}%</span>' if pw is not None else '')+
                             f'<span class="sc{" hi" if hi else ""}">{v:.1f}</span></span>')
    return f'<label for="{fr}"{" class=fin" if final else ""}>{line(a,ra,ta,va,ua,ca,pa)}<i class="dv"></i>{line(b,rb,tb,vb,ub,cb,None if pa is None else 100-pa)}</label>'
_cur=lambda t:sum(lval(p)[0] for p in LW['out'][str(RID[t])]['st'])
chips='<div class="mpk muc2" role="tablist" aria-label="Game">'+''.join(prow_(f'mu-{i}',a,b,seed(a),seed(b),streak(a),streak(b),_cur(a),_cur(b),False,rec(a),rec(b),round(_SD.simgame(a,b)[2]*100)) for i,(a,b) in enumerate(games))+'</div>'
cur='' if FIN else f'<div class="mwx mwx-{W}">'+radios+chips+''.join(panel(i,a,b) for i,(a,b) in enumerate(games))+'</div>'
css=''.join(f'#mu-{i}:checked~.muc2 label[for="mu-{i}"]{{border-color:var(--chalk);box-shadow:inset 0 0 0 1px var(--chalk)}}#mu-{i}:checked~.mup-{i}{{display:block}}' for i in range(lg.N//2))
# ---------- historical weeks
HS=json.load(open(P+'hist.json'));META=HS['m']
def hp(sp,inj=None):
    pid,tm,proj,act,o=sp.split('|');pos,name=META[pid]
    ha='@' if o.startswith('@') else 'vs';opp=o.lstrip('@') or None
    return [pid,pos,name,tm,float(proj),float(act),opp,inj,True,ha,HW[0]]
def hlineups(A,B):
    sa=[hp(x) for x in A[2].split(',')];sb=[hp(x) for x in B[2].split(',')]
    ta,tb=A[1],B[1];pa,pb=sum(x[4] for x in sa),sum(x[4] for x in sb)
    hdr=f'<div class="msh lsh">Lineups</div>{CTL([(VSW,'Order','Lineup',LSW),(LDW,'Stats','Rank',RKW),(LCW,'Colors','','')])}<div class="lnote">green = beat projection · red = fell short</div>'
    o=[ptsrow(sa,sb)]
    o+=['<div class="lpv">']+[lrow(x,y,'') for x,y in zip(sa,sb)]+['</div>',sview(sa,sb)]
    ba=sorted([hp(x) for x in A[3].split(',') if x],key=lambda q:-q[5]);bb=sorted([hp(x) for x in B[3].split(',') if x],key=lambda q:-q[5])
    if ba or bb:
        o.append(BH_HIST)
        o+=[lrow(ba[k] if k<len(ba) else None,bb[k] if k<len(bb) else None,'') for k in range(max(len(ba),len(bb)))]
    return '<div class="lus">'+hdr+'<div class="lus-a">'+''.join(o)+'</div>'+optblock(sa,sb,sa+ba,sb+bb,ta,tb,False,BH_HIST)+'</div>'
def hcard(w,a,b,A,B):
    xa=WK[a][w-1];xb=WK[b][w-1]
    side=lambda x,X,cl,won:(f'<div class="mus {cl}"><span class="hres {"w" if won else "l"}">{"WON" if won else "LOST"}</span><b>{e(x)}</b>'
        f'<span class="hsc">{X[1]:.1f}</span><span class="hrk">Week rank <i class="ch {tone(xa[4] if x==a else xb[4])}"><span class="ct">#{xa[4] if x==a else xb[4]}</span></i></span></div>')
    wa=A[1]>B[1]
    return (f'<div class="mcard"><div class="mch"><span>Week {w} · Final</span></div>'
            f'<div class="mvs">{side(a,A,"msl",wa)}<span class="mv2">vs</span>{side(b,B,"msr",not wa)}</div>'
            f'<div class="hmar">Margin <b>{abs(A[1]-B[1]):.1f}</b></div></div>')
hist=''
HW=[0]
for w in range(DONE,0,-1):
    HW[0]=w
    R2=HS['w'][str(w)];byg={}
    for rid,v in R2.items():byg.setdefault(v[0],[]).append(int(rid))
    gl=[]
    for mid in sorted(byg):
        r1,r2=byg[mid];a,b=RN2[r1],RN2[r2]
        if H.index(b)<H.index(a):a,b=b,a
        gl.append((a,b))
    gl.sort(key=lambda g:H.index(g[0]))
    hr=''.join(f'<input type="radio" name="hw{w}" id="hw{w}-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(lg.N//2))
    _hx=lambda t:WK[t][w-1]
    hc=f'<div class="mpk hwc{w}" role="tablist">'+''.join(prow_(f'hw{w}-{i}',a,b,_hx(a)[4],_hx(b)[4],'W' if R2[str(RID[a])][1]>R2[str(RID[b])][1] else 'L','W' if R2[str(RID[b])][1]>R2[str(RID[a])][1] else 'L',R2[str(RID[a])][1],R2[str(RID[b])][1],True,_rw(a,w),_rw(b,w)) for i,(a,b) in enumerate(gl))+'</div>'
    hpn=''.join(f'<div class="mup hwp{w}-{i}">{hcard(w,a,b,R2[str(RID[a])],R2[str(RID[b])])}{hlineups(R2[str(RID[a])],R2[str(RID[b])])}</div>' for i,(a,b) in enumerate(gl))
    hist+=f'<div class="mwx mwx-{w}">'+hr+hc+hpn+'</div>'
    css+=''.join(f'#hw{w}-{i}:checked~.hwc{w} label[for="hw{w}-{i}"]{{border-color:var(--chalk);box-shadow:inset 0 0 0 1px var(--chalk)}}#hw{w}-{i}:checked~.hwp{w}-{i}{{display:block}}' for i in range(lg.N//2))
wr=''.join(f'<input type="radio" name="mwk" id="mw-{w}" class="lr"{" checked" if w==WT else ""}>' for w in range(1,WT+1))
dd=('<details class="dd wdd"><summary>'+''.join(f'<span class="sv wsv-{w}">Week {w}</span>' for w in range(1,WT+1))+
    '<svg viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></summary>'
    '<div class="ddm">'+''.join(f'<label for="mw-{w}"><i>{"Now" if w==W else "Final"}</i>Week {w}</label>' for w in range(WT,0,-1))+'</div></details>')
sec=('<section class="mux" aria-labelledby="muh">'+'<input type="radio" name="lcol" id="lc-p" class="lr" checked><input type="radio" name="lcol" id="lc-t" class="lr"><input type="radio" name="lopt" id="lo-a" class="lr" checked><input type="radio" name="lopt" id="lo-o" class="lr"><input type="radio" name="lview" id="lv-p" class="lr" checked><input type="radio" name="lview" id="lv-s" class="lr"><input type="radio" name="ldet" id="ld-l" class="lr" checked><input type="radio" name="ldet" id="ld-d" class="lr"><input type="radio" name="lrank" id="rk-t" class="lr" checked><input type="radio" name="lrank" id="rk-g" class="lr">'+wr+f'<div class="posh"><b id="muh">Matchups</b><span id="mlive" class="mlive" data-w="{W}" hidden></span>{dd}</div>'+cur+hist+'</section>')
css+=''.join(f'#mw-{w}:checked~.posh .wsv-{w}{{display:inline}}#mw-{w}:checked~.mwx-{w}{{display:block}}#mw-{w}:checked~.posh label[for="mw-{w}"]{{background:var(--chalk);color:var(--ink)}}' for w in range(1,WT+1))
css+=('.mpk{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;margin:0 0 12px}.mpk label:last-child:nth-child(odd){grid-column:1/-1;justify-self:center;width:calc(50% - 2.5px)}'
      '.mop .mrc{font-style:normal;flex:none;color:var(--steel);font-size:.86em;font-variant-numeric:tabular-nums;margin-left:6px}'
      '.msc .mdf{font-style:normal;margin-left:8px;font-weight:600;font-variant-numeric:tabular-nums}.msc .mdf.w{color:var(--win)}.msc .mdf.l{color:var(--loss)}'
      '.mpk label{display:flex;flex-direction:column;gap:4px;padding:7px 9px;box-sizing:border-box;border-radius:6px;border:1px solid var(--hair);background:var(--ink);cursor:pointer;'
      'font-family:var(--display);font-weight:700;font-size:13.5px;letter-spacing:.03em;text-transform:uppercase;color:var(--label);white-space:nowrap;min-width:0}'
      '.mpk .pr2{display:grid;grid-template-columns:1.3em minmax(0,1fr) auto auto 3.1em;align-items:center;gap:5px;min-width:0;line-height:1.15}'
      '.mpk .prc{color:var(--steel);font-weight:600;font-size:.86em;font-variant-numeric:tabular-nums;letter-spacing:0}'
      '.mpk .pr2>b{min-width:0;overflow:hidden;text-overflow:ellipsis;font-weight:700}'
      '.mpk .dv{display:block;height:1px;background:currentColor;opacity:.15;margin:0 0 0 calc(1.3em + 5px)}'
      '.mpk .mrk{font-style:normal;text-align:right;color:var(--steel);font-variant-numeric:tabular-nums}'
      '.mpk .mrk.gold{color:#e8c15a}.mpk .mrk.g{color:var(--win)}.mpk .mrk.b{color:#ff8a9a}'
      '.mpk .stk{font-style:normal;font-size:10.5px;letter-spacing:0;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;width:2.5em;height:1.6em;padding:0 0 1.5px;border-radius:3px;line-height:1}'
      '.mpk .stk.w{color:var(--win);background:rgba(63,214,155,.12)}.mpk .stk.l{color:var(--loss);background:rgba(255,93,115,.12)}'
      '.mpk .sc{text-align:right;font-variant-numeric:tabular-nums;color:var(--label)}.mpk .fin .sc{color:var(--steel)}.mpk .fin .sc.hi{color:var(--chalk)}'
      '.mpk .pr2>b{color:var(--chalk)}.mpk .sc{color:var(--chalk)}.mpk .fin .sc{color:var(--steel)}.mpk .fin .sc.hi{color:var(--chalk)}'
      '.mpk label{transition:background-color .15s,border-color .15s}'
      '.mpk .nf{display:none}'
      '@media(max-width:449px){.mpk label{font-size:12.5px;letter-spacing:.01em}.mpk .pr2{grid-template-columns:1.1em minmax(0,1fr) auto auto 2.7em;gap:3px}.mpk .dv{margin-left:calc(1.2em + 3px)}}'
      '@media(max-width:399px){.mpk label{padding:7px 6px;font-size:12px;letter-spacing:0}}@media(max-width:389px){.mpk label{font-size:11.5px;letter-spacing:0}.mpk .pr2{gap:2px}}@media(max-width:374px){.mpk label{font-size:10.5px;letter-spacing:0;padding:7px 5px}.mpk .pr2{grid-template-columns:1em minmax(0,1fr) auto auto 2.55em}.mpk .pr2{gap:4px}}'
      +'')
css+=('.mcr em .hrt{display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;height:1.6em;font-family:var(--display);font-weight:700;font-size:inherit;letter-spacing:.08em;line-height:1;padding:0 calc(6.5px - .08em) 1.75px 6px;border-radius:4px;font-style:normal;vertical-align:middle}'
      '.mcr em .hrt-h{background:rgba(63,214,155,.14);color:#7fdcb6;box-shadow:inset 0 0 0 1px rgba(63,214,155,.5)}'
      '.mcr em .hrt-r{background:rgba(150,160,255,.13);color:#b9c1ff;box-shadow:inset 0 0 0 1px rgba(150,160,255,.5)}'
      '.mcr .hrd{font-style:normal;margin:0 6px;opacity:.6}'
      '.hrv-o{display:none}#lo-o:checked~.mwx .hrv-a{display:none}#lo-o:checked~.mwx .hrv-o{display:inline}'
      '.mcr .hrn{font-weight:500;color:var(--steel)}.mcr .hrn.hi{font-weight:700;color:var(--chalk)}')
css+=('.cr.lu .cn .hab{position:absolute;top:-8px;bottom:-8px;width:14px;box-sizing:border-box;border-radius:4px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-style:normal;pointer-events:none}'
      '.cr.lu .cn.a .hab{right:0}.cr.lu .cn.b .hab{left:0}'
      '.cr.lu .cn .hab span{display:block;font-family:var(--display);font-weight:700;font-size:10.5px;line-height:10px;height:10px;text-align:center}'
      '.cr.lu .cn .hab.hab-h{background:rgba(63,214,155,.14);color:#7fdcb6;box-shadow:inset 0 0 0 1px rgba(63,214,155,.5)}'
      '.cr.lu .cn .hab.hab-r{background:rgba(150,160,255,.13);color:#b9c1ff;box-shadow:inset 0 0 0 1px rgba(150,160,255,.5)}'
      '.cr.lu:has(.sln) .cn .hab{bottom:-4px}'
      '.cr.lu .cn.a.hbx .cnm{padding-right:15px}.cr.lu .cn.b.hbx .cnm{padding-left:15px}')
css+=('.hat{display:inline-block;min-width:14px;box-sizing:border-box;text-align:center;font-style:normal;font-family:var(--display);font-weight:700;font-size:11px;line-height:1;padding:2px 2px 1.5px;border-radius:3px;margin-right:2px;vertical-align:1px}'
      '.hat.h{color:#7fdcb6;background:rgba(63,214,155,.13);box-shadow:inset 0 0 0 1px rgba(63,214,155,.4)}'
      '.hat.r{color:#b3bcff;background:rgba(150,160,255,.12);box-shadow:inset 0 0 0 1px rgba(150,160,255,.38)}')
css+=('#lc-p:checked~.mwx .lcw label[for="lc-p"],#lc-t:checked~.mwx .lcw label[for="lc-t"]{background:var(--chalk);color:var(--ink)}'+team_tiles('#lc-t:checked~.mwx'))
css+=('.mug.muc label>span{white-space:nowrap!important}@media(max-width:419px){.muc label>span{letter-spacing:.02em!important}.mug.muc label{padding-inline:2px!important}}'
      '.muc .mrk{display:inline-block;margin-right:4px;text-align:right;font-style:normal;'
      'font-family:var(--display);font-weight:700;font-size:inherit;letter-spacing:0;color:var(--steel);font-variant-numeric:tabular-nums}'
      '.muc .mrk.gold{color:#e8c15a}.muc .mrk.g{color:var(--win)}.muc .mrk.b{color:#ff8a9a}'
      +''.join(f'#mu-{i}:checked~.muc label[for="mu-{i}"] .mrk{{color:var(--ink);opacity:.55}}' for i in range(lg.N//2)))
# full-width game rows (one per line, any number of games), bigger type, full names
css+=('.mpk{grid-template-columns:1fr!important;gap:6px}.mpk label:last-child:nth-child(odd){grid-column:auto;justify-self:stretch;width:auto}'
      '.mpk label{padding:10px 14px;font-size:16px;letter-spacing:.03em;gap:7px}'
      '.mpk .pr2{grid-template-columns:1.3em minmax(0,1fr) 2.4em 2.7em 2.6em 3.3em;gap:9px}.mpk .fin .pr2{grid-template-columns:1.3em minmax(0,1fr) 2.4em 2.7em 3.3em}'
      '.mpk .dv{margin-left:calc(1.3em + 9px)}.mpk .nf{display:inline}.mpk .ns{display:none}'
      '.mpk .stk{font-size:11.5px}.mpk .prc{text-align:right}'
      '.mpk .pwp{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;font-size:.86em;letter-spacing:0;color:var(--steel)}.mpk .pwp.hi{color:var(--label)}'
      '@media(max-width:399px){.mpk label{font-size:14.5px;padding:10px 11px;letter-spacing:.02em}.mpk .pr2{gap:6px}.mpk .dv{margin-left:calc(1.3em + 6px)}}'
      '@media(max-width:374px){.mpk label{font-size:13.5px;padding:9px 9px}.mpk .pr2{gap:5px}}')
open(P+'mu_section.html','w',encoding='utf-8').write(sec);open(P+'mu_css.css','w',encoding='utf-8').write(css)
if __name__=='__main__':
    for a,b in games: print(a,'v',b,len(byes(a,W)),len(byes(b,W)))
