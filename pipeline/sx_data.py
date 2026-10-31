import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Analysis for the Stats tab modules. Pure data; sx_build.py renders it.
import json,re,statistics as stt
from datetime import date,datetime,timezone,timedelta
import numpy as np
P=__DTP__+''
_s=open(P+'data_block.js',encoding='utf-8').read()
def _g(k):return json.loads(re.search(r'const '+k+r'=(.*?);\n',_s).group(1))
T=_g('T');WK=_g('WK');FUT=_g('FUT');PH=_g('PH')
TEAMS=list(T);G=len(WK[TEAMS[0]]);NOW=G+1
X=json.load(open(P+'cmp_extra.json',encoding='utf-8'))
RN={int(k):v for k,v in X['rn'].items()};RID={v:k for k,v in RN.items()}
SHORT={"Team Ram Rod":"Ram Rod","Bill's Block Party":"Block Party","Homer's Heroes":"Homer's","Mandingoes":"Mandingoes","Team RIPMFL":"RIPMFL","Cheating is Trying":"Cheating","Convicts":"Convicts","Nuts in the Face":"Nuts","Reverse Apache Master":"Apache","Canton waitlist":"Canton"}
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
CODE={"Team Ram Rod":"RR","Bill's Block Party":"BP","Homer's Heroes":"HH","Mandingoes":"MA","Team RIPMFL":"RI","Cheating is Trying":"CT","Convicts":"CV","Nuts in the Face":"NF","Reverse Apache Master":"AP","Canton waitlist":"CW"}
FROM_SHORT={**{v:k for k,v in SHORT0.items()},**{k:k for k in SHORT0}};FROM_SHORT["Bill's"]="Bill's Block Party"
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
def optimal(pool):
    by={}
    for q in pool:by.setdefault(q['pos'],[]).append(q)
    for k in by:by[k].sort(key=lambda q:-q['pts'])
    g=lambda pos,n:by.get(pos,[])[:n]
    fl=sorted(by.get('RB',[])[2:]+by.get('WR',[])[2:]+by.get('TE',[])[1:],key=lambda q:-q['pts'])[:1]
    return g('QB',1)+g('RB',2)+g('WR',2)+g('TE',1)+fl+g('K',1)+g('DEF',1)
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
    lg=np.mean(np.concatenate(list(sc.values())))
    pooled=np.mean([np.var(sc[t]) for t in TEAMS])
    mu={t:0.65*sc[t].mean()+0.35*lg for t in TEAMS}
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
    rows=np.arange(n)[:,None];seed_of[rows,order]=np.arange(10)[None,:]
    out={}
    for t in TEAMS:
        i=idx[t];s=seed_of[:,i]
        out[t]=dict(po=float((s<6).mean()*100),bye=float((s<2).mean()*100),top=float((s==0).mean()*100),
                    w=float(W[:,i].mean()),dist=[float((s==k).mean()*100) for k in range(10)])
    return out,dict(n=n,weeks=weeks,lg=float(lg))
# ---------- 2. schedule swap
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
        k=eff_week(x['ts']);a,b=x['rids']
        side={a:dict(pl=[],pk=[],faab=0),b:dict(pl=[],pk=[],faab=0)}
        for pid,to in (x['adds'] or {}).items():
            nm,pos,nfl=X['txp'][pid];wk=X['txw'][pid];pts=sum(wk[k-1:G]) if k<=G else 0.0
            side[to]['pl'].append(dict(name=nm,pos=pos,nfl=nfl,pts=round(pts,2)))
        for y,r,o,new,prev in x['picks']:
            side[new]['pk'].append(f'{y} {RD[r]} ({SHORT[RN[o]]})')
        for f in x['faab']:side[f['receiver']]['faab']+=f['amount']
        out.append(dict(ts=x['ts'],date=datetime.fromtimestamp(x['ts']/1000,timezone.utc).strftime('%b %-d'),eff=k,
            sides=[dict(team=RN[r],**side[r],tot=round(sum(p['pts'] for p in side[r]['pl']),2)) for r in (a,b)]))
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
            if abs(m)<10:c[0 if m>0 else 1]+=1
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
NEED={'QB':1,'RB':2,'WR':3,'TE':1,'K':1,'DEF':1}
def byes():
    out={}
    for t in TEAMS:
        act=[p for p in R[t] if not p[7]]
        core=[p for pos,n in NEED.items() for p in sorted([p for p in act if p[2]==pos],key=lambda p:-p[4])[:n]]
        out[t]={w:[p for p in core if BYE.get(p[3])==w] for w in range(NOW,15)}
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
