import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Weekly team assessment, generated from the same data as the page (rebuilds automatically each update).
# assess_html(team) -> HTML card placed at the bottom of that team's roster panel.
import json,re,html,statistics as stt
from datetime import date
P=__DTP__+''
import sys as _s0;_s0.path.insert(0,P);import lg
e=html.escape
_s=open(P+'data_block.js',encoding='utf-8').read()
def _g(k):return json.loads(re.search(r'const '+k+r'=(.*?);\n',_s).group(1))
T=_g('T');WK=_g('WK');FUT=_g('FUT');PH=_g('PH');PM=_g('PM')
EF={k:v for k,v in json.load(open(P+'eff.json')).items()}
_sk=json.load(open(P+'skill_opt.json'));_sk.pop('_note',None)
X=json.load(open(P+'cmp_extra.json',encoding='utf-8'))
K=json.load(open(P+'ro_ranks.json'));BYE=K.pop('_bye');PG=json.load(open(P+'ro_pg.json'))
R0=json.load(open(P+'rosters.json',encoding='utf-8'))
def _norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip();return {'RIPMFL':'Team RIPMFL'}.get(n,n)
R={_norm(k):v for k,v in R0.items()}
TEAMS=list(T)
G=len(WK[TEAMS[0]]);NOW=G+1;FIN=not any(FUT.values())
RID={v:int(k) for k,v in X['rn'].items()}
SHORT=dict(lg.SHORT)
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
FN=lambda n:lg.FULL.get(n,n)
# Owner's stated dynasty holds: never flagged as surplus or drop candidates.
HOLDS={}
def age(pid):
    b=X['age'].get(pid)
    if not b:return None
    y,m,d=map(int,b.split('-'));return (date.today()-date(y,m,d)).days/365.25
def ordn(n):return f'{n}{"th" if 10<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10,"th")}'
def rank(vals,t,desc=True):
    o=sorted(vals,key=lambda k:-vals[k] if desc else vals[k]);return o.index(t)+1
pg=lambda p:p[4]/p[6] if p[6] else 0
def act(t):return [p for p in R[t] if p[7]!='TX']
def by(t,pos):return sorted([p for p in act(t) if p[2]==pos and p[7]!='IR'],key=lambda p:-p[4])
NEED=dict(lg.CORE)
POSN={'QB':'QB','RB':'RB','WR':'WR','TE':'TE','K':'Kicker','DEF':'Defence'}
GRP={t:{pos:sum(p[4] for p in by(t,pos)[:n]) for pos,n in NEED.items()} for t in TEAMS}
GRANK={t:{pos:rank({k:GRP[k][pos] for k in TEAMS},t) for pos in NEED} for t in TEAMS}
GAVG={pos:sum(GRP[k][pos] for k in TEAMS)/10 for pos in NEED}
STD={t:stt.pstdev([w[2] for w in WK[t]]) for t in TEAMS}
FLOOR={t:min(w[2] for w in WK[t]) for t in TEAMS}
AGE={t:sum(a for a in (age(p[0]) for p in R[t]) if a)/max(1,len([1 for p in R[t] if age(p[0])])) for t in TEAMS}
own={}
_Y=int(_dt_os.environ.get('DT_SEASON','2026'))
YRS=[str(_Y+1),str(_Y+2),str(_Y+3)]
for y in YRS:
    for r in range(1,5):
        for o in range(1,11):own[(y,r,o)]=o
for y,r,o,ow in X['tp']:
    if y in YRS:own[(y,r,o)]=ow
FIRSTS={t:sorted([k for k,v in own.items() if v==RID[t] and k[1]==1]) for t in TEAMS}
LGPF=sum(T[k][3] for k in TEAMS)/(10*G)
def pl(p,mode='pts'):
    rk=(K.get(p[0]) or [None])[0];gk=(PG.get(p[0]) or [None])[0]
    if not rk or p[2] in('K','DEF'):return e(p[1])
    return f'{e(p[1])} ({p[2]}{rk}' + (f', {p[2]}{gk} per game)' if gk and rk-gk>=8 else ')')

HI=json.load(open(P+'hist.json'));HM=HI['m']
def _parse(sx):
    o=[]
    for x in sx.split(','):
        if not x:continue
        f=x.split('|');pos,name=HM.get(f[0],['DEF' if not f[0].isdigit() else '?',f[0]])
        o.append(dict(pid=f[0],pos=pos,name=name,proj=float(f[2]),pts=float(f[3])))
    return o
