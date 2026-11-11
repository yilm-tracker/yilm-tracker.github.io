import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Analysis for the Stats tab modules. Pure data; sx_build.py renders it.
import json,re,statistics as stt
from datetime import date,datetime,timezone,timedelta
import numpy as np
P=__DTP__+''
import sys as _s0;_s0.path.insert(0,P);import lg
_s=open(P+'data_block.js',encoding='utf-8').read()
def _g(k):return json.loads(re.search(r'const '+k+r'=(.*?);\n',_s).group(1))
T=_g('T');WK=_g('WK');FUT=_g('FUT');PH=_g('PH')
TEAMS=list(T);G=len(WK[TEAMS[0]]);NOW=G+1
X=json.load(open(P+'cmp_extra.json',encoding='utf-8'))
RN={int(k):v for k,v in X['rn'].items()};RID={v:k for k,v in RN.items()}
SHORT=dict(lg.SHORT)
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
CODE=dict(lg.CODE)
FROM_SHORT=dict(lg.FULL)
HI=json.load(open(P+'hist.json'));HM=HI['m']
AGE=dict(X['age']);AGE.update(json.load(open(P+'age_extra.json')))
R0=json.load(open(P+'rosters.json',encoding='utf-8'))
def _norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip();return {'RIPMFL':'Team RIPMFL'}.get(n,n)
R={_norm(k):v for k,v in R0.items()}
K=json.load(open(P+'ro_ranks.json'));BYE=K.pop('_bye')
def age(pid,on=None):
    on=on or date.today()
    b=AGE.get(pid)
    if not b:return None
    y,m,d=map(int,b.split('-'));return (on-date(y,m,d)).days/365.25
def parse(sx):
    o=[]
    for x in sx.split(','):
        if not x:continue
        f=x.split('|');pos,name=HM.get(f[0],['?',f[0]])
        o.append(dict(pid=f[0],pos=pos,name=name,nfl=f[1],proj=float(f[2]),pts=float(f[3])))
    return o
def lineup(t,w):
    d=HI['w'][str(w)][str(RID[t])];return parse(d[2]),parse(d[3])
def optimal(pool):return [q for q in lg.optimal(pool) if q is not None]
def dropped(t):
    """points per week left on the bench, by position: each optimal-lineup player who didn't start is paired with the
    starter he replaces (same position first, then a flex-eligible one, else an empty slot) and credited to his position"""
    a={k:0.0 for k in ('QB','RB','WR','TE','K','DEF')}
    for w in range(1,G+1):
        st,bn=lineup(t,w);op=optimal(st+bn);ids={q['pid'] for q in st};oi={q['pid'] for q in op}
        ins=sorted([q for q in op if q['pid'] not in ids],key=lambda q:-q['pts']);outs=sorted([q for q in st if q['pid'] not in oi],key=lambda q:q['pts'])
        fx=lambda p:any(p in v for v in lg.FLEXES.values())
        for i in ins:
            c=[o for o in outs if o['pos']==i['pos']] or [o for o in outs if any(i['pos'] in v and o['pos'] in v for v in lg.FLEXES.values())] or outs
            o=c[0] if c else None
            if o:outs.remove(o)
            a[i['pos']]+=i['pts']-(o['pts'] if o else 0)
    return {k:v/G for k,v in a.items()}
def result(t,w):
    x=WK[t][w-1];return x[2],x[3],FROM_SHORT[x[1]]
# integrity: starters sum to recorded score
for t in TEAMS:
    for w in range(1,G+1):
        st,_=lineup(t,w);assert abs(sum(q['pts'] for q in st)-WK[t][w-1][2])<0.02,(t,w)

