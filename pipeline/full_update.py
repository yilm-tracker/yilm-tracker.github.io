import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Weekly full refresh. Inputs pulled from Sleeper (see pull_*.json); completes week DONE and prepares week NOW=DONE+1.
import json,re,csv,math
from datetime import date
P=__DTP__+''
import sys as _sys
DONE=int(_sys.argv[1]) if len(_sys.argv)>1 else 7;NOW=DONE+1;TODAY=date.today()
L=lambda f:json.load(open(P+f,encoding='utf-8'))
M7=L('pull_m7.json');A=L('pull_pts.json');X8=L('pull8.json');X8a=L('pull8a.json')
PJ,META,S8,K8=X8['PJ'],X8['META'],X8['S8'],X8['K8']
OLD=L(f'wk{DONE}.json');HI=L('hist.json');X=L('cmp_extra.json');RO={r['rid']:r for r in M7['RO']}
def nm(pid):
    if pid in META and META[pid]:return META[pid][0]
    if pid in HI['m']:return HI['m'][pid][1]
    return pid
def pos(pid):
    if pid in META and META[pid]:return META[pid][1]
    if pid in A:return A[pid][0]
    return HI['m'].get(pid,['?'])[0]
# ---------- 1. completed week -> hist.json, weeks.json
oldp={p[0]:p for X_ in OLD['out'].values() for p in X_['st']+X_['bn']}
topp={};home=set(OLD['home'])
for p in oldp.values():
    if p[6]:topp[p[3]]=p[6]
def opps(tm):
    o=topp.get(tm)
    if not o:return ''
    return o if tm in home else '@'+o
def team_of(pid):
    if pid in oldp:return oldp[pid][3]
    if pid in A:return A[pid][1]
    return META.get(pid,[None,None,''])[2] if META.get(pid) else ''
hw={};wact={};wmx={};pairs={}
def optimal(pool):
    by={}
    for q in pool:by.setdefault(q['pos'],[]).append(q)
    for k in by:by[k].sort(key=lambda q:-q['pts'])
    g=lambda p_,n:by.get(p_,[])[:n]
    fl=sorted(by.get('RB',[])[2:]+by.get('WR',[])[2:]+by.get('TE',[])[1:],key=lambda q:-q['pts'])[:1]
    return g('QB',1)+g('RB',2)+g('WR',2)+g('TE',1)+fl+g('K',1)+g('DEF',1)
for m in M7['M7']:
    rid=m['rid'];st=m['st'];pp=m['pp']
    def ent(pid):
        tm=team_of(pid);pj=oldp[pid][4] if pid in oldp else 0
        return f"{pid}|{tm}|{pj}|{pp.get(pid,0)}|{opps(tm)}"
    bn=[p for p in pp if p not in st]
    hw[str(rid)]=[m['mid'],m['pts'],','.join(ent(p) for p in st),','.join(ent(p) for p in bn)]
    for pid in pp:
        if pid not in HI['m']:HI['m'][pid]=[pos(pid),nm(pid)]
    s=round(sum(pp[p] for p in st),2);assert abs(s-m['pts'])<0.02,(rid,s,m['pts'])
    wact[rid]=m['pts']
    op=optimal([{'pos':pos(p),'pts':v} for p,v in pp.items()]);wmx[rid]=round(sum(q['pts'] for q in op),2)
    assert wmx[rid]>=m['pts']-1e-9
    pairs.setdefault(m['mid'],[]).append(rid)
HI['w'][str(DONE)]=hw
json.dump(HI,open(P+'hist.json','w'),separators=(',',':'))
WJ=L('weeks.json') if __import__('os').path.exists(P+'weeks.json') else {}
WJ[str(DONE)]={'act':wact,'mx':wmx,'sched':[sorted(v) for k,v in sorted(pairs.items())]}
json.dump(WJ,open(P+'weeks.json','w'))
# ---------- 2. data_block.js
import importlib,sys;sys.path.insert(0,P)
import season;importlib.reload(season)
D=season.build(DONE)
s=open(P+'data_block.js',encoding='utf-8').read()
FUT=json.loads(re.search(r'const FUT=(\{.*?\});\n',s).group(1))
SH={1:"Convicts",2:"Homer's",3:"Ram Rod",4:"RIPMFL",5:"Apache",6:"Canton",7:"Nuts",8:"Bill's",9:"Mandingoes",10:"Cheating"}
m8={r[0]:(r[1],r[2]) for r in X8a['m8']}
def projtot(rid):return round(sum(PJ.get(p,[0])[0] for p in m8[rid][1]),2)
NF={}
for t,L_ in FUT.items():
    NF[t]=[x for x in L_ if x[0]>DONE]
    rid=season.RID[t]
    if NF[t] and NF[t][0][0]==NOW:
        opp=[r for r,(mid,_) in m8.items() if mid==m8[rid][0] and r!=rid][0]
        a,b=projtot(rid),projtot(opp);sd=0.215*(a+b);z=(a-b)/sd if sd else 0
        pct=round(100*0.5*(1+math.erf(z/math.sqrt(2))))
        assert NF[t][0][1]==SH[opp],(t,NF[t][0],SH[opp])
        NF[t][0]=[NOW,SH[opp],a,b,pct]
