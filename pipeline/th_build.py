import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Team Hub (v2): one team at a time, two views.
#   Data   = that team's row from every league matrix (Positions, Ranks, Stars, Age, Lineups, Margins, Home / Road, Byes)
#            built from the same data the Stats tab uses, so every number matches it.
#   Trends = week-by-week line charts (points, standings, points rank, all-play %, luck, playoff odds) with a CSS-only
#            week scrubber: tap a week and every chart's marker and readout moves to that week.
# Output: th_section.html + th_css.css (inserted by rebuild.py when features.json has "teamhub": true).
import json,re,html,sys,csv,math,random,statistics as st
P=__DTP__;sys.path.insert(0,P)
import lg
import sx_data as D
import sx_build as SB
e=html.escape
T,WK,FUT,G,TEAMS=D.T,D.WK,D.FUT,D.G,D.TEAMS
H=D._g('H');POSH=D._g('POS')['H']
N=len(TEAMS);SHORT0=D.SHORT0;FS=D.FROM_SHORT
ORD=list(lg.POS)
tone=lg.tone
def ordn(n):return f'{n}{"th" if 10<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10,"th")}'
def crank(vals,t,low=False):
    v=vals[t];return 1+sum(1 for x in vals.values() if (x<v-1e-9 if low else x>v+1e-9))
def rk(r,low_good=False):return f'<em class="tqr {tone(r)}">{ordn(r)}</em>'
def sg(x,d=1):return ('+' if x>=0.05 else '−' if x<=-0.05 else '')+f'{abs(x):.{d}f}' if abs(x)>=0.05 else f'{0:.{d}f}'
# ---------------------------------------------------------------- week-by-week series (all teams)
SC={t:{x[0]:x[2] for x in WK[t]} for t in TEAMS}
OPP={t:{x[0]:FS.get(x[1],x[1]) for x in WK[t]} for t in TEAMS}
for t in TEAMS:
    for f in FUT[t]:OPP[t][f[0]]=FS.get(f[1],f[1])
REG=14
try:
    import lg as _lgx;PON_,BYN_=_lgx.PO,_lgx.BYE_N
except Exception:PON_,BYN_=6,2
SER={t:dict(pts=[],res=[],stand=[],pfr=[],ap=[],luck=[],wins=[],xw=[]) for t in TEAMS}
for t in TEAMS:
    w_=xw=apw=apl=0
    for k in range(1,G+1):
        me=SC[t][k];op=SC[OPP[t][k]][k];won=me>op;w_+=won
        beat=sum(1 for o in TEAMS if o!=t and SC[o][k]<me);lost=sum(1 for o in TEAMS if o!=t and SC[o][k]>me)
        apw+=beat;apl+=lost;xw+=beat/(N-1)
        s=SER[t];s['pts'].append(me);s['res'].append('W' if won else 'L');s['wins'].append(w_);s['xw'].append(xw)
        s['ap'].append(100*apw/(apw+apl));s['luck'].append(w_-xw);s['stand'].append(POSH[t][k-1])
for k in range(1,G+1):
    cum={t:sum(SC[t][j] for j in range(1,k+1)) for t in TEAMS}
    for t in TEAMS:SER[t]['pfr'].append(crank(cum,t))
LGMED=[st.median(SC[t][k] for t in TEAMS) for k in range(1,G+1)]
# checks against the season table: all-play, luck, standings through week G
for t in TEAMS:
    assert abs(SER[t]['luck'][-1]-T[t][12])<0.011,(t,SER[t]['luck'][-1],T[t][12])
    assert SER[t]['wins'][-1]==T[t][0],t
    assert SER[t]['pfr'][-1]==T[t][4],t
# playoff odds as of each week (Monte Carlo: scores ~ normal(team mean, team sd through that week); seeding wins, then PF)
def odds_asof(k,n=4000,seed=11):
    rnd=random.Random(seed+k)
    pts={t:[SC[t][j] for j in range(1,k+1)] for t in TEAMS}
    allp=[v for t in TEAMS for v in pts[t]];psd=st.pstdev(allp) if len(allp)>1 else 20
    lg=st.mean(allp);M0=3  # shrink each team's mean toward the league mean (worth 3 weeks) so one big week doesn't decide it
    mu={t:(sum(pts[t])+M0*lg)/(k+M0) for t in TEAMS};sd={t:((st.stdev(pts[t])*(k-1)+psd*M0)/(k-1+M0) if k>=2 else psd) for t in TEAMS}
    w0={t:SER[t]['wins'][k-1] for t in TEAMS};pf0={t:sum(pts[t]) for t in TEAMS}
    games=[]
    for w in range(k+1,REG+1):
        seen=set()
        for t in TEAMS:
            if t in seen or w not in OPP[t]:continue
            o=OPP[t][w];seen|={t,o};games.append((t,o))
    cnt={t:[0,0,0,0] for t in TEAMS}
    for _ in range(n):
        W=dict(w0);PF=dict(pf0)
        for a,b in games:
            sa=rnd.gauss(mu[a],sd[a]);sb=rnd.gauss(mu[b],sd[b]);PF[a]+=sa;PF[b]+=sb
            W[a if sa>sb else b]+=1
        order=sorted(TEAMS,key=lambda t:(-W[t],-PF[t]))
        for i,t in enumerate(order):
            if i<6:cnt[t][0]+=1
            if i<2:cnt[t][1]+=1
            if i<1:cnt[t][2]+=1
            cnt[t][3]+=i+1
    return {t:[100*c/n for c in cnt[t]] for t in TEAMS}
OD=SB.O
ODW={k:odds_asof(k) for k in range(1,G)}
ODW[G]={t:[OD[t]['po'],OD[t]['bye'],OD[t]['top'],100*sum((i+1)*v/100 for i,v in enumerate(OD[t]['dist']))] for t in TEAMS}  # current week: the same figures as Stats > Odds
for t in TEAMS:
    for j,key in enumerate(('po','bye','top','fin')):SER[t][key]=[ODW[k][t][j]/(100 if key=='fin' else 1) for k in range(1,G+1)]
# ---------------------------------------------------------------- per-team matrices
PROWS={}
for r in csv.DictReader(open(P+'pos/pos.csv',encoding='utf-8')):
    PROWS[D.RN[int(r['roster_id'])]]=r
EF={t:v for t,v in json.load(open(P+'eff.json')).items()}
EFR={t:EF[t][0] for t in TEAMS}
DP={t:[D.dropped(t)[k] for k in ORD] for t in TEAMS}
CLS=SB.CL;STS=SB.ST;YOS=SB.YO;HES=SB.HE;BYS=SB.BY;HRT=SB.HRT
def avg(v):return sum(v)/len(v) if v else 0
# ---------------------------------------------------------------- Data view
def sec(title,sub=''):return f'<div class="sxh tqh"><b>{title}</b><span>{sub}</span></div>'
def kpi(lab,val,r=None,sub='',neutral=False):
    rr=(f'<em class="tqr">{ordn(r)}</em>' if neutral else rk(r)) if r else ''
    return f'<div class="tqk"><span class="tqkl">{lab}</span><b class="tqkv">{val}</b><span class="tqks">{rr}{sub}</span></div>'