# ---------- 1. playoff odds
def odds(n=20000,seed=7):
    rng=np.random.default_rng(seed)
    sc={t:np.array([w[2] for w in WK[t]]) for t in TEAMS}
    lgm=np.mean(np.concatenate(list(sc.values())))
    pooled=np.mean([np.var(sc[t]) for t in TEAMS])
    mu={t:0.65*sc[t].mean()+0.35*lgm for t in TEAMS}
    sd={t:float(np.sqrt(0.5*np.var(sc[t])+0.5*pooled)) for t in TEAMS}
    idx={t:i for i,t in enumerate(TEAMS)}
    weeks=sorted({f[0] for t in TEAMS for f in FUT[t]})
    W=np.tile(np.array([T[t][0] for t in TEAMS],float),(n,1));PF=np.tile(np.array([T[t][3] for t in TEAMS],float),(n,1))
    for wk in weeks:
        S=np.stack([rng.normal(mu[t],sd[t],n) for t in TEAMS],axis=1)
        PF+=S;seen=set()
        for t in TEAMS:
            f=[x for x in FUT[t] if x[0]==wk]
            if not f or t in seen:continue
            o=FROM_SHORT[f[0][1]];seen|={t,o}
            a,b=idx[t],idx[o];W[:,a]+=S[:,a]>S[:,b];W[:,b]+=S[:,b]>S[:,a]
    key=W*10000+PF  # wins, then points for
    order=np.argsort(-key,axis=1);seed_of=np.empty_like(order)
    rows=np.arange(n)[:,None];seed_of[rows,order]=np.arange(lg.N)[None,:]
    out={}
    for t in TEAMS:
        i=idx[t];s=seed_of[:,i]
        out[t]=dict(po=float((s<lg.PO).mean()*100),bye=float((s<lg.BYE_N).mean()*100),top=float((s==0).mean()*100),
                    w=float(W[:,i].mean()),dist=[float((s==k).mean()*100) for k in range(lg.N)])
    return out,dict(n=n,weeks=weeks,lg=float(lgm))
def simgame(a,b):
    """this week's game under the playoff-odds model (each score ~ Normal(65% own average + 35% league average,
    blended spread)): the model's expected points for each side and a's win chance (what the 20,000 runs converge to)"""
    from math import erf,sqrt
    sc={t:np.array([w[2] for w in WK[t]]) for t in TEAMS};lgm=np.mean(np.concatenate(list(sc.values())))
    pooled=np.mean([np.var(sc[t]) for t in TEAMS])
    mu=lambda t:0.65*sc[t].mean()+0.35*lgm;sd=lambda t:float(np.sqrt(0.5*np.var(sc[t])+0.5*pooled))
    ma,mb=float(mu(a)),float(mu(b));z=(ma-mb)/sqrt(sd(a)**2+sd(b)**2)
    return ma,mb,0.5*(1+erf(z/sqrt(2)))
# ---------- 2. schedule swap
def everyweek():
    """record if a played b every week: a's score vs b's score in each week 1..G -> {a:{b:(w,l,t)}}"""
    E={}
    for a in TEAMS:
        E[a]={}
        for b in TEAMS:
            if a==b:continue
            s=[(WK[a][w][2],WK[b][w][2]) for w in range(G)]
            E[a][b]=(sum(x>y for x,y in s),sum(x<y for x,y in s),sum(x==y for x,y in s))
    return E
def schedswap():
    M={}
    for a in TEAMS:
        M[a]={}
        for b in TEAMS:
            wn=0
            for w in range(1,G+1):
                opp=result(b,w)[2]
                mine=WK[a][w-1][2]
                theirs=WK[b][w-1][2] if opp==a else WK[opp][w-1][2]
                wn+=mine>theirs
            M[a][b]=wn
    return M
# ---------- 3. trades
K1=datetime(2026,9,13,17,0,tzinfo=timezone.utc)  # Sunday 1pm ET of Week 1; a trade counts from the first Sunday slate after it
def eff_week(ts):
    d=datetime.fromtimestamp(ts/1000,timezone.utc)
    for k in range(1,19):
        if d<K1+timedelta(days=7*(k-1)):return k
    return 19
RD={1:'1st',2:'2nd',3:'3rd',4:'4th'}
def trades():
    out=[]
    for x in sorted(X['tx'],key=lambda x:-x['ts']):
        k=eff_week(x['ts']);rids=list(x['rids'])  # two or more teams
        side={r:dict(pl=[],pk=[],faab=0) for r in rids}
        for pid,to in (x['adds'] or {}).items():
            nm,pos,nfl=X['txp'][pid];wk=X['txw'][pid];pts=sum(wk[k-1:G]) if k<=G else 0.0
            side[to]['pl'].append(dict(name=nm,pos=pos,nfl=nfl,pts=round(pts,2)))
        for y,r,o,new,prev in x['picks']:
            side[new]['pk'].append(f'{y} {RD[r]} ({SHORT[RN[o]]})')
        for f in x['faab']:side[f['receiver']]['faab']+=f['amount']
        out.append(dict(ts=x['ts'],date=datetime.fromtimestamp(x['ts']/1000,timezone.utc).strftime('%b %-d'),eff=k,
            sides=[dict(team=RN[r],**side[r],tot=round(sum(p['pts'] for p in side[r]['pl']),2)) for r in rids]))
    return out