for t in NF:  # make win% pairs sum to 100
    if not NF[t]:continue
    rid=season.RID[t];x=NF[t][0]
    if x[0]==NOW:
        opp=[r for r,(mid,_) in m8.items() if mid==m8[rid][0] and r!=rid][0]
        if rid>opp:x[4]=100-[y for y in NF[season.RN[opp]] if y[0]==NOW][0][4]
def C(k,v):return f'const {k}='+json.dumps(v,ensure_ascii=False,separators=(',',':'))+';\n'
out=(f'const G={DONE};\n// [w,l,top5W,pf,pfRk,pfAvg,pa,paRk,paAvg,oppRk,apW,apL,luck]\n'+C('T',D['T'])+C('H',D['H'])+C('M',D['M'])+
 '// per team: [week, opp, score, oppScore, scoreWeekRank, oppScoreWeekRank]\n'+C('WK',D['WK'])+
 f'// remaining schedule: [week, opp, projScore, oppProj, winPct] (week {NOW}: Sleeper projections for set lineups; later weeks: only week and opponent are used)\n'+C('FUT',NF)+
 '// standings order after the previous week, for movement arrows\n'+C('PH',D['PH'])+C('PM',D['PM'])+
 '// could have [won, lost] from weekly Max PF\n'+C('CH',D['CH'])+'// standings position after each week (from Week 1), per view\n'+C('POS',D['POS']))
open(P+'data_block.js','w',encoding='utf-8').write(out)
json.dump(D['EFF'],open(P+'eff.json','w'),indent=0)
# ---------- 3. position totals (pos.csv) and skill efficiency from hist
rows=list(csv.DictReader(open(P+'pos/pos.csv',encoding='utf-8')));PO=['QB','RB','WR','TE','K','DEF']
agg={};stc={};sk={}
ngs={};_DET=json.load(open(P+'stats_detail.json')) if _dt_os.path.exists(P+'stats_detail.json') else {}  # per-start averages leave out starts with no game
for w in range(1,DONE+1):
    for rid,v in HI['w'][str(w)].items():
        def par(sx):
            o=[]
            for x in sx.split(','):
                if not x:continue
                f=x.split('|');o.append({'pid':f[0],'pos':HI['m'][f[0]][0],'pts':float(f[3]),'opp':f[4] if len(f)>4 else 'x'})
            return o
        st_,bn_=par(v[2]),par(v[3])
        for q in st_:
            a=agg.setdefault(rid,{});a[q['pos']]=a.get(q['pos'],0)+q['pts'];c=stc.setdefault(rid,{});c[q['pos']]=c.get(q['pos'],0)+1
            if not q['opp'] or (q['pts']==0 and not _DET.get(str(w),{}).get(q['pid'],{}).get('gp',1)):  # no game: bye week (or inactive)
                n_=ngs.setdefault(rid,{});n_[q['pos']]=n_.get(q['pos'],0)+1
        F={'RB','WR','TE'};pool=[q for q in st_+bn_ if q['pos'] in F]
        by={}
        for q in pool:by.setdefault(q['pos'],[]).append(q['pts'])
        for k in by:by[k].sort(reverse=True)
        best=sum(by.get('RB',[])[:2])+sum(by.get('WR',[])[:2])+sum(by.get('TE',[])[:1])+max(by.get('RB',[])[2:3]+by.get('WR',[])[2:3]+by.get('TE',[])[1:2]+[0])
        actv=sum(q['pts'] for q in st_ if q['pos'] in F)
        e=sk.setdefault(rid,{'act':0,'opt':0,'hits':0,'wk':[]});e['act']+=actv;e['opt']+=best;e['wk'].append(round(best-actv,2));e['hits']+=abs(best-actv)<0.005
T=D['T']
for r in rows:
    rid=r['roster_id'];t=season.RN[int(rid)]
    for p_ in PO:
        r[p_]=round(agg[rid].get(p_,0),2);r['starts_'+p_]=stc[rid].get(p_,0);r['nogame_'+p_]=ngs.get(rid,{}).get(p_,0);r['avg_'+p_]=round(r[p_]/max(1,r['starts_'+p_]-r['nogame_'+p_]),2)
    r['wins']=T[t][0];r['total']=round(sum(agg[rid].values()),2)
    assert abs(r['total']-T[t][3])<0.05,(t,r['total'],T[t][3])
for key in ['total']+PO+['avg_'+p for p in PO]:
    for r in rows:r[(key if key=='total' else key)+'_rank']=1+sum(float(o[key])>float(r[key])+1e-9 for o in rows)