def data_view(t):
    o=[]
    x=T[t];sd=H.index(t)+1;O=OD[t]
    strk=SER[t]['res'];k=1
    while k<len(strk) and strk[-k-1]==strk[-1]:k+=1
    o.append('<div class="tqhero">'
             f'<div class="tqid"><span class="tqsd {tone(sd)}">{sd}</span><div><b>{e(t)}</b><span>{x[0]}-{x[1]} · <i class="stk {strk[-1].lower()}">{strk[-1]}{k}</i> · {x[5]:.1f} PF/wk</span></div></div>'
             '<div class="tqod">'+''.join(f'<div><span>{lab}</span><b>{SB.pct(v)}</b></div>' for lab,v in (('Playoffs',O['po']),('Bye',O['bye']),('#1 seed',O['top'])))+'</div></div>')
    apr={u:T[u][10]/(T[u][10]+T[u][11]) for u in TEAMS};lk={u:T[u][12] for u in TEAMS}
    o.append('<div class="tqkg">'
             +kpi('Points for',f'{x[3]:.1f}',x[4])+kpi('Points against',f'{x[6]:.1f}',x[7],' <span class="tqkn">most = 1st</span>',neutral=True)
             +kpi('All-play',f'{x[10]}-{x[11]}',crank(apr,t))+kpi('Luck',sg(x[12],2),crank(lk,t))
             +kpi('Lineup efficiency',f'{EF[t][0]:.0f}<small>%</small>',crank(EFR,t))+kpi('Left on bench',f'{EF[t][1]:.1f}<small>/wk</small>',crank({u:EF[u][1] for u in TEAMS},t,low=True))
             +'</div>')
    # positions
    pr=PROWS[t];rows=''
    best={p:max(float(PROWS[u][f'avg_{p}']) for u in TEAMS) for p in ORD}
    for p in ORD:
        v=float(pr[f'avg_{p}']);r=int(pr[f'avg_{p}_rank'])
        rows+=(f'<div class="tqpr"><i class="pz p-{p.lower()}">{p}</i><span class="tqbar"><i class="p-{p.lower()}" style="width:{100*v/best[p]:.1f}%"></i></span>'
               f'<b class="tqv">{v:.1f}</b>{rk(r)}</div>')
    o.append(sec('Points per start','By position · bar = share of the league best'));o.append(f'<div class="tqpos">{rows}</div>')
    # weekly score rank row + results
    cells=''.join(f'<span class="hm r{r}">{r}</span>' for r in HES[t]);hd=''.join(f'<span>W{w}</span>' for w in range(1,G+1))
    res=''.join(f'<span class="tqwl {r_.lower()}">{r_}</span>' for r_ in SER[t]['res'])
    o.append(sec('Weekly score rank','1 = highest score that week'))
    o.append(f'<div class="sxm hmx tqgrid" style="--n:{G}"><div class="sxr sxhd"><span></span>{hd}<span>Avg</span></div>'
             f'<div class="sxr"><span class="mxn">Rank</span>{cells}<span class="hav">{avg(HES[t]):.1f}</span></div>'
             f'<div class="sxr tqres"><span class="mxn">Result</span>{res}<span></span></div></div>')
    # every-week head to head: this team's score against each opponent's score, every week
    ew=SB.EW[t];ops=[u for u in H if u!=t]
    o.append(sec('Every-week head to head',f'Record if they had played each team every week · Wk 1–{G}'))
    o.append('<div class="tqew">'+''.join(f'<div><span>{e(u)}</span><b class="{"up" if ew[u][0]>ew[u][1] else "dn" if ew[u][0]<ew[u][1] else ""}">{SB._rec(ew[u])}</b></div>' for u in ops)+'</div>')
    # stars
    s=STS[t]
    segs=''.join(f'<i class="p-{v[1].lower()}{" s1" if i==0 else ""}" style="width:{v[2]/s["tot"]*100:.2f}%"></i>' for i,v in enumerate(s['top3']))
    names=''.join(f'<span>{SB.pz(v[1])}{e(v[0])} <em>{v[2]/s["tot"]*100:.0f}%</em></span>' for v in s['top3'])
    s1={u:STS[u]['s1'] for u in TEAMS};s3={u:STS[u]['s3'] for u in TEAMS}
    o.append(sec('Star dependence','Share of season points from the top 1 and top 3 scorers'))
    o.append(f'<div class="stb tqstb"><div class="stt"><span><b>{s["s1"]:.0f}%</b> top 1 <em class="tqr">{ordn(crank(s1,t))}</em></span><span><b>{s["s3"]:.0f}%</b> top 3 <em class="tqr">{ordn(crank(s3,t))}</em></span></div>'
             f'<div class="bar sbar">{segs}</div><div class="stn">{names}</div></div>')
    # age
    p_=YOS[t]['pct'];yr={u:YOS[u]['pct'][0] for u in TEAMS}
    o.append(sec('Production by age','Share of starters\' points by player age '+('at season end' if _dt_os.environ.get('DT_PAST')=='1' else 'today')))
    o.append('<div class="ylg"><span class="ay">25 and under</span><span class="ap">26–29</span><span class="ao">30+</span><span class="ad">DEF</span></div>'
             f'<div class="stb tqstb"><div class="stt"><span><b class="ay">{p_[0]:.0f}%</b> · <b class="ap">{p_[1]:.0f}%</b> · <b class="ao">{p_[2]:.0f}%</b></span><span>youth share {rk(crank(yr,t))}</span></div>'
             f'<div class="bar ybar"><i class="y0" style="width:{p_[0]:.2f}%"></i><i class="y1" style="width:{p_[1]:.2f}%"></i><i class="y2" style="width:{p_[2]:.2f}%"></i><i class="y3" style="width:{p_[3]:.2f}%"></i></div></div>')
    # lineups: dropped points by position
    dmax=max(max(v for v,p in zip(DP[u],ORD) if p not in ('K','DEF')) for u in TEAMS) or 1
    o.append(sec('Dropped points','Per week: bench points that should have started, by position'))
    o.append('<div class="tqdp">'+''.join(f'<div><i class="pz p-{p.lower()}">{p}</i><b class="tqv{" z" if DP[t][i]<0.05 else ""}">{DP[t][i]:.1f}</b>{(lambda r,tie:f'<i class="ch tqdr {tone(r)}"><span class="ct">{"T" if tie else ""}{r}</span></i>')(crank({u:DP[u][i] for u in TEAMS},t,True),sum(1 for u in TEAMS if u!=t and abs(DP[u][i]-DP[t][i])<1e-9)>0)}<span class="tqmini"><i class="p-{p.lower()}" style="height:{100*DP[t][i]/dmax:.1f}%"></i></span></div>' for i,p in enumerate(ORD) if p not in ('K','DEF'))+'</div>')
    # margins
    c=CLS[t];am={u:CLS[u]['avgm'] for u in TEAMS}
    o.append(sec('Margins','Close = under 10 pts · blowout = 30+ pts'))
    o.append('<div class="tqkg tq3">'+kpi('Close games',f'{c["close"][0]}-{c["close"][1]}')+kpi('Blowouts',f'{c["blow"][0]}-{c["blow"][1]}')+kpi('Avg margin',f'<span class="{"up" if c["avgm"]>=0.05 else "dn" if c["avgm"]<=-0.05 else ""}">{sg(c["avgm"])}</span>',crank(am,t))+'</div>')
    # home / road
    h=HRT[t];hs={u:HRT[u]['h']/(HRT[u]['h']+HRT[u]['r']) for u in TEAMS}
    ah,ar=avg(h['ph']),avg(h['pr'])
    o.append(sec('Home / Road',f'Starters at home or on the road · Wk 1–{G}'))
    o.append(f'<div class="tqhr"><div class="tqhr1">{SB.HT}<b>{h["h"]}</b><span class="hx-bar tqhb">{SB._split(h["h"],h["r"])[len("<span class=\"hx-bar\">"):-7]}</span><b>{h["r"]}</b>{SB.RT}</div>'
             f'<div class="tqhr2"><span>Home share</span><b>{100*hs[t]:.0f}<small>%</small></b>{rk(crank(hs,t))}</div></div>')
    vh,vr=SB._hv(ah,ar);dd=SB._dv(ah-ar)
    o.append('<div class="sxt hx-tb tqhrt" style="--cols:minmax(0,1fr) 56px 56px 52px">'
             f'<div class="sxr sxhd"><span></span><span>{SB.HT}</span><span>{SB.RT}</span><span>Diff</span></div>'
             f'<div class="sxr"><span>Points per start</span>{vh}{vr}{dd}</div>'
             f'<div class="sxr"><span>Record when more starters</span><span class="sxv">{SB._hrrec(h["lh"])}</span><span class="sxv">{SB._hrrec(h["lr"])}</span><span></span></div></div>')
    # byes (none once the regular season is over)
    wk=list(range(D.NOW,15));B=BYS[t]
    if not wk:return ''.join(o)
    cells=''.join(f'<span class="bx b{min(len(B[w]),3)}">{len(B[w]) or "–"}</span>' for w in wk)
    o.append(sec('Bye exposure','Core starters on bye each remaining week'))
    o.append(f'<div class="sxm bym tqgrid" style="--n:{len(wk)}"><div class="sxr sxhd"><span></span>{"".join(f"<span>W{w}</span>" for w in wk)}</div><div class="sxr"><span class="mxn">On bye</span>{cells}</div></div>')
    notes=''
    for w in wk:
        if not B[w]:continue
        op=OPP[t].get(w);r=H.index(op)+1 if op else None
        nm=''.join(f'<span>{SB.pz(p[2])}{e(p[3]+" DEF" if p[2]=="DEF" else p[1])}</span>' for p in B[w])
        notes+=(f'<div class="bnl"><span>Wk {w}</span><b class="bnt">vs <em class="{tone(r)}">{r}</em> {e(SHORT0.get(op,op))}</b><i>{nm}</i></div>')
    o.append(notes or '<div class="tqnone">No core starters on bye in the remaining weeks</div>')
    return ''.join(o)
