import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Season engine: weekly actual/max scores + schedule -> every standings constant in data_block.js.
# act/mx/sched for weeks 1-6 come from the original max6.py chain; later weeks from weeks.json (written by full_update.py).
import json,io,contextlib,os
P=__DTP__+''
_g={}
with contextlib.redirect_stdout(io.StringIO()):
    _cwd=os.getcwd();os.chdir(P)
    exec(open(P+'max6.py').read().split("teams=list(season); W=range(1,7)")[0],_g)
    os.chdir(_cwd)
act,mx,sched,season=_g['act'],_g['mx'],_g['sched'],_g['season']
B,R,M,C,Pp,N,H_,T_,A,W_=_g['B'],_g['R'],_g['M'],_g['C'],_g['P'],_g['N'],_g['H'],_g['T'],_g['A'],_g['W']
TEAMS=list(season)
RID={"Convicts":1,"Homer's Heroes":2,"Team Ram Rod":3,"Team RIPMFL":4,"Reverse Apache Master":5,"Canton waitlist":6,"Nuts in the Face":7,"Bill's Block Party":8,"Mandingoes":9,"Cheating is Trying":10}
RN={v:k for k,v in RID.items()}
if os.path.exists(P+'weeks.json'):
    for w,d in json.load(open(P+'weeks.json')).items():
        w=int(w);act[w]={RN[int(r)]:v for r,v in d['act'].items()};mx[w]={RN[int(r)]:v for r,v in d['mx'].items()}
        sched[w]=[(RN[a],RN[b]) for a,b in d['sched']]
WKS={B:"Block Party",R:"Ram Rod",H_:"Homer's",Pp:"RIPMFL",M:"Mandingoes",C:"Convicts",A:"Apache",T_:"Cheating",W_:"Canton",N:"Nuts"}
def build(G):
    W=range(1,G+1)
    def table(weeks):
        S={t:dict(w=0,l=0,mw=0,pf=0,pa=0,orr=[],apw=0,apl=0) for t in TEAMS}
        for w in weeks:
            rk={t:i+1 for i,t in enumerate(sorted(act[w],key=lambda t:-act[w][t]))}
            cut=sorted(act[w].values(),reverse=True)[4]
            for t in TEAMS:
                S[t]['mw']+=act[w][t]>=cut
                S[t]['apw']+=sum(act[w][t]>act[w][o] for o in TEAMS if o!=t);S[t]['apl']+=sum(act[w][t]<act[w][o] for o in TEAMS if o!=t)
            for a,b in sched[w]:
                for x,y in((a,b),(b,a)):
                    S[x]['pf']+=act[w][x];S[x]['pa']+=act[w][y];S[x]['orr'].append(rk[y])
                    if act[w][x]>act[w][y]:S[x]['w']+=1
                    else:S[x]['l']+=1
        return S
    def orders(S):
        h=sorted(TEAMS,key=lambda t:(-S[t]['w'],-S[t]['pf']));m=sorted(TEAMS,key=lambda t:(-(S[t]['w']+S[t]['mw']),-S[t]['pf']));return h,m
    Sp=table(range(1,G));S=table(W)
    ph,pm=orders(Sp);h,m=orders(S)
    pfr={t:i+1 for i,t in enumerate(sorted(TEAMS,key=lambda t:-S[t]['pf']))}
    par={t:i+1 for i,t in enumerate(sorted(TEAMS,key=lambda t:-S[t]['pa']))}
    T={}
    for t in TEAMS:
        s=S[t];ap=s['apw']/(s['apw']+s['apl']);luck=round(s['w']-ap*G,2)
        T[t]=[s['w'],s['l'],s['mw'],round(s['pf'],2),pfr[t],round(s['pf']/G,2),round(s['pa'],2),par[t],round(s['pa']/G,2),round(sum(s['orr'])/G,1),s['apw'],s['apl'],luck]
    WK={t:[] for t in TEAMS}
    for w in W:
        rk={t:i+1 for i,t in enumerate(sorted(act[w],key=lambda t:-act[w][t]))}
        for a,b in sched[w]:
            for x,y in((a,b),(b,a)):WK[x].append([w,WKS[y],act[w][x],act[w][y],rk[x],rk[y]])
    CH={}
    for t in TEAMS:
        cw=cl=0
        for w in W:
            for a,b in sched[w]:
                for x,y in((a,b),(b,a)):
                    if x!=t:continue
                    if act[w][x]>act[w][y]:cl+=act[w][x]<mx[w][y]
                    else:cw+=mx[w][x]>act[w][y]
        CH[t]=[cw,cl]
    POS={'H':{t:[] for t in TEAMS},'M':{t:[] for t in TEAMS}}
    for n in W:
        hh,mm=orders(table(range(1,n+1)))
        for t in TEAMS:POS['H'][t].append(hh.index(t)+1);POS['M'][t].append(mm.index(t)+1)
    pf={t:sum(act[w][t] for w in W) for t in TEAMS};mp={t:sum(mx[w][t] for w in W) for t in TEAMS}
    EFF={t:[round(pf[t]/mp[t]*100,2),round((mp[t]-pf[t])/G,2),round(pf[t],2),round(mp[t],2)] for t in TEAMS}
    return dict(G=G,T=T,H=h,M=m,WK=WK,PH=ph,PM=pm,CH=CH,POS=POS,EFF=EFF)
if __name__=='__main__':
    import re
    d=build(6);s=open(P+'bak7/data_block.js').read()
    for k in ['T','H','M','WK','PH','PM','CH','POS']:
        old=json.loads(re.search(r'const '+k+r'=(.*?);\n',s).group(1))
        same=(old==d[k]) if not isinstance(old,dict) else all(old[t]==d[k][t] for t in old)
        print(k,same)
    E=json.load(open(P+'bak7/eff.json'));print('EFF',all(E[t]==d['EFF'][t] for t in E))