def _opt(pool):return lg.optsum(pool)
def lastweek(t):
    w=WK[t][-1];d=HI['w'][str(G)][str(RID[t])]
    st=_parse(d[2]);bn=_parse(d[3])
    sc=sum(q['pts'] for q in st);pj=sum(q['proj'] for q in st)
    assert abs(sc-w[2])<0.02,(t,sc,w[2])
    top=max(st,key=lambda q:q['pts']);flop=min([q for q in st if q['pos'] not in('K','DEF')],key=lambda q:q['pts']-q['proj'])
    lost=_opt(st+bn)-sc
    res='W' if w[2]>w[3] else 'L'
    strk=0
    for x in reversed(WK[t]):
        if ('W' if x[2]>x[3] else 'L')==res:strk+=1
        else:break
    return dict(wk=G,res=res,sc=w[2],op=w[3],opp=w[1],rk=w[4],pj=pj,top=top,flop=flop,lost=lost,strk=strk)
def assess(t):
    w,l,_,pf,pfr,pfa,pa,par,_,_,apw,apl,luck=T[t]
    hr=PH.index(t)+1;mr=PM.index(t)+1
    apx=apw/(apw+apl)*G;apr=rank({k:T[k][10] for k in TEAMS},t)
    ef=EF[t];efr=rank({k:EF[k][0] for k in TEAMS},t)
    stdr=rank(STD,t);flr=rank(FLOOR,t)
    ager=rank(AGE,t,desc=False)
    fut=FUT[t];xw=sum(f[4] for f in fut)/100;fw=w+xw;fl=G+len(fut)-fw
    good=[];bad=[]
    # results vs underlying
    if pfr<=3:good.append((9-pfr,f'Scoring {pfa:.1f}/wk, {ordn(pfr)} in the league ({pfa-LGPF:+.1f} vs average).'))
    if pfr>=lg.N-2:bad.append((pfr,f'Scoring {pfa:.1f}/wk, {ordn(pfr)} in the league ({pfa-LGPF:+.1f} vs average).'))
    if apx-w>=0.75:good.append((7,f'Better than the record: all-play {apw}-{apl} points to about {apx:.1f} wins, not {w}.'))
    if w-apx>=0.75:bad.append((7,f'Record flatters: all-play {apw}-{apl} points to about {apx:.1f} wins, not {w}.'))
    if apr<=2 and not any('all-play' in x for _,x in good):good.append((6,f'All-play {apw}-{apl}, '+('best in the league.' if apr==1 else f'{ordn(apr)} best.')))
    if par<=2:bad.append((4,f'Faced the {"most" if par==1 else "2nd-most"} points against ({pa/G:.1f}/wk).'))
    if par>=lg.N-1:good.append((3,f'Faced the {"fewest" if par==lg.N else "2nd-fewest"} points against ({pa/G:.1f}/wk) – some schedule luck.'))
    if stdr>=lg.N-1:good.append((5,f'Steady: {"lowest" if stdr==lg.N else "2nd-lowest"} week-to-week swing, floor {FLOOR[t]:.1f}.'))
    if stdr<=2:bad.append((5,f'Volatile: {"highest" if stdr==1 else "2nd-highest"} week-to-week swing ({FLOOR[t]:.1f} to {max(x[2] for x in WK[t]):.1f}).'))
    if flr==1 and stdr<9:good.append((5,f'Highest floor in the league ({FLOOR[t]:.1f}).'))
    if efr<=2:good.append((5,f'Sharp lineups: {ef[0]:.1f}% of max points, {ordn(efr)} in the league.'))
    if efr>=lg.N-2:bad.append((5,f'Lineup leaks: {ef[1]:.1f} pts/wk left on the bench ({ordn(efr)} in efficiency).'))
    # position groups
    for pos in lg.POS:
        r=GRANK[t][pos];top=by(t,pos)[:NEED[pos]]
        names=', '.join(pl(p) for p in top) if top else 'none'
        lab=POSN[pos]+(' room' if pos in('QB','RB','WR','TE') else '')
        if r<=2 and pos not in('K',):good.append((8 if pos in('RB','WR') else 6,f'{lab} {ordn(r)}: {names}.'))
        if r>=lg.N-1 and pos not in('K','DEF'):bad.append((8 if pos in('RB','WR','QB') else 6,f'{lab} {ordn(r)} ({GRP[t][pos]:.0f} pts vs {GAVG[pos]:.0f} avg): {names}.'))
    # QB depth / surplus (1-QB league)
    qbs=[p for p in act(t) if p[2]=='QB' and p[7]!='IR']
    good_q=[p for p in qbs if (PG.get(p[0]) or [99])[0]<=15]
    if len(good_q)>=2:
        bad.append((4,f'QB surplus in a 1-QB league: {", ".join(pl(p) for p in good_q)} – trade value on the bench.'))
    if len(qbs)==1:
        b=BYE.get(qbs[0][3]);bad.append((7,f'One active QB ({e(qbs[0][1])})'+(f'; {qbs[0][3]} bye in Week {b}.' if b and b>=NOW else '.')))
    # IR on notable players
    ir=[p for p in R[t] if p[7]=='IR' and (K.get(p[0]) or [999])[0]<=24]
    if ir:bad.append((4,'On IR: '+', '.join(pl(p) for p in ir)+'.'))
    # ageing core with / without successor
    core=[p for pos,n in NEED.items() if pos not in('K','DEF') for p in by(t,pos)[:n]]
    for p in core:
        a=age(p[0])
        if a and a>=31:
            succ=sorted([q for q in R[t] if q[2]==p[2] and q is not p and age(q[0]) and age(q[0])<=27.5 and a-age(q[0])>=5],key=lambda q:-q[4])
            if succ:good.append((2,f'{e(p[1])} ({a:.1f}) has a successor in place: {e(succ[0][1])} ({age(succ[0][0]):.1f}).'))
            else:bad.append((3,f'Age risk: {e(p[1])} is {a:.1f} with no young {p[2]} behind him.'))
    # byes still ahead: weeks with 2+ core starters out
    bw={}
    for p in core:
        b=BYE.get(p[3])
        if b and b>=NOW:bw.setdefault(b,[]).append(p[1].split(' ')[-1] if p[2]!='DEF' else p[1])
    for b in sorted(bw):
        if len(bw[b])>=2:bad.append((3,f'Week {b} bye crunch: {", ".join(e(x) for x in bw[b])}.'))
    # dynasty
    if ager<=3:good.append((4,f'Young roster (avg {AGE[t]:.1f}, {ordn(ager)}-youngest).'))
    if ager>=lg.N-2:bad.append((3,f'Older roster (avg {AGE[t]:.1f}, {ordn(lg.N+1-ager)}-oldest).'))
    nf=len(FIRSTS[t])
    if nf>=4:good.append((6,f'Draft capital: {nf} 1sts in {YRS[0]}–{YRS[2][2:]} ('+', '.join(f"{y} {SHORT[X['rn'][str(o)]]}" for y,_,o in FIRSTS[t])+').'))
    if nf==0:bad.append((6,f'No 1st-round picks in {YRS[0]}, {YRS[1]} or {YRS[2]}.'))
    # schedule
    hard=min(fut,key=lambda f:f[4]) if fut else None;easy=sum(1 for f in fut if f[4]>=70)
    if fut and xw>=5:good.append((5,f'Soft run-in: ~{xw:.1f} projected wins left, {easy} of {len(fut)} games at 70%+.'))
    if fut and xw<=3:bad.append((5,f'Tough run-in: ~{xw:.1f} projected wins left; hardest is Wk {hard[0]} vs {e(FN(hard[1]))} ({hard[4]}%).'))
    star=max(act(t),key=lambda p:(p[2] not in('K','DEF'),p[4]))
    good.append((1,f'Best player: {pl(star)}, {star[4]:.1f} pts.'))
    good.sort(key=lambda x:-x[0]);bad.sort(key=lambda x:-x[0])
    # verdict
    seed=min(hr,mr)
    if FIN:tier,tc=(('Contender','tc') if apr<=2 else ('Playoff team','tp')) if hr<=lg.PO else ('Missed playoffs','tl')
    elif apr<=2:tier,tc='Contender','tc'
    elif hr<=lg.PO and fw>=7.5:tier,tc='Playoff team','tp'
    elif hr<=lg.PO or fw>=6.5:tier,tc='Bubble','tb'
    else:tier,tc='Long shot','tl'
    fr=f'{round(fw)}-{round(fl)}'
    return dict(tier=tier,tc=tc,good=[x for _,x in good[:5]],bad=[x for _,x in bad[:5]],
        stats=[('Record',f'{w}-{l}',f'{ordn(hr)} H2H'),('Pts/wk',f'{pfa:.1f}',f'{ordn(pfr)}'),('All-play',f'{apw}-{apl}',f'{ordn(apr)}'),(('Seed',f'{hr}','final') if FIN else ('Projected',fr,f'+{xw:.1f} W'))])