# ---------- 4. lineup decisions
FLEX={'RB','WR','TE'}
def decisions():
    rows=[];per={t:dict(flip=0,lost=0.0) for t in TEAMS}
    for t in TEAMS:
        for w in range(1,G+1):
            st,bn=lineup(t,w);op=optimal(st+bn)
            sc=sum(q['pts'] for q in st);best=sum(q['pts'] for q in op)
            me,them,opp=result(t,w);flip=me<them and best>them
            per[t]['lost']+=best-sc;per[t]['flip']+=flip
            ids={q['pid'] for q in st};oids={q['pid'] for q in op}
            ins=sorted([q for q in op if q['pid'] not in ids],key=lambda q:-q['pts'])
            outs=sorted([q for q in st if q['pid'] not in oids],key=lambda q:q['pts'])
            for i in ins:
                cand=[o for o in outs if o['pos']==i['pos'] or (i['pos'] in FLEX and o['pos'] in FLEX)]
                if not cand:continue
                o=cand[0];outs.remove(o)
                rows.append(dict(team=t,w=w,opp=opp,bench=i,start=o,swing=i['pts']-o['pts'],flip=flip,me=me,them=them,best=best))
    rows.sort(key=lambda r:-r['swing'])
    return rows,per
# ---------- 5. projections
def projections():
    tm={};pl={}
    for t in TEAMS:
        d=[];beat=0
        for w in range(1,G+1):
            st,_=lineup(t,w);a=sum(q['pts'] for q in st);p=sum(q['proj'] for q in st);d.append(a-p);beat+=a>p
            for q in st:
                if q['pos'] in('K','DEF'):continue
                r=pl.setdefault((q['pid']),dict(name=q['name'],pos=q['pos'],nfl=q['nfl'],team=t,n=0,diff=0.0,pts=0.0))
                r['n']+=1;r['diff']+=q['pts']-q['proj'];r['pts']+=q['pts'];r['team']=t
        tm[t]=dict(avg=sum(d)/G,beat=beat)
    P3=[dict(r,avg=r['diff']/r['n']) for r in pl.values() if r['n']>=3]
    P3.sort(key=lambda r:-r['avg'])
    return tm,P3[:6],P3[::-1][:6]
# ---------- 6. close games
def close():
    out={};games=[]
    for t in TEAMS:
        c=[0,0];bl=[0,0]
        for w in range(1,G+1):
            me,them,opp=result(t,w);m=me-them
            if m and round(abs(m),2)<=10:c[0 if m>0 else 1]+=1  # close = 10.00 or less (2026-11-10; was under 10)
            if abs(m)>=30:bl[0 if m>0 else 1]+=1
            if m>0:games.append(dict(w=w,win=t,lose=opp,ws=me,ls=them,m=m))
        out[t]=dict(close=c,blow=bl,avgm=sum(result(t,w)[0]-result(t,w)[1] for w in range(1,G+1))/G)
    games.sort(key=lambda g:g['m'])
    return out,games[:5],games[::-1][:3]
# ---------- 7. star dependence (points scored while in the starting lineup)
def stars():
    out={}
    for t in TEAMS:
        c={}
        for w in range(1,G+1):
            st,_=lineup(t,w)
            for q in st:c.setdefault(q['pid'],[q['name'],q['pos'],0.0]);c[q['pid']][2]+=q['pts']
        tot=sum(v[2] for v in c.values());top=sorted(c.values(),key=lambda v:-v[2])
        out[t]=dict(tot=tot,top1=top[0],s1=top[0][2]/tot*100,s3=sum(v[2] for v in top[:3])/tot*100,top3=top[:3])
        assert abs(tot-T[t][3])<0.05,(t,tot,T[t][3])
    return out