# ---------------------------------------------------------------- Trends view (SVG line charts + CSS week scrubber)
VW,VH,PL,PR,PT,PB=320,128,30,12,12,20
def xs(k):return PL+(VW-PL-PR)*(k-1)/max(G-1,1)
def chart(key,title,vals,lo,hi,fmt,ticks,inv=False,ref=None,refl='',dots=None,zero=None,area=None,readout=None,tickfmt=None,seeds=False):
    ys=lambda v:PT+(VH-PT-PB)*((v-lo)/(hi-lo) if not inv else (v-lo)/(hi-lo))
    Y=(lambda v:PT+(VH-PT-PB)*(v-lo)/(hi-lo)) if inv else (lambda v:VH-PB-(VH-PT-PB)*(v-lo)/(hi-lo))
    g=[]
    for tv in ticks:
        g.append(f'<line class="tgl" x1="{PL}" x2="{VW-PR}" y1="{Y(tv):.1f}" y2="{Y(tv):.1f}"/><text class="tax" x="{PL-6}" y="{Y(tv)+3.5:.1f}" text-anchor="end">{(tickfmt or str)(tv)}</text>')
    if seeds:  # bye line (2nd) and playoff line (6th)
        for v,c,lab in ((2,'tqby','Bye'),(6,'tqpo','Playoffs')):
            g.append(f'<line class="{c}" x1="{PL}" x2="{VW-PR}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text class="{c}t" x="{PL+4}" y="{Y(v)-3:.1f}" text-anchor="start">{lab}</text>')
    if zero is not None:g.append(f'<line class="tzero" x1="{PL}" x2="{VW-PR}" y1="{Y(zero):.1f}" y2="{Y(zero):.1f}"/>')
    for k in range(1,G+1):g.append(f'<text class="tax" x="{xs(k):.1f}" y="{VH-4}" text-anchor="middle">{k}</text>')
    if ref:g.append('<path class="tref" d="'+'M'+' L'.join(f'{xs(k):.1f} {Y(v):.1f}' for k,v in enumerate(ref,1))+'"/>')
    if area is not None:  # luck: fill between line and zero, green above / red below
        for k in range(1,G):
            a,b=vals[k-1],vals[k];
            g.append(f'<path class="tarea {"pos" if (a+b)/2>=0 else "neg"}" d="M{xs(k):.1f} {Y(0):.1f} L{xs(k):.1f} {Y(a):.1f} L{xs(k+1):.1f} {Y(b):.1f} L{xs(k+1):.1f} {Y(0):.1f}Z"/>')
    g.append('<path class="tline" d="'+'M'+' L'.join(f'{xs(k):.1f} {Y(v):.1f}' for k,v in enumerate(vals,1))+'"/>')
    for k,v in enumerate(vals,1):
        c=f' {dots[k-1]}' if dots else ''
        g.append(f'<circle class="tdot{c}" cx="{xs(k):.1f}" cy="{Y(v):.1f}" r="3"/>')
        g.append(f'<g class="twm twm-{k}"><line class="tcur" x1="{xs(k):.1f}" x2="{xs(k):.1f}" y1="{PT-4}" y2="{VH-PB}"/><circle class="tsel{c}" cx="{xs(k):.1f}" cy="{Y(v):.1f}" r="5.5"/></g>')
    ro=''.join(f'<b class="tro tro-{k}">{(readout or fmt)(k)}</b>' for k in range(1,G+1))
    leg=f'<span class="tleg"><i></i>{refl}</span>' if refl else ''
    return (f'<div class="tch"><div class="tchh"><span>{title}</span>{leg}{ro}</div>'
            f'<svg viewBox="0 0 {VW} {VH}" class="tsvg" role="img" aria-label="{e(title)} by week">{"".join(g)}</svg></div>')
