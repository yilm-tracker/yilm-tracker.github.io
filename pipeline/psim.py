# Player-level season sim. Every simulated week each team starts its best lineup by Sleeper projection, and every
# starter's score is drawn separately:
#   * mean = the player's league-scored Sleeper projection for that week (0 on a bye or when ruled out); in the
#     pre-game sim for this week, blended 50/50 with FantasyPros (fp_pull.py) where FantasyPros has a line
#   * spread by position, fitted on actual-vs-projected scores in this league's scoring (2025 season + 2026 so far,
#     about 8,000 player-weeks): sd = k * projection^b
#   * right-skewed (lognormal), never negative
#   * players on the same NFL team move together (a shared game factor: QB and his receivers most, kickers least)
#   * the current week is live: finished players keep their points, players mid-game add a draw for the part of the
#     game still to play (game clock), the rest are drawn in full; Questionable / Doubtful starters sometimes score 0
# Then the real remaining schedule, seeds by wins then points for, the playoff bracket, and (dynasty) next draft's order.
# Results are cached in psim.json, keyed on the input files, so every builder reads the same run.
import os,json,hashlib,re
import numpy as np
P=os.path.dirname(os.path.abspath(__file__)).removesuffix('/pos')+'/'
import sys as _s;_s.path.insert(0,P)
import sx_data as D
try:
    import lg as _lg
    PO,BYE_N,DYN=_lg.PO,_lg.BYE_N,_lg.DYN
except Exception:
    PO,BYE_N,DYN=6,2,True
N=len(D.TEAMS);TEAMS=D.TEAMS;IDX={t:i for i,t in enumerate(TEAMS)}
NSIM=20000
# sd = k * mu^b by position (fit described above)
SDK={'QB':(4.58,.18),'RB':(2.31,.45),'WR':(2.90,.37),'TE':(2.23,.49),'K':(2.84,.27),'DEF':(5.18,.12)}
# loading on the NFL team's game factor (pairwise correlation of two teammates = product of their loadings)
LOAD={'QB':.6,'WR':.5,'TE':.45,'RB':.3,'K':.25,'DEF':0.0}
# chance a starter with this injury tag does not play (Sleeper's projection already trims a little for the tag)
MISS={'Questionable':.15,'Doubtful':.7,'Out':1.0,'IR':1.0,'PUP':1.0,'Sus':1.0,'NA':1.0}
INPUTS=['data_block.js','rosters.json','fut_proj.json','pull8.json','ro_ranks.json']
def _wk():return f'wk{D.NOW}.json'
FP_W=0.5   # weight on FantasyPros in the pre-game sim
def _fpf():return f"{P}fp/{os.environ.get('DT_SEASON','2026')}_w{D.NOW}.json"
def _fp():
    f=_fpf()
    try:return {k:float(v) for k,v in json.load(open(f)).get('pts',{}).items()} if os.path.exists(f) else {}
    except Exception:return {}
def _key():
    h=hashlib.sha1(b'psim-v2')
    for f in INPUTS+[_wk()]:
        if os.path.exists(P+f):h.update(open(P+f,'rb').read())
    if os.path.exists(_fpf()):h.update(open(_fpf(),'rb').read())
    return h.hexdigest()
def _sd(pos,mu):
    k,b=SDK.get(pos,(3.0,.35));return k*np.power(np.maximum(mu,0.5),b)
def _draw(mu,sd,pos,nfl,rng,n,Z,teams):
    """n draws for each player: lognormal with mean mu and sd sd, sharing the NFL team's game factor"""
    mu=np.asarray(mu,float);sd=np.asarray(sd,float)
    if not len(mu):return np.zeros((n,0))
    ld=np.array([LOAD.get(p,0.0) for p in pos]);ti=np.array([teams.get(t,-1) for t in nfl])
    z=np.where(ti[None,:]>=0,ld[None,:]*Z[:,np.maximum(ti,0)],0)+np.sqrt(1-np.where(ti>=0,ld,0)**2)[None,:]*rng.standard_normal((n,len(mu)))
    s2=np.log1p((sd/np.maximum(mu,1e-6))**2);s=np.sqrt(s2)
    x=np.maximum(mu,0)[None,:]*np.exp(s[None,:]*z-s2[None,:]/2)
    return np.where(mu[None,:]>0,x,0.0)