# ---------- 8. youth production
def youth():
    out={}
    for t in TEAMS:
        b=[0.0,0.0,0.0,0.0]  # <=25, 26-29, 30+, DEF/unknown
        for w in range(1,G+1):
            st,_=lineup(t,w)
            for q in st:
                a=age(q['pid'])
                if a is None:b[3]+=q['pts']
                else:b[0 if a<26 else 1 if a<30 else 2]+=q['pts']
        tot=sum(b);out[t]=dict(b=b,pct=[x/tot*100 for x in b],tot=tot)
    return out
# ---------- 9. weekly rank heatmap
def heat():return {t:[w[4] for w in WK[t]] for t in TEAMS}
# ---------- 10. bye exposure (core starters by season points, current rosters)
NEED=dict(lg.CORE)
def byes():
    out={}
    for t in TEAMS:
        act=[p for p in R[t] if not p[7]]
        core=[p for pos,n in NEED.items() for p in sorted([p for p in act if p[2]==pos],key=lambda p:-p[4])[:n]]
        out[t]={w:[p for p in core if BYE.get(p[3])==w] for w in range(NOW,15)}
    return out
# ---------- 2026-11-10 form, close games, remaining schedule, prime-time sweat, perfect-lineup record (identical in both repos)
# Exact arithmetic: every score is read as a Fraction of its 2-decimal value and rounded half-up only for display.
from fractions import Fraction as _F
from decimal import Decimal as _D,ROUND_HALF_UP as _RHU
import os as _os
def _fx(v):return _F(str(v))
def q2(x,n=2):
    x=x if isinstance(x,_F) else _fx(x)
    return float((_D(x.numerator)/_D(x.denominator)).quantize(_D(1).scaleb(-n),rounding=_RHU))
REGW=int(getattr(globals().get('lg'),'REG',14))   # last regular-season week
HSEED=_g('H')                                      # H2H standings order (the Standings board's own array)
def seed(t):return HSEED.index(t)+1
def _sc(t,w):return _fx(WK[t][w-1][2])
def _op(t,w):return FROM_SHORT[WK[t][w-1][1]]
FORM_N=4
def form(n=FORM_N):
    """points over the last n completed weeks (fewer early on), ranked high to low, against the H2H seed.
    diff = seed - form rank: positive = playing better than the standings say."""
    wk=list(range(max(1,G-n+1),G+1))
    if not wk:return dict(weeks=[],rows=[])
    tot={t:sum(_sc(t,w) for w in wk) for t in TEAMS}
    rows=[]
    for t in sorted(TEAMS,key=lambda t:(-tot[t],seed(t))):
        r=1+sum(1 for u in TEAMS if tot[u]>tot[t])
        rows.append(dict(team=t,tot=q2(tot[t]),avg=q2(tot[t]/len(wk)),tot1=q2(tot[t],1),avg1=q2(tot[t]/len(wk),1),wk=[q2(_sc(t,w)) for w in wk],rank=r,seed=seed(t),diff=seed(t)-r,
                         season=q2(sum(_sc(t,w) for w in range(1,G+1))/G)))
    return dict(weeks=wk,rows=rows)
CLOSE_PTS=10
def closegames(lim=CLOSE_PTS):
    """every game settled by lim points or less (margin rounded to 0.01; ties excluded), per team, in week order"""
    out={t:[] for t in TEAMS}
    for t in TEAMS:
        for w in range(1,G+1):
            me,them=_sc(t,w),_fx(WK[t][w-1][3]);m=me-them
            if m!=0 and abs(m)<=lim:out[t].append(dict(w=w,opp=_op(t,w),me=q2(me),them=q2(them),m=q2(abs(m)),win=m>0))
    return out
def sos():
    """remaining regular-season schedule, hardest first: mean points-for per week of the opponents still to play"""
    wk=sorted({f[0] for t in TEAMS for f in FUT[t] if NOW<=f[0]<=REGW})
    if not wk or not G:return dict(weeks=[],rows=[],lg=None)
    pfw={t:sum(_sc(t,w) for w in range(1,G+1))/G for t in TEAMS}
    rows=[]
    for t in TEAMS:
        op={f[0]:FROM_SHORT[f[1]] for f in FUT[t] if NOW<=f[0]<=REGW}
        v=sum(pfw[o] for o in op.values())/len(op)
        rows.append(dict(team=t,opp=[op.get(w) for w in wk],x=v,v=q2(v),v1=q2(v,1)))
    rows.sort(key=lambda r:(-r['x'],seed(r['team'])))
    for r in rows:r['rank']=1+sum(1 for u in rows if u['x']>r['x'])
    return dict(weeks=wk,rows=rows,lg=q2(sum(pfw.values())/len(TEAMS)),lg1=q2(sum(pfw.values())/len(TEAMS),1),pfw={t:q2(v) for t,v in pfw.items()},pfw1={t:q2(v,1) for t,v in pfw.items()},pfw0={t:int(q2(v,0)) for t,v in pfw.items()})