def odds_chart(s):
    Y=lambda v:VH-PB-(VH-PT-PB)*v/100
    L=[('po','Playoffs','c1'),('bye','Bye','c2'),('top','#1 seed','c3')]
    g=[]
    for tv in (0,50,100):g.append(f'<line class="tgl" x1="{PL}" x2="{VW-PR}" y1="{Y(tv):.1f}" y2="{Y(tv):.1f}"/><text class="tax" x="{PL-6}" y="{Y(tv)+3.5:.1f}" text-anchor="end">{tv}%</text>')
    for k in range(1,G+1):g.append(f'<text class="tax" x="{xs(k):.1f}" y="{VH-4}" text-anchor="middle">{k}</text>')
    for key,_,c in reversed(L):
        g.append(f'<path class="tline {c}" d="M'+' L'.join(f'{xs(k):.1f} {Y(v):.1f}' for k,v in enumerate(s[key],1))+'"/>')
        g+= [f'<circle class="tdot {c}" cx="{xs(k):.1f}" cy="{Y(v):.1f}" r="2.6"/>' for k,v in enumerate(s[key],1)]
    for k in range(1,G+1):
        g.append(f'<g class="twm twm-{k}"><line class="tcur" x1="{xs(k):.1f}" x2="{xs(k):.1f}" y1="{PT-4}" y2="{VH-PB}"/>'
                 +''.join(f'<circle class="tsel {c}" cx="{xs(k):.1f}" cy="{Y(s[key][k-1]):.1f}" r="4.5"/>' for key,_,c in reversed(L))+'</g>')
    pc=lambda v:('>99' if 99<v<99.95 else '<1' if 0.05<v<1 else f'{v:.0f}')
    ro=''.join(f'<span class="tro tro-{k} trm">'+''.join(f'<b class="{c}">{pc(s[key][k-1])}<small>%</small></b>' for key,_,c in L)+'</span>' for k in range(1,G+1))
    leg='<span class="tlg3">'+''.join(f'<span class="{c}"><i></i>{lab}</span>' for _,lab,c in L)+'</span>'
    return (f'<div class="tch"><div class="tchh"><span>Playoff odds</span>{ro}</div>{leg}'
            f'<svg viewBox="0 0 {VW} {VH}" class="tsvg" role="img" aria-label="Playoff, bye and number one seed odds by week">{"".join(g)}</svg></div>')
# ---------------------------------------------------------------- extra weekly series for Trends
POS4=['QB','RB','WR','TE']
for t in TEAMS:
    s=SER[t];s['srk']=[];s['par']=[];s['eff']=[];s['proj']=[];s['pos']={p_:[] for p_ in POS4}
for k in range(1,G+1):
    cpa={t:sum(SC[OPP[t][j]][j] for j in range(1,k+1)) for t in TEAMS}
    lu={t:D.lineup(t,k) for t in TEAMS}
    pp={t:{p_:sum(q['pts'] for q in lu[t][0] if q and q['pos']==p_) for p_ in POS4} for t in TEAMS}
    for t in TEAMS:
        s=SER[t];me=SC[t][k]
        s['srk'].append(1+sum(1 for o in TEAMS if SC[o][k]>me+1e-9));s['par'].append(crank(cpa,t))
        st_,bn_=lu[t];best=sum(q['pts'] for q in D.optimal([q for q in st_+bn_ if q]) if q)
        s['eff'].append(100*sum(q['pts'] for q in st_ if q)/best if best else 100.0)
        s['proj'].append(sum(q.get('proj',0) or 0 for q in st_ if q))
        for p_ in POS4:s['pos'][p_].append(pp[t][p_]-st.mean(pp[u][p_] for u in TEAMS))
LGEFF=[st.mean(SER[t]['eff'][k] for t in TEAMS) for k in range(G)]
# power score: all-play win % to date (60%) and the last three weeks' all-play win % (40%); ranked each week
for k in range(1,G+1):
    pw={}
    for t in TEAMS:
        rec=[(sum(1 for o in TEAMS if o!=t and SC[o][j]<SC[t][j]))/(N-1) for j in range(1,k+1)]
        pw[t]=0.6*sum(rec)/len(rec)+0.4*sum(rec[-3:])/len(rec[-3:])
    for t in TEAMS:SER[t].setdefault('pwr',[]).append(crank(pw,t))
def rtile(txt,cls=''):
    """a rank readout as a tile (sized from the digits by inkTile on the page)"""
    return f'<i class="tqt {cls}" data-h="20"><span class="ct">{txt}</span></i>'
def stier(r):return 'tby' if r<=BYN_ else 'tpo' if r<=PON_ else ''
def multi_chart(key,title,series,lo,hi,ticks,tickfmt,readout,zero=None,ref=None,refl=''):
    """several lines on one chart (series = [(label, values, css class)])"""
    Y=lambda v:VH-PB-(VH-PT-PB)*(v-lo)/(hi-lo)
    g=[f'<line class="tgl" x1="{PL}" x2="{VW-PR}" y1="{Y(tv):.1f}" y2="{Y(tv):.1f}"/><text class="tax" x="{PL-6}" y="{Y(tv)+3.5:.1f}" text-anchor="end">{tickfmt(tv)}</text>' for tv in ticks]
    if zero is not None:g.append(f'<line class="tzero" x1="{PL}" x2="{VW-PR}" y1="{Y(zero):.1f}" y2="{Y(zero):.1f}"/>')
    g+=[f'<text class="tax" x="{xs(k):.1f}" y="{VH-4}" text-anchor="middle">{k}</text>' for k in range(1,G+1)]
    if ref:g.append('<path class="tref" d="M'+' L'.join(f'{xs(k):.1f} {Y(v):.1f}' for k,v in enumerate(ref,1))+'"/>')
    for _,vals,c in series:
        g.append(f'<path class="tline {c}" d="M'+' L'.join(f'{xs(k):.1f} {Y(v):.1f}' for k,v in enumerate(vals,1))+'"/>')
    for k in range(1,G+1):
        g.append(f'<g class="twm twm-{k}"><line class="tcur" x1="{xs(k):.1f}" x2="{xs(k):.1f}" y1="{PT-4}" y2="{VH-PB}"/>'
                 +''.join(f'<circle class="tsel {c}" cx="{xs(k):.1f}" cy="{Y(vals[k-1]):.1f}" r="4.5"/>' for _,vals,c in series)+'</g>')
    ro=''.join(f'<span class="tro tro-{k} trm">{readout(k)}</span>' for k in range(1,G+1))
    leg='<span class="tlg3">'+''.join(f'<span class="{c}"><i></i>{lab}</span>' for lab,_,c in series)+(f'<span class="tref"><i></i>{refl}</span>' if refl else '')+'</span>'
    return (f'<div class="tch"><div class="tchh"><span>{title}</span>{ro}</div>{leg}'
            f'<svg viewBox="0 0 {VW} {VH}" class="tsvg" role="img" aria-label="{e(title)} by week">{"".join(g)}</svg></div>')
def bands_chart(s):
    """playoff / bye / #1 odds as nested bands: every #1 seed has a bye and every bye team is in the playoffs, so each band
    is the chance to finish in exactly that tier; blank above = out"""
    Y=lambda v:VH-PB-(VH-PT-PB)*v/100
    L=[('po','Playoffs','b1'),('bye','Bye','b2'),('top','#1 seed','b3')]
    g=[f'<line class="tgl" x1="{PL}" x2="{VW-PR}" y1="{Y(tv):.1f}" y2="{Y(tv):.1f}"/><text class="tax" x="{PL-6}" y="{Y(tv)+3.5:.1f}" text-anchor="end">{tv}%</text>' for tv in (0,50,100)]
    g+=[f'<text class="tax" x="{xs(k):.1f}" y="{VH-4}" text-anchor="middle">{k}</text>' for k in range(1,G+1)]
    for key,_,c in L:
        pts_=' '.join(f'{xs(k):.1f},{Y(v):.1f}' for k,v in enumerate(s[key],1))
        g.append(f'<polygon class="tband {c}" points="{xs(1):.1f},{Y(0):.1f} {pts_} {xs(G):.1f},{Y(0):.1f}"/>')
        g.append(f'<path class="tline {c}" d="M'+' L'.join(f'{xs(k):.1f} {Y(v):.1f}' for k,v in enumerate(s[key],1))+'"/>')
    for k in range(1,G+1):
        g.append(f'<g class="twm twm-{k}"><line class="tcur" x1="{xs(k):.1f}" x2="{xs(k):.1f}" y1="{PT-4}" y2="{VH-PB}"/>'
                 +''.join(f'<circle class="tsel {c}" cx="{xs(k):.1f}" cy="{Y(s[key][k-1]):.1f}" r="4.5"/>' for key,_,c in L)+'</g>')
    pc=lambda v:('>99' if 99<v<99.95 else '<1' if 0.05<v<1 else f'{v:.0f}')
    ro=''.join(f'<span class="tro tro-{k} trm">'+''.join(f'<b class="{c}">{pc(s[key][k-1])}<small>%</small></b>' for key,_,c in L)+'</span>' for k in range(1,G+1))
    leg='<span class="tlg3">'+''.join(f'<span class="{c}"><i></i>{lab}</span>' for _,lab,c in L)+'</span>'
    return (f'<div class="tch"><div class="tchh"><span>Playoff odds</span>{ro}</div>{leg}'
            f'<svg viewBox="0 0 {VW} {VH}" class="tsvg" role="img" aria-label="Playoff, bye and number one seed odds by week">{"".join(g)}</svg></div>')