with open(P+'pos/pos.csv','w',encoding='utf-8',newline='') as f:
    w_=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w_.writeheader();w_.writerows(rows)
SK={'_note':f'Weeks 1-{DONE}, Sleeper matchups. act = points from the 6 RB/WR/TE/FLEX starters; opt = best legal 2 RB + 2 WR + 1 TE + 1 FLEX from the roster; lost = opt - act; hits = weeks with nothing lost; wk = per-week lost'}
for rid,e in sk.items():SK[season.RN[int(rid)]]={'act':round(e['act'],2),'opt':round(e['opt'],2),'hits':e['hits'],'wk':e['wk']}
json.dump(SK,open(P+'skill_opt.json','w'))
# ---------- 4. rosters, ranks, per-game ranks (weeks 1..DONE, league scoring)
tot={p:round(sum(v for v in a[2][:DONE] if v is not None),2) for p,a in A.items()}
gp={p:a[3][:DONE].count('1') for p,a in A.items()};ap={p:a[0] for p,a in A.items()}
K={};PG={}
pgv=lambda q:tot[q]/gp[q] if gp[q] else 0
OLDR=L('rosters.json');keys={}
for k in OLDR:
    n=k.replace('’',"'").replace(' 👑','').strip();n={'RIPMFL':'Team RIPMFL'}.get(n,n);keys[season.RID[n]]=k
R={}
for rid,r in RO.items():
    pl=[]
    for pid in r['pl']:
        p_=pos(pid);pts=tot.get(pid,0.0);g=gp.get(pid,0)
        same=[q for q in tot if ap[q]==p_]
        rk=1+sum(1 for q in same if tot[q]>pts+1e-9) if pid in tot else len(same)+1
        tie=int(sum(1 for q in same if abs(tot[q]-pts)<1e-9)>1) if pid in tot else 0
        ordn=1+sum(1 for q in same if tot[q]>pts+1e-9 or (abs(tot[q]-pts)<1e-9 and q<pid)) if pid in tot else len(same)+1
        if pid in tot:K[pid]=[rk,tie,pts]
        if g:PG[pid]=[1+sum(1 for q in same if gp[q]>=3 and pgv(q)>pgv(pid)+1e-9),g]
        else:PG[pid]=None
        tag='IR' if pid in (r['res'] or []) else 'TX' if pid in (r['taxi'] or []) else ''
        tm=(META.get(pid) or [None,None,None])[2] or (A[pid][1] if pid in A else '')
        pl.append([pid,nm(pid),p_,tm,pts,ordn,g,tag])
    R[keys[rid]]=pl
json.dump(R,open(P+'rosters.json','w'),ensure_ascii=False)
OK=L('ro_ranks.json');K['_bye']=OK['_bye']
json.dump(K,open(P+'ro_ranks.json','w'));json.dump(PG,open(P+'ro_pg.json','w'))
# ---------- 5. compare extras: bench per week, traded players' weekly points, ages
for m in M7['M7']:
    t=season.RN[m['rid']];b=round(sum(v for p,v in m['pp'].items() if p not in m['st']),2)
    if len(X['bench'][t])<DONE:X['bench'][t].append(b)
for pid in X['txw']:
    a=A.get(pid);X['txw'][pid]=[(v if v is not None else 0) for v in a[2][:DONE]] if a else (X['txw'][pid]+[0]*DONE)[:DONE]
for pid,v in META.items():
    if v and v[4] and pid not in X['age']:X['age'][pid]=v[4]
json.dump(X,open(P+'cmp_extra.json','w'),ensure_ascii=False)
# ---------- 6. current week lineups (wk{NOW}.json) + kickoffs
INJ={'Questionable','Doubtful','Out','IR','PUP','Sus'}
home8={h for w_,a_,h in S8 if w_==NOW}
out={}
for rid,(mid,st) in m8.items():
    r=RO[rid]
    def row(pid):
        pj=PJ.get(pid,[0,None]);inj=(META.get(pid) or [None]*4)[3]
        if pid in (r['res'] or []):inj=inj or 'IR'
        tm=(META.get(pid) or [None,None,None])[2] or ''
        return [pid,pos(pid),nm(pid),tm,pj[0],0,pj[1],inj if inj in INJ else None]
    out[str(rid)]={'mid':mid,'pts':0,'st':[row(p) for p in st],'bn':[row(p) for p in r['pl'] if p not in st]}
json.dump({'done':[],'out':out,'home':sorted(home8),'done_note':'final + vs/@ for completed games too'},open(P+f'wk{NOW}.json','w'))
KI=L('kick.json');KI[str(NOW)]=K8;json.dump(KI,open(P+'kick.json','w'))
print('ok',{season.RN[r]:(wact[r],wmx[r]) for r in wact})