def run():
    k=_key()
    if os.path.exists(P+'psim.json'):
        c=json.load(open(P+'psim.json'))
        if c.get('key')==k:return c
    rng=np.random.default_rng(11);n=NSIM
    R=D.R;LW=json.load(open(P+_wk())) if os.path.exists(P+_wk()) else None
    FP=json.load(open(P+'fut_proj.json')) if os.path.exists(P+'fut_proj.json') else {}
    META=json.load(open(P+'pull8.json')).get('META',{}) if os.path.exists(P+'pull8.json') else {}
    inj=lambda pid:(META.get(pid) or [None]*4)[3]
    BYEW=getattr(D,'BYE',{}) or {}
    nflteams=sorted({p[3] for t in TEAMS for p in R[t] if p[3]});NT={t:i for i,t in enumerate(nflteams)}
    # this week's projections (lineup file) as the fallback for weeks the projection pull does not cover
    cur={}
    if LW:
        for o in LW['out'].values():
            for p in o['st']+o['bn']:
                if p:cur[p[0]]=p[4]
    weeks=sorted({f[0] for t in TEAMS for f in D.FUT[t]});REG=max(weeks) if weeks else D.G
    def proj(pid,nfl,w):
        m=FP.get(str(w))
        if m is not None:return float(m.get(pid,0.0))
        if BYEW.get(nfl)==w:return 0.0
        return float(cur.get(pid,0.0))
    def lineup_scores(w,Z):
        """(n, teams) simulated points for week w from each team's best projected lineup"""
        out=np.zeros((n,N))
        for t in TEAMS:
            pool=[{'pid':p[0],'pos':p[2],'nfl':p[3],'pts':proj(p[0],p[3],w)} for p in R[t] if (p[7] if len(p)>7 else '') not in ('IR','TX')]
            st=[q for q in D.optimal(pool) if q and q['pts']>0]
            mu=[q['pts'] for q in st];pos=[q['pos'] for q in st]
            out[:,IDX[t]]=_draw(mu,_sdv(pos,mu),pos,[q['nfl'] for q in st],rng,n,Z,NT).sum(1) if mu else 0
        return out
    def _sdv(pos,mu):return np.array([_sd(p,m) for p,m in zip(pos,mu)]) if mu else np.array([])
    def current_week(Z):
        """the week in progress: finished players fixed, live players their points + the rest of their game, others drawn"""
        out=np.zeros((n,N));done=set(LW.get('done',[]));live=set(LW.get('live',[]));left=LW.get('left',{})
        for t in TEAMS:
            st=[p for p in LW['out'][str(D.RID[t])]['st'] if p]
            fixed=0.0;mu=[];sd=[];pos=[];nfl=[];miss=[]
            for p in st:
                fin=p[8] if len(p)>8 else p[3] in done
                if fin:fixed+=p[5];continue
                if p[3] in live:
                    f=float(left.get(p[3],0.5));fixed+=p[5]
                    if p[4]*f>0:mu.append(p[4]*f);sd.append(float(_sd(p[1],p[4]))*np.sqrt(f));pos.append(p[1]);nfl.append(p[3]);miss.append(0.0)
                    continue
                if p[4]>0:mu.append(p[4]);sd.append(float(_sd(p[1],p[4])));pos.append(p[1]);nfl.append(p[3]);miss.append(MISS.get(inj(p[0]),0.0))
            x=_draw(mu,sd,pos,nfl,rng,n,Z,NT) if mu else np.zeros((n,0))
            if mu:x=x*(rng.random(x.shape)>=np.array(miss)[None,:])
            out[:,IDX[t]]=fixed+x.sum(1)
        return out
    FPW=_fp()   # FantasyPros projections for this week (league scoring), {} without a key
    def _blend(p):
        # second opinion: Sleeper and FantasyPros blended (FP_W on FantasyPros); Sleeper alone where FantasyPros has no line
        f=FPW.get(p[0]);return p[4] if f is None else (1-FP_W)*p[4]+FP_W*f
    def pregame():
        """this week's games as simulated before kickoff: every starter in the set lineup drawn in full from his projection
        (no live points); own random stream, so it does not move as the games are played"""
        r2=np.random.default_rng(12);Z2=r2.standard_normal((n,len(nflteams)));out=np.zeros((n,N))
        for t in TEAMS:
            st=[p for p in LW['out'][str(D.RID[t])]['st'] if p and p[4]>0]
            mu=[_blend(p) for p in st];pos=[p[1] for p in st]
            if not mu:continue
            x=_draw(mu,[float(_sd(q,m)) for q,m in zip(pos,mu)],pos,[p[3] for p in st],r2,n,Z2,NT)
            x=x*(r2.random(x.shape)>=np.array([MISS.get(inj(p[0]),0.0) for p in st])[None,:])
            out[:,IDX[t]]=x.sum(1)
        return out
    PRE=pregame() if LW else None;pre=[]
    W=np.tile(np.array([D.T[t][0] for t in TEAMS],float),(n,1));PF=np.tile(np.array([D.T[t][3] for t in TEAMS],float),(n,1))
    games=[]
    for w in weeks:
        Z=rng.standard_normal((n,len(nflteams)))
        S=current_week(Z) if (LW and w==D.NOW) else lineup_scores(w,Z)
        PF+=S;seen=set()
        for t in TEAMS:
            f=[x for x in D.FUT[t] if x[0]==w]
            if not f or t in seen:continue
            o=D.FROM_SHORT[f[0][1]];seen|={t,o};a,b=IDX[t],IDX[o]
            W[:,a]+=S[:,a]>S[:,b];W[:,b]+=S[:,b]>S[:,a]
            if w==D.NOW:
                games.append([t,o,float(S[:,a].mean()),float(S[:,b].mean()),float((S[:,a]>S[:,b]).mean()*100)])
                if PRE is not None:pre.append([t,o,float(PRE[:,a].mean()),float(PRE[:,b].mean()),float((PRE[:,a]>PRE[:,b]).mean()*100)])
    order=np.argsort(-(W*10000+PF),axis=1)            # order[:,k] = team index seeded k+1
    seed_of=np.empty_like(order);rows=np.arange(n)[:,None];seed_of[rows,order]=np.arange(N)[None,:]
    # playoffs: fixed bracket (Sleeper default). 6 teams, 2 byes: 3v6 and 4v5, then 1 plays the 4/5 winner and 2 the 3/6
    # winner, then the final. 4 teams: 1v4, 2v3, final.
    finish=None
    if weeks and (PO,BYE_N) in ((6,2),(4,0)):   # (once the regular season is over the Playoffs tab has the real bracket)
        PW=[lineup_scores(REG+i,rng.standard_normal((n,len(nflteams)))) for i in (1,2,3)]
        sc=lambda wk,ti:np.take_along_axis(PW[wk],ti[:,None],1)[:,0]
        def game(wk,a,b):
            sa,sb=sc(wk,a),sc(wk,b);return np.where(sa>=sb,a,b),np.where(sa>=sb,b,a)
        s=lambda k:order[:,k]
        if PO==6:
            w36,l36=game(0,s(2),s(5));w45,l45=game(0,s(3),s(4))
            wA,lA=game(1,s(0),w45);wB,lB=game(1,s(1),w36)
        else:
            l36=l45=None;wA,lA=game(1,s(0),s(3));wB,lB=game(1,s(1),s(2))
        ch,ru=game(2,wA,wB)
        # finishing order for draft purposes: champion last, then runner-up, semifinal losers, quarterfinal losers
        # (better seed picks later within a round), then non-playoff teams by reverse standings (worst seed first)
        finish=np.zeros((n,N),int)   # finish[:,team] = pick slot (1 = first pick)
        def put(ti,slot):finish[rows[:,0],ti]=slot
        for k in range(PO,N):put(order[:,k],N-k)
        def pair(a,b,hi):
            sa,sb=np.take_along_axis(seed_of,a[:,None],1)[:,0],np.take_along_axis(seed_of,b[:,None],1)[:,0]
            better=np.where(sa<sb,a,b);worse=np.where(sa<sb,b,a);put(worse,hi-1);put(better,hi)
        base=N-PO
        if PO==6:pair(l36,l45,base+2)
        pair(lA,lB,base+(4 if PO==6 else 2));put(ru,N-1);put(ch,N)
        title=np.zeros(N);final=np.zeros(N)
        for i in range(N):title[i]=(ch==i).mean()*100;final[i]=((ch==i)|(ru==i)).mean()*100
    out={'key':k,'n':n,'weeks':weeks,'now':D.NOW,'teams':{},'games':games,'pre':pre}
    for t in TEAMS:
        i=IDX[t];sd_=seed_of[:,i]
        r={'po':float((sd_<PO).mean()*100),'bye':float((sd_<BYE_N).mean()*100),'top':float((sd_==0).mean()*100),
           'w':float(W[:,i].mean()),'fin':float(sd_.mean()+1),'dist':[float((sd_==k).mean()*100) for k in range(N)]}
        if finish is not None:
            r['title']=float(title[i]);r['final']=float(final[i])
            if DYN:r['pick']=[float((finish[:,i]==k).mean()*100) for k in range(1,N+1)];r['avgpick']=float(finish[:,i].mean())
        out['teams'][t]=r
    json.dump(out,open(P+'psim.json','w'))
    return out
if __name__=='__main__':
    import time;t0=time.time();o=run();print('psim',round(time.time()-t0,1),'s')
    for t,r in sorted(o['teams'].items(),key=lambda x:-x[1]['po']):print(f"{t:24s} W {r['w']:.1f} fin {r['fin']:.1f} 1st {r['top']:.0f} bye {r['bye']:.0f} po {r['po']:.0f} title {r.get('title',0):.0f} pick {r.get('avgpick',0):.1f}")
    for g in o['games']:print(g)