def trends_view(t):
    s=SER[t]
    pts=s['pts'];lo=math.floor(min(pts+LGMED+s['proj'])/20)*20;hi=math.ceil(max(pts+LGMED+s['proj'])/20)*20
    rt=lambda v:list(range(lo,hi+1,20 if hi-lo<=100 else 40))
    rk_ticks=sorted({1,4,7,10,N})
    ch=[chart('pts','Points scored',pts,lo,hi,None,rt(0),ref=LGMED,refl='league median',
              dots=[r.lower() for r in s['res']],readout=lambda k:f'{pts[k-1]:.1f} <small class="{s["res"][k-1].lower()}">{s["res"][k-1]}</small>'),
        chart('srk','Weekly score rank',s['srk'],1,N,None,rk_ticks,inv=True,readout=lambda k:rtile(s['srk'][k-1],tone(s['srk'][k-1])),tickfmt=lambda v:ordn(v)),
        chart('st','Standings',s['stand'],1,N,None,rk_ticks,inv=True,seeds=True,readout=lambda k:rtile(ordn(s['stand'][k-1]),stier(s['stand'][k-1])),tickfmt=lambda v:ordn(v)),
        multi_chart('pwr','Power rank vs seed',[('Power',s['pwr'],'c1'),('Seed',s['stand'],'c4')],N,1,rk_ticks,lambda v:ordn(v),
              lambda k:f'{rtile(ordn(s["pwr"][k-1]),tone(s["pwr"][k-1]))}<small>power</small> {rtile(ordn(s["stand"][k-1]),stier(s["stand"][k-1]))}<small>seed</small>'),
        multi_chart('pfpa','Points-for and against rank',[('PF',s['pfr'],'c1'),('PA',s['par'],'c5')],N,1,rk_ticks,lambda v:ordn(v),
              lambda k:f'{rtile(ordn(s["pfr"][k-1]),tone(s["pfr"][k-1]))}<small>PF</small> {rtile(ordn(s["par"][k-1]),tone(s["par"][k-1]))}<small>PA</small>'),
        chart('ap','All-play win %',s['ap'],0,100,None,[0,50,100],readout=lambda k:f'{s["ap"][k-1]:.0f}<small>%</small>',tickfmt=lambda v:f'{v}%'),
        chart('lk','Luck · wins minus expected',s['luck'],min(-2,math.floor(min(s['luck']))),max(2,math.ceil(max(s['luck']))),None,
              sorted({min(-2,math.floor(min(s['luck']))),0,max(2,math.ceil(max(s['luck'])))}),zero=0,area=True,
              readout=lambda k:f'{sg(s["luck"][k-1],2)} <small>{s["wins"][k-1]} W · {s["xw"][k-1]:.2f} xW</small>',tickfmt=lambda v:sg(v,0) if v else '0'),
        multi_chart('pva','Projected vs actual',[('Actual',pts,'c1'),('Projected',s['proj'],'c4')],lo,hi,rt(0),str,
              lambda k:f'<b class="c1">{pts[k-1]:.1f}</b><b class="c4">{s["proj"][k-1]:.1f}</b><small>{sg(pts[k-1]-s["proj"][k-1])}</small>'),
        chart('eff','Lineup efficiency',s['eff'],min(70,math.floor(min(s['eff']+LGEFF)/10)*10),100,None,
              sorted({min(70,math.floor(min(s['eff']+LGEFF)/10)*10),85,100}),ref=LGEFF,refl='league avg',readout=lambda k:f'{s["eff"][k-1]:.0f}<small>%</small>',tickfmt=lambda v:f'{v}%'),
        multi_chart('pos','Position strength',[(p_,s['pos'][p_],'p-'+p_.lower()) for p_ in POS4],
              min(-20,5*math.floor(min(min(v) for v in s['pos'].values())/5)),max(20,5*math.ceil(max(max(v) for v in s['pos'].values())/5)),
              sorted({min(-20,5*math.floor(min(min(v) for v in s['pos'].values())/5)),0,max(20,5*math.ceil(max(max(v) for v in s['pos'].values())/5))}),
              lambda v:sg(v,0) if v else '0',lambda k:''.join(f'<b class="p-{p_.lower()}">{sg(s["pos"][p_][k-1],0) if abs(s["pos"][p_][k-1])>=0.5 else "0"}</b>' for p_ in POS4),zero=0),
        bands_chart(s),
        chart('fin','Projected finish',s['fin'],1,N,None,rk_ticks,inv=True,seeds=True,readout=lambda k:f'{s["fin"][k-1]:.1f} <small>avg finish</small>',tickfmt=lambda v:ordn(v))]
    def rc(k):
        o=OPP[t][k];r=s['res'][k-1]
        return (f'<div class="trc trc-{k}"><span class="trw">Week {k}</span>{rtile(r,("w" if r=="W" else "l")+'" data-ref="W')}'
                f'<b class="trs">{pts[k-1]:.1f} – {SC[o][k]:.1f}</b><span class="tro2"><em>vs</em><i class="pav" data-avt="{e(o)}" aria-hidden="true"></i><b>{e(SHORT0.get(o,o))}</b></span></div>')
    return f'<div class="trd">{"".join(rc(k) for k in range(1,G+1))}</div>',f'<div class="tcs">{"".join(ch)}</div>'