# prime-time sweat: who still had starters to play when the week's first Monday night game kicked off (kick.json: the
# week's NFL kickoffs by team, written by full_update.py from Sleeper's schedule; a team without a game is on bye)
try:KICKS=json.load(open(P+'kick.json'))
except Exception:KICKS={}
try:
    from zoneinfo import ZoneInfo as _ZI;_ET=_ZI('America/New_York')
except Exception:_ET=timezone(timedelta(hours=-5))
def mnf_kick(w):
    ks=sorted({datetime.fromisoformat(v[0]) for v in KICKS.get(str(w),{}).values() if v and v[0]})
    m=[k for k in ks if k.astimezone(_ET).weekday()==0 and k.astimezone(_ET).hour>=17]
    return m[0] if m else None
def _side(t,w,cut):
    d=HI['w'][str(w)][str(RID[t])];pre=_F(0);left=[];K=KICKS.get(str(w),{})
    for x in d[2].split(','):
        if not x:continue
        f=x.split('|');k=K.get(f[1]);k=datetime.fromisoformat(k[0]) if k and k[0] else None
        if k is not None and k>=cut:left.append(dict(pid=f[0],proj=_fx(f[2]),pts=_fx(f[3])))
        else:pre+=_fx(f[3])
    return pre,left
LIVE_X=1   # a live sweat: the side behind needs no more than LIVE_X times its remaining starters' projection
def sweats(kind='live',mult=None):
    """per matchup of every completed week with a Monday night game.
    kind 'any'  : not settled at MNF kickoff = at least one starter on either side still to play (bye players are done)
    kind 'trail': the side behind at MNF kickoff (either side when level) still had a starter to play
    kind 'live' : 'trail' and the gap was no more than LIVE_X times what that side's remaining starters were projected to score
                  (Sleeper projections; a level game with a starter left on either side counts), plus any game the side
                  behind went on to win anyway, so no comeback is ever left out
    kind 'proj' : 'live' without the comeback clause
    kind 'swing': hindsight: the gap was no more than the points all remaining starters went on to score"""
    per={t:dict(n=0,w=0,l=0,cb=0,co=0,mg=[],games=[]) for t in TEAMS};ng=0;tot=0
    for w in range(1,G+1):
        cut=mnf_kick(w)
        if cut is None:continue
        seen=set()
        for a in TEAMS:
            b=_op(a,w)
            if a in seen:continue
            seen|={a,b};tot+=1
            pa,la=_side(a,w,cut);pb,lb=_side(b,w,cut)
            if not (la or lb):continue
            gap=abs(pa-pb);tl=la if pa<pb else lb if pb<pa else la+lb
            if kind!='any':
                if kind=='swing':
                    if gap>sum(q['pts'] for q in la+lb):continue
                elif not tl:continue
                elif kind in('live','proj') and gap>(LIVE_X if mult is None else mult)*sum(q['proj'] for q in tl):
                    if kind=='proj' or not ((pa<pb and _sc(a,w)>_sc(b,w)) or (pb<pa and _sc(b,w)>_sc(a,w))):continue
            ng+=1
            for t,o,x,y,lt,lo in ((a,b,pa,pb,la,lb),(b,a,pb,pa,lb,la)):
                fa,fb=_sc(t,w),_sc(o,w);p=per[t];won=fa>fb;p['n']+=1;p['w' if won else 'l']+=fa!=fb and 1 or 0
                p['mg'].append(x-y)
                cb=x<y and won;co=x>y and fa<fb;p['cb']+=cb;p['co']+=co
                p['games'].append(dict(w=w,opp=o,pre=q2(x),opre=q2(y),m=q2(x-y),left=len(lt),oleft=len(lo),me=q2(fa),them=q2(fb),win=won,cb=cb,co=co))
    for p in per.values():p['avg']=q2(sum(p['mg'])/len(p['mg'])) if p['mg'] else None;p['avg1']=q2(sum(p['mg'])/len(p['mg']),1) if p['mg'] else None;p['mg']=[q2(x) for x in p['mg']]
    return dict(per=per,n=ng,of=tot)