def assess_html(t):
    a=assess(t)
    st=''.join(f'<span><em>{k}</em><b>{v}</b><i>{s}</i></span>' for k,v,s in a['stats'])
    li=lambda xs:''.join(f'<li>{x}</li>' for x in xs) or '<li>Nothing stands out.</li>'
    L=lastweek(t);ln=lambda q:e(q['name'].split(' ',1)[-1] if q['pos']!='DEF' else q['name'])
    lead=(f'<div class="ral"><div class="ralh"><b class="{"up" if L["res"]=="W" else "dn"}">{L["res"]}</b><span>Week {L["wk"]} · {L["sc"]:.1f}–{L["op"]:.1f} vs {e(FN(L["opp"]))}</span></div>'
          f'<p>{"Top score" if L["rk"]==1 else ordn(L["rk"])+"-highest score"} of the week, {("+" if L["sc"]>=L["pj"] else "−")+f"{abs(L['sc']-L['pj']):.1f}"} vs projection. '
          f'Top scorer {ln(L["top"])} ({L["top"]["pts"]:.1f}); biggest miss {ln(L["flop"])} ({L["flop"]["pts"]:.1f} vs {L["flop"]["proj"]:.1f} proj). '
          + (f'Optimal lineup would have scored {L["lost"]:.1f} more. ' if L['lost']>=0.05 else 'Started the optimal lineup. ')
          + f'{L["strk"]}&#8209;game {"winning" if L["res"]=="W" else "losing"} streak.</p></div>' if L['strk']>=2 else
          f'<div class="ral"><div class="ralh"><b class="{"up" if L["res"]=="W" else "dn"}">{L["res"]}</b><span>Week {L["wk"]} · {L["sc"]:.1f}–{L["op"]:.1f} vs {e(FN(L["opp"]))}</span></div>'
          f'<p>{"Top score" if L["rk"]==1 else ordn(L["rk"])+"-highest score"} of the week, {("+" if L["sc"]>=L["pj"] else "−")+f"{abs(L['sc']-L['pj']):.1f}"} vs projection. '
          f'Top scorer {ln(L["top"])} ({L["top"]["pts"]:.1f}); biggest miss {ln(L["flop"])} ({L["flop"]["pts"]:.1f} vs {L["flop"]["proj"]:.1f} proj). '
          + (f'Optimal lineup would have scored {L["lost"]:.1f} more.' if L['lost']>=0.05 else 'Started the optimal lineup.')+'</p></div>')
    return (f'<div class="ras"><div class="rah"><b>Team assessment</b><i class="rat {a["tc"]}">{a["tier"]}</i></div>'+lead+
            f'<div class="rash">{"Regular season" if FIN else "Season to date"}</div>'
            f'<div class="rak">{st}</div>'
            f'<div class="rag up"><h4>Strengths</h4><ul>{li(a["good"])}</ul></div>'
            f'<div class="rag dn"><h4>Concerns</h4><ul>{li(a["bad"])}</ul></div>'+
            (f'<div class="ran">Weeks 1–{G} results and end-of-season rosters</div></div>' if FIN else f'<div class="ran">Weeks 1–{G} results, current rosters and app win projections · refreshed with each update</div></div>'))
if __name__=='__main__':
    import re as _r
    for t in TEAMS:print(_r.sub('<[^>]+>',' ',assess_html(t))[:420]);print()
    raise SystemExit
    for t in TEAMS:
        a=assess(t);print('\n==',t,a['tier'],a['stats']);[print(' +',x) for x in a['good']];[print(' -',x) for x in a['bad']]