# ---------------------------------------------------------------- assemble
picker='<div class="tqpk" role="tablist" aria-label="Team">'+''.join(f'<label for="thx-{i}"><em class="rrk">{i+1}</em><span>{e(t)}</span></label>' for i,t in enumerate(H))+'</div>'
wks='<div class="tqwk" role="group" aria-label="Week"><span>Week</span>'+''.join(f'<label for="thw-{k}">{k}</label>' for k in range(1,G+1))+'</div>'
radios=(''.join(f'<input type="radio" name="thx" id="thx-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(N))
        +'<input type="radio" name="tqv" id="thv-d" class="lr" checked><input type="radio" name="tqv" id="thv-t" class="lr">'
        +''.join(f'<input type="radio" name="thw" id="thw-{k}" class="lr"{" checked" if k==G else ""}>' for k in range(1,G+1)))
ctl=('<div class="tqctl"><div class="pseg tqvs" role="group" aria-label="View"><label for="thv-d">Data</label><label for="thv-t">Trends</label></div></div>')
pans=''.join((lambda tr:f'<div class="tqp tqp-{i}"><div class="tqdv">{data_view(t)}</div><div class="tqtv"><div class="tqsk">{wks}{tr[0]}</div>{tr[1]}</div></div>')(trends_view(t)) for i,t in enumerate(H))
JS=('<script>(function(){var VW=%d,PL=%d,PR=%d,G=%d;function pick(sv,x){var r=sv.getBoundingClientRect();var vx=(x-r.left)*VW/r.width;'
    'var k=Math.round((vx-PL)/((VW-PL-PR)/(G-1)))+1;k=Math.max(1,Math.min(G,k));var el=document.getElementById("thw-"+k);'
    'if(el&&!el.checked){el.checked=true;el.dispatchEvent(new Event("change",{bubbles:true}))}}'
    'var act=null;document.addEventListener("pointerdown",function(e){var sv=e.target.closest&&e.target.closest(".thx2 .tsvg");if(!sv)return;act=sv;pick(sv,e.clientX)});'
    'document.addEventListener("pointermove",function(e){if(act)pick(act,e.clientX)});'
    '["pointerup","pointercancel"].forEach(function(t){document.addEventListener(t,function(){act=null})})})()</script>')%(VW,PL,PR,G)
sec_=(f'<section class="thx2" aria-labelledby="thh2">{radios}<div class="posh"><b id="thh2">Team Hub</b></div>'
      f'<div class="rsub">One team at a time · Wk 1–{G}</div>{picker}{ctl}{pans}</section>'+JS)
TL='#efd38a'
PKCSS=('.thx2 .tqpk{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;margin:2px 0 12px}'
 '.thx2 .tqpk label{display:flex;align-items:center;gap:7px;min-height:36px;padding:6px 10px;box-sizing:border-box;border-radius:6px;border:1px solid var(--hair);background:var(--ink);cursor:pointer;'
 'font-family:var(--display);font-weight:700;font-size:13.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--label);white-space:nowrap;min-width:0}'
 '.thx2 .tqpk label span{overflow:hidden;text-overflow:ellipsis;min-width:0}'
 '.thx2 .tqpk .rrk{font-style:normal;flex:none;min-width:1.2em;text-align:right;color:var(--steel);font-variant-numeric:tabular-nums}'
 '@media(max-width:429px){.thx2 .tqpk label{font-size:12.5px;letter-spacing:.02em;padding:6px 8px;gap:6px}}@media(max-width:374px){.thx2 .tqpk label{font-size:11.5px;letter-spacing:.01em;padding:6px 6px;gap:5px}}'
 '.tqkn{font-size:10.5px;color:var(--dim)}')
css=PKCSS+(''.join(f'#thx-{i}:checked~.tqpk label[for="thx-{i}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#thx-{i}:checked~.tqpk label[for="thx-{i}"] .rrk{{color:var(--ink);opacity:.55}}#thx-{i}:checked~.tqp-{i}{{display:block}}' for i in range(N))
 +''.join(f'#thw-{k}:checked~.tqp .tqwk label[for="thw-{k}"]{{background:var(--chalk);color:var(--ink)}}#thw-{k}:checked~.tqp .twm-{k},#thw-{k}:checked~.tqp .tro-{k}{{display:inline}}#thw-{k}:checked~.tqp .trc-{k}{{display:grid}}' for k in range(1,G+1))
 +'#thv-d:checked~.tqctl label[for="thv-d"],#thv-t:checked~.tqctl label[for="thv-t"]{background:var(--chalk);color:var(--ink)}'
 +'.thx2 .tqp,.thx2 .tqtv{display:none}#thv-t:checked~.tqp .tqdv{display:none}#thv-t:checked~.tqp .tqtv{display:block}'
 +'.thx2 .tqctl{display:flex;justify-content:flex-end;margin:0 0 10px}.thx2 .tqctl .pseg{display:inline-flex}'
 # hero
 +'.tqhero{display:flex;flex-direction:column;gap:12px;padding:14px;margin:4px 0 10px;background:var(--deck);border:1px solid var(--hair);border-radius:12px}'
 +'.tqid{display:flex;align-items:center;gap:12px;min-width:0}.tqid>div{display:flex;flex-direction:column;gap:3px;min-width:0}'
 +'.tqid b{font-family:var(--display);font-weight:700;font-size:22px;letter-spacing:.03em;text-transform:uppercase;color:var(--chalk);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
 +'.tqid>div>span{font-size:13px;color:var(--label);font-variant-numeric:tabular-nums}'
 +'.tqsd{flex:none;display:grid;place-items:center;width:40px;height:40px;border-radius:10px;font-family:var(--display);font-weight:700;font-size:22px;background:var(--ink);color:var(--label);box-shadow:inset 0 0 0 1px var(--line-strong,rgba(255,255,255,.14))}'
 +'.tqsd.gold{color:#e8c15a;box-shadow:inset 0 0 0 1.5px rgba(232,193,90,.6)}.tqsd.g{color:var(--win);box-shadow:inset 0 0 0 1.5px rgba(63,214,155,.5)}.tqsd.b{color:#ff8a9a;box-shadow:inset 0 0 0 1.5px rgba(255,93,115,.5)}'
 +'.tqid .stk{font-style:normal;font-family:var(--display);font-weight:700;font-size:11px;padding:1px 4px 0;border-radius:3px}.tqid .stk.w{color:var(--win);background:rgba(63,214,155,.12)}.tqid .stk.l{color:var(--loss);background:rgba(255,93,115,.12)}'
 +'.tqod{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.tqod>div{display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 4px;border-radius:8px;background:var(--ink);border:1px solid var(--hair)}'
 +'.tqod span{font-family:var(--display);font-weight:600;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--steel)}.tqod b{font-family:var(--display);font-weight:700;font-size:22px;color:var(--chalk);font-variant-numeric:tabular-nums}'
 +'.tqod b small,.tqkv small,.tqv small,.tqhr2 b small{font-size:.6em;color:var(--steel);margin-left:1px}'
 # kpi grid
 +'.tqkg{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;margin:0 0 6px}.tqkg.tq3{grid-template-columns:repeat(3,minmax(0,1fr))}'
 +'.tqk{display:flex;flex-direction:column;gap:3px;padding:9px 11px;border-radius:8px;background:var(--deck);border:1px solid var(--hair);min-width:0}'
 +'.tqkl{font-family:var(--display);font-weight:600;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--steel);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
 +'.tqkv{font-family:var(--display);font-weight:700;font-size:21px;color:var(--chalk);font-variant-numeric:tabular-nums;line-height:1.05}.tqks{min-height:15px;font-size:11px;color:var(--steel)}'
 +'.tqr{font-style:normal;font-family:var(--display);font-weight:700;font-size:11.5px;letter-spacing:.03em;color:var(--label)}.tqr.gold{color:#e8c15a}.tqr.g{color:var(--win)}.tqr.b{color:#ff8a9a}'
 +'.thx2 .tqh{margin-top:20px}'
 # positions
 +'.tqpos{display:flex;flex-direction:column}.tqpr{display:grid;grid-template-columns:34px minmax(0,1fr) 44px 34px;align-items:center;gap:10px;min-height:34px;border-bottom:1px solid var(--hair)}'
 +'.tqpr .pz{justify-self:start}.tqbar{height:8px;border-radius:4px;background:var(--hair);overflow:hidden}.tqbar i{display:block;height:100%;border-radius:4px;background:var(--pc);opacity:.78}'
 +'.tqv{font-family:var(--display);font-weight:700;font-size:16px;color:var(--chalk);text-align:right;font-variant-numeric:tabular-nums}.tqv.z{color:var(--dim)}.tqpr .tqr{text-align:right}'
 # grids
 +'.tqgrid.sxm .sxr{grid-template-columns:58px repeat(var(--n),minmax(0,1fr)) 38px}.tqgrid.bym .sxr{grid-template-columns:58px repeat(var(--n),minmax(0,1fr))}'
 +'.tqgrid .mxn{font-size:12px;color:var(--steel)}'
 +'.tqgrid .sxr>span.tqwl{background:none!important;height:18px!important;font-size:12px!important}.tqwl.w{color:var(--win)!important}.tqwl.l{color:var(--loss)!important}'
 +'.hm.r1{box-shadow:inset 0 0 0 1.5px #e8c15a}.hm.r10{box-shadow:inset 0 0 0 1.5px rgba(255,93,115,.85)}'
 +'.tqstb .stt{display:flex;justify-content:space-between;gap:10px;font-size:12.5px;color:var(--steel);margin-bottom:8px}.tqstb .stt b{font-family:var(--display);font-size:16px;color:var(--chalk)}'
 +'.tqstb .stt b.ay{color:#6fc9a4}.tqstb .stt b.ap{color:#e2c27a}.tqstb .stt b.ao{color:#e58f9c}'
 # dropped
 +'.tqdp{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px}.tqdp>div{display:flex;flex-direction:column;align-items:center;gap:6px;padding:8px 0 6px;border-radius:8px;background:var(--deck);border:1px solid var(--hair)}'
 +'.tqdp .tqv{text-align:center}.tqmini{display:flex;align-items:flex-end;width:10px;height:28px;border-radius:3px;background:var(--hair);overflow:hidden}.tqmini i{display:block;width:100%;background:var(--pc);border-radius:3px}'
 # home / road
 +'.tqhr{display:flex;flex-direction:column;gap:10px;padding:12px;border-radius:10px;background:var(--deck);border:1px solid var(--hair);margin-bottom:6px}'
 +'.tqhr1{display:grid;grid-template-columns:auto auto minmax(0,1fr) auto auto;align-items:center;gap:8px}.tqhr1>b{font-family:var(--display);font-weight:700;font-size:18px;color:var(--chalk);font-variant-numeric:tabular-nums}'
 +'.tqhb{max-width:none!important;margin:0!important;height:8px!important;border-radius:4px}'
 +'.tqhr2{display:flex;align-items:baseline;gap:8px;font-size:12.5px;color:var(--steel)}.tqhr2 b{font-family:var(--display);font-weight:700;font-size:18px;color:var(--chalk)}'
 +'.tqhrt .sxr>span:first-child{font-size:12.5px;color:var(--label)}'
 +'.thx2 .bnl{grid-template-columns:44px 112px minmax(0,1fr)}.thx2 .bnl .bnt{display:block;white-space:nowrap;font-size:12.5px;color:var(--label);font-weight:500}.thx2 .bnl .bnt em{font-style:normal;font-family:var(--display);font-weight:700}'
 +'.thx2 .bnl .bnt em{display:inline-flex;align-items:center;justify-content:center;width:22px;height:17px;padding-bottom:1px;box-sizing:border-box;margin:0 5px 0 4px;border-radius:3px;background:rgba(238,240,244,.08);color:var(--label);font-size:11.5px;vertical-align:1px}'
 '.thx2 .bnl .bnt em.gold{color:#e8c15a;background:rgba(232,193,90,.14)}.thx2 .bnl .bnt em.g{color:var(--win);background:rgba(63,214,155,.12)}.thx2 .bnl .bnt em.b{color:#ff8a9a;background:rgba(255,93,115,.12)}'
 +'.tqnone{padding:10px 0;font-size:12.5px;color:var(--steel)}'
 # trends
 +'.tqsk{position:sticky;top:var(--navh,0px);z-index:5;background:var(--ink);padding-bottom:8px;margin-bottom:2px}.tqwk{display:grid;grid-template-columns:auto repeat('+str(G)+',minmax(0,1fr));align-items:center;gap:4px;padding:8px 0;margin:0 0 8px;background:var(--ink)}'
 +'.tqwk>span{font-family:var(--display);font-weight:600;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--steel);margin-right:4px}'
 +'.tqwk label{display:grid;place-items:center;height:32px;border-radius:8px;border:1px solid var(--hair);background:var(--deck);font-family:var(--display);font-weight:700;font-size:15px;color:var(--label);cursor:pointer}'
 +'.trd{margin:0}.trc{display:none;grid-template-columns:auto 26px auto minmax(0,1fr);justify-content:start;justify-items:start;align-items:center;column-gap:10px;padding:10px 12px;border-radius:10px;background:var(--deck);border:1px solid var(--hair)}'
 +'.trc span{font-family:var(--display);font-weight:600;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--steel)}.trc b{font-family:var(--display);font-weight:700;font-size:18px;color:var(--chalk);font-variant-numeric:tabular-nums}.trc em{font-style:normal;font-size:12.5px;color:var(--label);text-align:right}'
 +'.tcs{display:grid;grid-template-columns:minmax(0,1fr);gap:8px}@media(min-width:760px){.tcs{grid-template-columns:repeat(2,minmax(0,1fr))}}'
 +'.tch{padding:10px 12px 6px;border-radius:10px;background:var(--deck);border:1px solid var(--hair)}'
 +'.tchh{display:flex;align-items:baseline;gap:8px;margin-bottom:4px}.tchh>span:first-child{font-family:var(--display);font-weight:700;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--label);white-space:nowrap}'
 +'.tleg{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--steel);white-space:nowrap}.tleg i{width:14px;border-top:1.5px dashed var(--steel)}'
 +'.tro{display:none;margin-left:auto;font-family:var(--display);font-weight:700;font-size:17px;color:var(--chalk);white-space:nowrap;font-variant-numeric:tabular-nums}.tro small{font-size:12px;font-weight:600;color:var(--steel);margin-left:2px}.tro small.w{color:var(--win)}.tro small.l{color:var(--loss)}.tro small.w,.tro small.l{display:inline-block;width:1.1em;text-align:center}'
 +'.tsvg{display:block;width:100%;height:auto;overflow:visible}'
 +'.tgl{stroke:var(--hair);stroke-width:1}.tzero{stroke:var(--line-strong,rgba(255,255,255,.2));stroke-width:1}'
 +'.tax{font-family:var(--display);font-weight:600;font-size:10px;fill:var(--steel);font-variant-numeric:tabular-nums}'
 +'.tref{fill:none;stroke:var(--steel);stroke-width:1.25;stroke-dasharray:3 3;opacity:.8}'
 +'.tline{fill:none;stroke:var(--chalk);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}'
 +'.tarea.pos{fill:rgba(63,214,155,.16)}.tarea.neg{fill:rgba(255,93,115,.16)}'
 +'.tdot{fill:var(--deck);stroke:var(--chalk);stroke-width:1.5}.tdot.w{stroke:var(--win)}.tdot.l{stroke:var(--loss)}'
 +'.tline.c1{stroke:var(--chalk)}.tline.c2{stroke:#6fc9a4}.tline.c3{stroke:#e8c15a}.tdot.c1{stroke:var(--chalk)}.tdot.c2{stroke:#6fc9a4}.tdot.c3{stroke:#e8c15a}'
 +'.tsel.c1{fill:var(--chalk)}.tsel.c2{fill:#6fc9a4}.tsel.c3{fill:#e8c15a}'
 +'.trm{display:none;gap:10px}.trm b{font-family:var(--display);font-weight:700;font-size:16px;font-variant-numeric:tabular-nums}.trm b+b{margin-left:10px}.trm b small{font-size:11px;color:var(--steel);margin-left:1px}.trm b.c1{color:var(--chalk)}.trm b.c2{color:#6fc9a4}.trm b.c3{color:#e8c15a}'
 +'.tlg3{display:flex;gap:12px;margin:0 0 4px;font-size:11px;color:var(--steel)}.tlg3 span{display:inline-flex;align-items:center;gap:5px}.tlg3 i{width:14px;height:2px;border-radius:1px;background:currentColor}.tlg3 .c1 i{background:var(--chalk)}.tlg3 .c2 i{background:#6fc9a4}.tlg3 .c3 i{background:#e8c15a}'
 +'.tqby{stroke:#8ec5ff;stroke-width:1;opacity:.55;stroke-dasharray:4 3}.tqpo{stroke:var(--chalk);stroke-width:1;opacity:.4;stroke-dasharray:4 3}'
 +'.tqbyt{font-family:var(--display);font-weight:600;font-size:9px;letter-spacing:.06em;text-transform:uppercase;fill:#8ec5ff;opacity:.8}.tqpot{font-family:var(--display);font-weight:600;font-size:9px;letter-spacing:.06em;text-transform:uppercase;fill:var(--chalk);opacity:.6}'
 +'.tsvg{cursor:pointer;touch-action:pan-y;-webkit-tap-highlight-color:transparent;user-select:none;-webkit-user-select:none}'
 +'@media (max-width:440px){.trc .trw{display:none}.trc{column-gap:9px;grid-template-columns:26px auto minmax(0,1fr)!important}}.trc>.tqt{justify-self:center}.trc .tro2 b{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;white-space:normal!important;line-height:1.15}'
 +'.trc .trw{min-width:5.2em;font-family:var(--display);font-weight:700;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--label);white-space:nowrap}' +'.trc .trs{font-family:var(--display);font-weight:700;font-size:20px;color:var(--chalk);font-variant-numeric:tabular-nums;white-space:pre;min-width:11.7ch}' +'.trc .tro2{display:inline-flex;align-items:center;gap:7px;min-width:0;font-family:var(--body);font-weight:600;font-size:14.5px;letter-spacing:0;text-transform:none;color:var(--chalk)}.trc .tro2 em{font-style:normal;font-family:var(--display);font-weight:700;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--steel)}' +'.trc .tro2 b{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}.trc .pav{display:block;flex:none;width:24px;height:24px;border-radius:50%;background-color:var(--deck-2);background-position:center;background-size:cover;box-shadow:0 0 0 1px var(--hair)}.trc .pav.nl{display:none}' +'.tqt{display:inline-block;border-radius:4px;background:var(--hair);color:var(--label);font-family:var(--display);font-weight:700;font-style:normal;line-height:1;vertical-align:middle}' +'.tqt.gold{background:rgba(244,196,81,.16);color:#f4c451;box-shadow:inset 0 0 0 1px rgba(244,196,81,.45)}.tqt.g,.tqt.w{background:var(--win-bg);color:var(--win)}.tqt.b,.tqt.l{background:var(--loss-bg);color:var(--loss)}.tqt.last{box-shadow:inset 0 0 0 1px rgba(255,93,115,.55)}' +'.tqt.tby{background:rgba(255,122,26,.16);color:var(--pylon)}.tqt.tpo{background:rgba(142,197,255,.14);color:var(--sky)}' +'.trm small{font-family:var(--body);font-size:10.5px;font-weight:500;color:var(--steel);margin:0 8px 0 4px}.trm small:last-child{margin-right:0}' +'.tline.c4{stroke:var(--steel);stroke-dasharray:4 3}.tsel.c4{fill:var(--steel)}.tline.c5{stroke:#ff8a9a}.tsel.c5{fill:#ff8a9a}.tlg3 .c4 i{background:var(--steel)}.tlg3 .c5 i{background:#ff8a9a}.trm b.c4{color:var(--steel)}' +'.tline.p-qb{stroke:#ff6f9c}.tline.p-rb{stroke:#3fd6b5}.tline.p-wr{stroke:#5cc0ff}.tline.p-te{stroke:#ffa95c}.tsel.p-qb{fill:#ff6f9c}.tsel.p-rb{fill:#3fd6b5}.tsel.p-wr{fill:#5cc0ff}.tsel.p-te{fill:#ffa95c}' +'.tlg3 .p-qb i{background:#ff6f9c}.tlg3 .p-rb i{background:#3fd6b5}.tlg3 .p-wr i{background:#5cc0ff}.tlg3 .p-te i{background:#ffa95c}.trm b.p-qb{color:#ff6f9c}.trm b.p-rb{color:#3fd6b5}.trm b.p-wr{color:#5cc0ff}.trm b.p-te{color:#ffa95c}' +'.tband{stroke:none}.tband.b1{fill:rgba(127,166,255,.34)}.tband.b2{fill:rgba(255,138,61,.42)}.tband.b3{fill:rgba(244,196,81,.55)}.tline.b1{stroke:#7fa6ff}.tline.b2{stroke:#ff8a3d}.tline.b3{stroke:#f4c451}.tsel.b1{fill:#7fa6ff}.tsel.b2{fill:#ff8a3d}.tsel.b3{fill:#f4c451}' +'.tlg3 .b1 i{background:#7fa6ff}.tlg3 .b2 i{background:#ff8a3d}.tlg3 .b3 i{background:#f4c451}.trm b.b1{color:#7fa6ff}.trm b.b2{color:#ff8a3d}.trm b.b3{color:#f4c451}.tlg3 .tref i{background:none;border-top:1.5px dashed var(--steel);height:0}'
 +'.twm{display:none}.tcur{stroke:'+TL+';stroke-width:1;opacity:.55}.tsel{fill:'+TL+';stroke:var(--deck);stroke-width:2}.tsel.w{fill:var(--win)}.tsel.l{fill:var(--loss)}')
open(P+'th_section.html','w',encoding='utf-8').write(sec_)
css+=('.tqew{display:grid;grid-template-columns:1fr 1fr;column-gap:14px}'
      '.tqew>div{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 0;border-top:1px solid var(--hair);min-width:0}'
      '.tqew>div:nth-child(-n+2){border-top:0}'
      '.tqew span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:var(--label)}'
      '.tqew b{flex:none;font-family:var(--display);font-weight:700;font-size:15px;font-variant-numeric:tabular-nums;color:var(--steel)}'
      '.tqew b.up{color:var(--win)}.tqew b.dn{color:#ff8a9a}')
open(P+'th_css.css','w',encoding='utf-8').write(css)
if __name__=='__main__':
    t=H[1];print(t,{k:[round(x,2) if isinstance(x,float) else x for x in v] for k,v in SER[t].items()})