def perfect():
    """record if every team had started its best lineup every week (weekly Max PF against Max PF), from the same
    season.mx that Could have and Tot Eff use"""
    import season as SE
    out={t:dict(o=[0,0,0],a=[0,0,0],opt=_F(0),act=_F(0),flip=[]) for t in TEAMS}
    for w in range(1,G+1):
        for a,b in SE.sched[w]:
            for x,y in ((a,b),(b,a)):
                mx,my,ax,ay=_fx(SE.mx[w][x]),_fx(SE.mx[w][y]),_fx(SE.act[w][x]),_fx(SE.act[w][y]);o=out[x]
                o['o'][0 if mx>my else 1 if mx<my else 2]+=1;o['a'][0 if ax>ay else 1 if ax<ay else 2]+=1
                o['opt']+=mx;o['act']+=ax
                if (mx>my)!=(ax>ay):o['flip'].append(dict(w=w,opp=y,win=mx>my,mx=q2(mx),omx=q2(my)))
    for t,o in out.items():
        o['dw']=o['o'][0]-o['a'][0];o['bench']=q2(o['opt']-o['act']);o['bench1']=q2(o['opt']-o['act'],1);o['eff']=q2(100*o['act']/o['opt'],1) if o['opt'] else None
        o['opt']=q2(o['opt']);o['act']=q2(o['act'])
    return out
def couldhave():
    """per team, from the same weekly Max PF as the Standings card's Could have (season.py CH):
    won  = losses this team's best lineup would have won (its Max PF above the opponent's actual score)
    lost = wins the opponent's best lineup would have taken (the opponent's Max PF above this team's actual score)"""
    import season as SE
    out={t:dict(won=[],lost=[]) for t in TEAMS}
    for w in range(1,G+1):
        for a,b in SE.sched[w]:
            for x,y in ((a,b),(b,a)):
                ax,ay,mx,my=_fx(SE.act[w][x]),_fx(SE.act[w][y]),_fx(SE.mx[w][x]),_fx(SE.mx[w][y])
                if ax>ay:
                    if ax<my:out[x]['lost'].append(dict(w=w,opp=y,me=q2(ax),them=q2(ay),best=q2(my),bench=q2(my-ay),own=q2(mx)))
                elif mx>ay:out[x]['won'].append(dict(w=w,opp=y,me=q2(ax),them=q2(ay),best=q2(mx),bench=q2(mx-ax),obest=q2(my)))
    CH=_g('CH')
    for t in TEAMS:assert [len(out[t]['won']),len(out[t]['lost'])]==list(CH[t]),(t,CH[t])   # one definition: the Standings card's
    return out
if __name__=='__main__':
    o,m=odds()
    for t in sorted(TEAMS,key=lambda t:-o[t]['po']):print(f"{t:24s} po {o[t]['po']:5.1f} bye {o[t]['bye']:5.1f} #1 {o[t]['top']:5.1f} W {o[t]['w']:.2f}")
    M=schedswap();print({SHORT[a]:[M[a][b] for b in TEAMS] for a in TEAMS})
    for a in TEAMS:assert M[a][a]==T[a][0],(a,M[a][a],T[a][0])
    for x in trades()[:4]:print(x)
    rows,per=decisions();print(rows[:3]);print(per)
    tm,hi,lo=projections();print(tm);print([(r['name'],round(r['avg'],1),r['n']) for r in hi]);print([(r['name'],round(r['avg'],1)) for r in lo])
    c,cl,bl=close();print(c);print(cl)
    s=stars();print({SHORT[t]:(s[t]['top1'][0],round(s[t]['s1'],1),round(s[t]['s3'],1)) for t in TEAMS})
    y=youth();print({SHORT[t]:[round(x) for x in y[t]['pct']] for t in TEAMS})
    b=byes();print({SHORT[t]:{w:len(v) for w,v in b[t].items()} for t in TEAMS})
