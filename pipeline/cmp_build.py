import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Compare tab: Team A / Team B dropdowns (details + CSS radios), sub-tabs, one panel per unordered pair (45),
# mirrored by CSS when the picked order is reversed (grid areas swap, colours swap).
import json,re,html,csv,sys,statistics as stt
from datetime import date
P=__DTP__+''
import sys as _s0;_s0.path.insert(0,P);import lg
sys.path.insert(0,P);from nfl_colors import badge_c as badge,NFL_CSS
s=open(P+'data_block.js',encoding='utf-8').read()
g=lambda n:json.loads(re.search(r'const '+n+r'=(.*?);\n',s).group(1))
T,H,WK,FUT=g('T'),g('H'),g('WK'),g('FUT')
def norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip(); return {'RIPMFL':'Team RIPMFL'}.get(n,n)
R={norm(k):v for k,v in json.load(open(P+'rosters.json',encoding='utf-8')).items()}
K=json.load(open(P+'ro_ranks.json'));BYE=K.pop('_bye')
X=json.load(open(P+'cmp_extra.json',encoding='utf-8'))
EF=json.load(open(P+'eff.json'))
SKo=json.load(open(P+'skill_opt.json'));SKo.pop('_note',None)
SK={t:v['act']/v['opt']*100 for t,v in SKo.items()}
POS=list(lg.POS)
PS={norm(r['team']):{p:float(r[p])/max(1,int(r['starts_'+p])-int(r.get('nogame_'+p) or 0)) for p in POS} for r in csv.DictReader(open(P+'pos/pos.csv',encoding='utf-8'))}
SHORT=dict(lg.SHORT)
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
FULL=dict(lg.FULL)
RN={int(k):v for k,v in X['rn'].items()};RID={v:k for k,v in RN.items()}
e=html.escape;G=len(WK[H[0]]);W=G+1;TODAY=date.today()
from datetime import datetime as _dtm
_K=json.load(open(P+'kick.json')).get('1',{})
OPEN=min((int(_dtm.fromisoformat(v[0]).timestamp()*1000) for v in _K.values() if v and v[0]),default=1788800000000)-86400000
seed=lambda t:H.index(t)+1
tone=lg.tone
chip=lambda r:f'<i class="ch {tone(r)}"><span class="ct">{r}</span></i>'
form=lambda t:''.join(f'<i class="fm {"w" if x[2]>x[3] else "l"}"></i>' for x in WK[t][-5:])
SUF={'Jr.','Sr.','II','III','IV','V'}
def last(n):
    a=[w for w in n.split(' ') if w not in SUF]
    if len(a)>=3 and a[-2]=='St.':return 'St. '+a[-1]
    return a[-1] if len(a)>1 else n
def pname(p):return last(p[1])
def age(pid):
    b=X['age'].get(pid)
    if not b:return None
    y,m,d=map(int,b.split('-'));return (TODAY-date(y,m,d)).days/365.25
def row(l,x,y,va=None,vb=None,low=False):
    if va is not None and low: va,vb=-va,-vb
    ca='up' if va is not None and va>vb+1e-9 else '';cb='up' if va is not None and vb>va+1e-9 else ''
    return f'<div class="mcr"><span class="{ca}">{x}</span><em>{l}</em><span class="{cb}">{y}</span></div>'
sec=lambda t,body,sub='':f'<div class="msh">{t}{f"<small>{sub}</small>" if sub else ""}</div><div class="mcmp">{body}</div>'
ppt=lambda p,lab=None:f'<i class="pp sm p-{p.lower()}"><span class="ct">{lab or p}</span></i>'
active=lambda t:[p for p in R[t] if p[7]!='TX']
rk=lambda p:K[p[0]][0] if K.get(p[0]) and p[4]>0 else None
# ---------- Overview
def overview(a,b):
    A,B=T[a],T[b]
    m=[x for x in WK[a] if FULL[x[1]]==b]
    SHN={v:k for k,v in FULL.items() if len(k)<len(v)}
    # meetings: last result (scores, winner bright) and the next game, as two tiles
    nxt=[x for x in FUT[a] if FULL[x[1]]==b]
    def last(x):
        wa=x[2]>x[3];w=a if wa else b
        return (f'<div class="mtg"><span class="mtl">Last meeting · Wk {x[0]}</span><b class="mts"><i class="{"win" if wa else ""}">{x[2]:.1f}</i><em>–</em><i class="{"" if wa else "win"}">{x[3]:.1f}</i></b>'
                f'<span class="mtw"><i class="pav" data-avt="{e(w)}" aria-hidden="true"></i>{e(SHN.get(w,w))} by {abs(x[2]-x[3]):.1f}</span></div>')
    tiles=''.join(last(x) for x in m[-1:]) or '<div class="mtg"><span class="mtl">Last meeting</span><b class="mts mtn">—</b><span class="mtw">Not played yet this season</span></div>'
    if nxt:
        k=nxt[0][0];gap=k-G
        tiles+=(f'<div class="mtg nx"><span class="mtl">Next meeting</span><b class="mts">Week {k}</b><span class="mtw">'
                +('this week' if gap<=1 else f'in {gap} weeks')+'</span></div>')
    else:tiles+='<div class="mtg nx"><span class="mtl">Next meeting</span><b class="mts mtn">—</b><span class="mtw">No more regular-season games</span></div>'
    h2=f'<div class="mtgs">{tiles}</div>'+(''.join(f'<div class="mprev">Also Week {x[0]}: {x[2]:.1f}–{x[3]:.1f}</div>' for x in m[:-1]))
    ew=lambda x,y:(sum(p[2]>q[2] for p,q in zip(WK[x],WK[y])),sum(p[2]<q[2] for p,q in zip(WK[x],WK[y])))
    ea,eb=ew(a,b),ew(b,a)
    body=(row('Record',f'{A[0]}-{A[1]}',f'{B[0]}-{B[1]}',A[0],B[0])+row('Every-week H2H',f'{ea[0]}-{ea[1]}',f'{eb[0]}-{eb[1]}',ea[0],eb[0])+row('PF / wk',f'{A[5]:.1f}',f'{B[5]:.1f}',A[5],B[5])+
      row('PA / wk',f'{A[8]:.1f}',f'{B[8]:.1f}',A[8],B[8],low=True)+row('Max PF / wk',f'{EF[a][3]/G:.1f}',f'{EF[b][3]/G:.1f}',EF[a][3],EF[b][3])+
      row('All-play',f'{A[10]}-{A[11]}',f'{B[10]}-{B[11]}',A[10],B[10])+row('Luck',f'{A[12]:+.2f}',f'{B[12]:+.2f}',A[12],B[12])+
      row('Eff',f'{EF[a][0]:.0f}%',f'{EF[b][0]:.0f}%',round(EF[a][0]),round(EF[b][0]))+row('Skill',f'{SK[a]:.0f}%',f'{SK[b]:.0f}%',round(SK[a]),round(SK[b])))
    return f'<div class="cs cs-ov">{h2}{sec("Season",body)}</div>'
# ---------- Scoring
def swap(a,b):
    w=l=0
    for xa,xb in zip(WK[a],WK[b]):
        opp=xb[3] if FULL[xb[1]]!=a else xb[2]
        if xa[2]>opp:w+=1
        else:l+=1
    return w,l
def chart(a,b):
    Wd,Hh,l,r,t,bt=320,150,26,8,10,20;lo,hi=60,200
    x=lambda k:l+(Wd-l-r)*(k-1)/(G-1);y=lambda v:t+(Hh-t-bt)*(1-(v-lo)/(hi-lo))
    o=f'<svg class="cch" viewBox="0 0 {Wd} {Hh}" role="img" aria-label="Weekly scores">'
    for gv in (100,150,200):o+=f'<line x1="{l}" x2="{Wd-r}" y1="{y(gv):.1f}" y2="{y(gv):.1f}" stroke="#262c38"/><text x="{l-5}" y="{y(gv)+3.5:.1f}" text-anchor="end" font-size="10" fill="#626b7c">{gv}</text>'
    for k in range(1,G+1):o+=f'<text x="{x(k):.1f}" y="{Hh-5}" text-anchor="middle" font-size="10" fill="#9aa3b5">{k}</text>'
    for t_,c in ((a,'var(--ca)'),(b,'var(--cb)')):
        pts=' '.join(f'{x(q[0]):.1f},{y(q[2]):.1f}' for q in WK[t_])
        o+=f'<polyline points="{pts}" fill="none" style="stroke:{c}" stroke-width="2.2" stroke-linejoin="round"/>'
        o+=''.join(f'<circle cx="{x(q[0]):.1f}" cy="{y(q[2]):.1f}" r="3.2" style="fill:{c}" stroke="#0f1218" stroke-width="1.2"/>' for q in WK[t_])
    return o+'</svg>'
def scoring(a,b):
    sa=[x[2] for x in WK[a]];sb=[x[2] for x in WK[b]]
    swa,swb=swap(a,b),swap(b,a)
    hw=lambda u,v:sum(1 for x,y in zip(u,v) if x>y)
    body=(row('Average',f'{stt.mean(sa):.1f}',f'{stt.mean(sb):.1f}',stt.mean(sa),stt.mean(sb))+
      row('Median',f'{stt.median(sa):.1f}',f'{stt.median(sb):.1f}',stt.median(sa),stt.median(sb))+
      row('High',f'{max(sa):.1f}',f'{max(sb):.1f}',max(sa),max(sb))+row('Low',f'{min(sa):.1f}',f'{min(sb):.1f}',min(sa),min(sb))+
      row('Swing (SD)',f'{stt.pstdev(sa):.1f}',f'{stt.pstdev(sb):.1f}',stt.pstdev(sa),stt.pstdev(sb),low=True)+
      row('Weeks 130+',str(sum(v>=130 for v in sa)),str(sum(v>=130 for v in sb)),sum(v>=130 for v in sa),sum(v>=130 for v in sb))+
      row('Outscored other',str(hw(sa,sb)),str(hw(sb,sa)),hw(sa,sb),hw(sb,sa)))
    sw=(row('Actual record',f'{T[a][0]}-{T[a][1]}',f'{T[b][0]}-{T[b][1]}',T[a][0],T[b][0])+
        row('With other’s schedule',f'{swa[0]}-{swa[1]}',f'{swb[0]}-{swb[1]}',swa[0],swb[0]))
    leg=f'<div class="cleg"><span><i class="la"></i>{e(a)}</span><span><i class="lb"></i>{e(b)}</span></div>'
    return f'<div class="cs cs-sc"><div class="msh">Weekly scores</div>{chart(a,b)}{leg}{sec("Consistency",body,f"same weeks, Wk 1–{G}")}{sec("Schedule swap",sw,"each team’s scores against the other’s opponents")}</div>'
# ---------- Positions
TOPN={'QB':12,'RB':24,'WR':24,'TE':12,'K':12,'DEF':12}
def positions(a,b):
    ps=''.join(row(ppt(p),f'{PS[a][p]:.1f}',f'{PS[b][p]:.1f}',PS[a][p],PS[b][p]) for p in POS)
    def best(t,p):
        r=[q for q in active(t) if q[2]==p and rk(q)];return min(r,key=rk) if r else None
    bs=''
    for p in POS:
        pa,pb=best(a,p),best(b,p)
        bs+=f'<div class="cr cbp">{cn(pa,"a")}<em>{p}</em>{cn(pb,"b")}</div>'
    cnt=lambda t,p:sum(1 for q in active(t) if q[2]==p and rk(q) and rk(q)<=TOPN[p])
    st=''.join(row(ppt(p,f'{p} ≤{TOPN[p]}'),str(cnt(a,p)),str(cnt(b,p)),cnt(a,p),cnt(b,p)) for p in POS)
    ta,tb=sum(cnt(a,p) for p in POS),sum(cnt(b,p) for p in POS)
    st+=row('Total',str(ta),str(tb),ta,tb)
    return f'<div class="cs cs-po">{sec("Points per start",ps)}{f'<div class="msh">Best player<small>by position rank</small></div><div class="cbpw">{bs}</div>'}{sec("Startable players",st,"top 12 QB, TE, K, DEF · top 24 RB, WR")}</div>'
# ---------- Players (mirrored, one line each)
PG=json.load(open(P+'ro_pg.json'))
def cn(p,side,mode='p'):
    if p is None:return f'<span class="cn {side}"></span>'
    r=rk(p) if mode=='p' else (PG[p[0]][0] if PG.get(p[0]) else None);lab=f'{p[2]}{r}' if r else p[2]
    ir='<i class="cir"></i>' if p[7]=='IR' else ''
    ag=age(p[0])
    agh=f'<em class="pag {"ay" if ag<27 else "ap" if ag<31 else "ao"}">{ag:.1f}</em>' if ag else ''
    sm2=f'<span class="gp">{p[6]} GP</span>' if mode=='g' else agh
    sq=f'<i class="pq p-{p[2].lower()}{" l3" if (r and r>=100) or (p[2]=="DEF" and r and r>=10) else ""}"><span class="pqi"><span>{p[2]}</span>{f"<b>{r}</b>" if r else ""}</span></i>'
    return f'<span class="cn {side}">{sq}<span class="cnm"><b>{ir}<span>{e(pname(p))}</span>{agh}</b><small>{badge(p[3])}<span class="gp">{p[6]} GP</span></small></span></span>'
def cell(p,side,mode):
    if p is None:return f'<span class="cn {side}"></span><span class="cv {side}"></span>'
    v=p[4] if mode=='p' else (p[4]/p[6] if p[6] else 0)
    return cn(p,side,mode)+f'<span class="cv {side}">{v:.1f}</span>'
def players(a,b,mode):
    val=(lambda p:p[4]) if mode=='p' else (lambda p:p[4]/p[6] if p[6] else 0)
    o=[]
    for pos in POS:
        la=sorted([p for p in active(a) if p[2]==pos],key=lambda p:-val(p));lb=sorted([p for p in active(b) if p[2]==pos],key=lambda p:-val(p))
        if not la and not lb:continue
        if mode=='p':ta,tb=sum(map(val,la)),sum(map(val,lb))
        else:ta,tb=sum(p[4] for p in la)/max(1,sum(p[6] for p in la)),sum(p[4] for p in lb)/max(1,sum(p[6] for p in lb))
        o.append(f'<div class="cgh p-{pos.lower()}"><span class="{"up" if ta>tb+1e-9 else ""}">{ta:.1f}</span><em>{pos}</em><span class="{"up" if tb>ta+1e-9 else ""}">{tb:.1f}</span></div>')
        for k in range(max(len(la),len(lb))):
            pa=la[k] if k<len(la) else None;pb=lb[k] if k<len(lb) else None;w=''
            if pa and pb:va,vb=val(pa),val(pb);w=' wa' if va>vb+1e-9 else ' wb' if vb>va+1e-9 else ''
            o.append(f'<div class="cr{w}">{cell(pa,"a",mode)}{cell(pb,"b",mode)}</div>')
    return ''.join(o)
def playersec(a,b):
    return f'<div class="cs cs-pl"><div class="cpg pseg" role="group" aria-label="Player points"><label for="cs-p">Pts</label><label for="cs-g">Pts/g</label></div><div class="cpl cpl-p">{players(a,b,"p")}</div><div class="cpl cpl-g">{players(a,b,"g")}</div></div>'
# ---------- Depth
def depth(a,b):
    ba,bb=stt.mean(X['bench'][a]),stt.mean(X['bench'][b])
    tot=lambda t:sum(p[4] for p in R[t])
    n10=lambda t:sum(1 for p in active(t) if p[6] and p[4]/p[6]>=10)
    cnt=lambda t,k:sum(1 for p in R[t] if p[7]==k)
    body=(row('Bench pts / wk',f'{ba:.1f}',f'{bb:.1f}',ba,bb)+row('Bench share',f'{ba/(ba+T[a][5])*100:.0f}%',f'{bb/(bb+T[b][5])*100:.0f}%',ba/(ba+T[a][5]),bb/(bb+T[b][5]))+
      row('Roster pts',f'{tot(a):.0f}',f'{tot(b):.0f}',tot(a),tot(b))+row('10+ pts/g players',str(n10(a)),str(n10(b)),n10(a),n10(b))+
      row('Active players',str(cnt(a,'')),str(cnt(b,'')))+row('On IR',str(cnt(a,'IR')),str(cnt(b,'IR')))+(row('Taxi',str(cnt(a,'TX')),str(cnt(b,'TX'))) if lg.DYN else ''))
    return f'<div class="cs cs-dp">{sec("Depth",body,f"bench = rostered players not started, Wk 1–{G}")}</div>'
# ---------- Schedule
def schedule(a,b):
    PAST=not FUT[a];fa,fb=(WK[a],WK[b]) if PAST else (FUT[a],FUT[b])
    av=lambda f,fn:stt.mean(fn(FULL[x[1]]) for x in f)
    t3=lambda f:sum(seed(FULL[x[1]])<=3 for x in f)
    by=lambda t,w:sum(1 for p in R[t] if not p[7] and BYE.get(p[3])==w)
    ab=lambda t,f:sum(by(t,x[0]) for x in f)
    s1=(row('Avg opp seed',f'{av(fa,seed):.1f}',f'{av(fb,seed):.1f}',av(fa,seed),av(fb,seed))+
        row('Avg opp PF / wk',f'{av(fa,lambda t:T[t][5]):.1f}',f'{av(fb,lambda t:T[t][5]):.1f}',av(fa,lambda t:T[t][5]),av(fb,lambda t:T[t][5]),low=True)+
        row('Games vs top 3',str(t3(fa)),str(t3(fb)),t3(fa),t3(fb),low=True)+
        row('Bye absences',str(ab(a,fa)),str(ab(b,fb)),ab(a,fa),ab(b,fb),low=True))
    rows=''
    for xa,xb in zip(fa,fb):
        oa,ob=FULL[xa[1]],FULL[xb[1]];na,nb=by(a,xa[0]),by(b,xb[0])
        ia=f'<i class="mby">{na}</i>' if na else '';ib=f'<i class="mby">{nb}</i>' if nb else ''
        rows+=(f'<div class="mcr csr"><span>{chip(seed(oa))}<b>{e(oa)}</b>{ia}</span><em>Wk {xa[0]}</em>'
               f'<span>{chip(seed(ob))}<b>{e(ob)}</b>{ib}</span></div>')
    return f'<div class="cs cs-sh">{sec("Full season" if PAST else "Rest of season",s1,"final seeds · white = easier run" if PAST else "white = easier run")}{sec("Week by week",rows,"opponent seed · players on bye in blue")}</div>'
# ---------- Dynasty
_Y=int(_dt_os.environ.get('DT_SEASON','2026'));SEAS=[str(_Y+1),str(_Y+2),str(_Y+3)]
OWN={}
for sn in SEAS:
    for rd in range(1,X['rounds']+1):
        for r in RN:OWN[(sn,rd,r)]=r
for sn,rd,r,o in X['tp']:
    if sn in SEAS:OWN[(sn,rd,r)]=o
def picks(t,sn):
    rid=RID[t];return sorted([(rd,r) for (s_,rd,r),o in OWN.items() if s_==sn and o==rid])
def dynasty(a,b):
    def avg(t,pos=None):
        v=[age(p[0]) for p in R[t] if p[2] not in('DEF','K') and (pos is None or p[2]==pos) and age(p[0])]
        return stt.mean(v) if v else None
    def avgw(t):
        v=[(age(p[0]),p[4]) for p in active(t) if p[2] not in('DEF','K') and age(p[0])]
        return sum(x*w for x,w in v)/max(1e-9,sum(w for _,w in v))
    ag=row('Roster',f'{avg(a):.1f}',f'{avg(b):.1f}',avg(a),avg(b),low=True)+row('Points-weighted',f'{avgw(a):.1f}',f'{avgw(b):.1f}',avgw(a),avgw(b),low=True)
    for p in ['QB','RB','WR','TE']:
        x,y=avg(a,p),avg(b,p)
        ag+=row(ppt(p),f'{x:.1f}' if x else '–',f'{y:.1f}' if y else '–',*( (x,y,True) if x and y else (None,None)))
    def pk(t,sn):
        rid=RID[t]
        return ''.join(f'<i class="pk{"" if r==rid else " via"}" title="{"own" if r==rid else "via "+e(RN[r])}"><span class="ct">{rd}</span></i>' for rd,r in picks(t,sn)) or '<span class="none">–</span>'
    pr=''.join(f'<div class="mcr cpk2"><span>{pk(a,sn)}</span><em>{sn}</em><span>{pk(b,sn)}</span></div>' for sn in SEAS)
    n1=lambda t:sum(1 for sn in SEAS for rd,_ in picks(t,sn) if rd==1);nt=lambda t:sum(len(picks(t,sn)) for sn in SEAS)
    pr+=row('1st-rounders',str(n1(a)),str(n1(b)),n1(a),n1(b))+row('Total picks',str(nt(a)),str(nt(b)),nt(a),nt(b))
    return f'<div class="cs cs-dy">{sec("Average age",ag,"QB, RB, WR, TE · younger in white")}{sec("Rookie picks",pr,"round number · blue outline = acquired")}</div>'
# ---------- Trades
def trades(a,b):
    ra,rb=RID[a],RID[b]
    cnt=lambda r:sum(1 for t in X['tx'] if r in t['rids'])
    body=row('Trades this season',str(cnt(ra)),str(cnt(rb)))
    items=''
    for t in sorted(X['tx'],key=lambda t:t['ts']):
        if set(t['rids'])!={ra,rb}:continue
        def got(r):
            out=[]
            for pid,to in (t['adds'] or {}).items():
                if to==r:
                    nm,pos,tm=X['txp'][pid];since=sum(X['txw'][pid][w-1] for w in range(max(1,t['w']),G+1))
                    out.append(f'<div class="ti">{ppt(pos)}<span>{e(nm)}</span><b>{since:.1f}</b></div>')
            for sn,rd,orig,to,frm in t['picks']:
                if to==r:out.append(f'<div class="ti"><i class="pk"><span class="ct">{rd}</span></i><span>{sn} R{rd}{"" if orig==to else " · "+e(RN[orig])}</span></div>')
            for f in t['faab']:
                if f['receiver']==r:out.append(f'<div class="ti"><i class="pk faab"><span class="ct">$</span></i><span>${f["amount"]} FAAB</span></div>')
            return ''.join(out) or '<div class="ti none">–</div>'
        when='Pre-season' if t['ts']<OPEN else f'Week {t["w"]}'
        items+=f'<div class="ctr"><div class="ctw">{when}</div><div class="mcr ctg"><div>{got(ra)}</div><em>gets</em><div>{got(rb)}</div></div></div>'
    if not items:items='<div class="mprev">No trades between these two teams this season</div>'
    return f'<div class="cs cs-tr">{sec("Activity",body)}<div class="msh">Trades with each other<small>points scored since the trade</small></div>{items}</div>'
SUBS=[('ov','Overview'),('sc','Scoring'),('po','Positions'),('pl','Players'),('dp','Depth'),('sh','Schedule'),('dy','Dynasty'),('tr','Trades')]
if not lg.DYN:SUBS=[x for x in SUBS if x[0]!='dy']  # redraft league: no future picks
def panel(i,j):
    a,b=H[i],H[j]
    side=lambda x,cl:f'<div class="mus {cl}">{chip(seed(x))}<b>{e(x)}</b><span class="mrec">{T[x][0]}-{T[x][1]}</span><span class="mform">{form(x)}</span></div>'
    return (f'<div class="cpn cp-{i}-{j}"><div class="mcard chead"><div class="mvs">{side(a,"msl")}<span class="mv2">vs</span>{side(b,"msr")}</div></div>'
            +overview(a,b)+scoring(a,b)+positions(a,b)+playersec(a,b)+depth(a,b)+schedule(a,b)+(dynasty(a,b) if lg.DYN else '')+trades(a,b)+'</div>')
radios=(''.join(f'<input type="radio" name="ca" id="ca-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(lg.N))+
        ''.join(f'<input type="radio" name="cb" id="cb-{i}" class="lr"{" checked" if i==1 else ""}>' for i in range(lg.N))+
        ''.join(f'<input type="radio" name="csub" id="ct-{k}" class="lr"{" checked" if k=="ov" else ""}>' for k,_ in SUBS)+
        '<input type="radio" name="cs" id="cs-p" class="lr" checked><input type="radio" name="cs" id="cs-g" class="lr">')
_SVS={}  # full team names everywhere
def dd(k,lab):
    return (f'<details class="dd dd-{k}"><summary><span class="ddk">{lab}</span>'+''.join(f'<span class="sv sv-{i}"><span class="svf">{e(t)}</span><span class="svs">{e(_SVS.get(t,t))}</span></span>' for i,t in enumerate(H))+
            '<svg viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></summary>'
            f'<div class="ddm">'+''.join(f'<label for="c{k}-{i}"><i>{i+1}</i>{e(t)}</label>' for i,t in enumerate(H))+'</div></details>')
nav='<div class="lbc csub">'+''.join(f'<label for="ct-{k}">{n}</label>' for k,n in SUBS)+'</div>'
html_=('<section class="cmx" aria-labelledby="cmh">'+radios+
     '<div class="posh"><b id="cmh">Compare</b></div>'+
     '<div class="cpk">'+dd('a','A')+dd('b','B')+'</div>'+nav+
     '<div class="csame">Pick two different teams.</div>'+
     ''.join(panel(i,j) for i in range(lg.N) for j in range(lg.N) if i<j)+'</section>')
css=''.join(f'#ca-{i}:checked~.cpk .dd-a .sv-{i},#cb-{i}:checked~.cpk .dd-b .sv-{i}{{display:inline}}#ca-{i}:checked~.cpk .dd-a label[for="ca-{i}"],#cb-{i}:checked~.cpk .dd-b label[for="cb-{i}"]{{background:var(--chalk);color:var(--ink)}}' for i in range(lg.N))
css+=','.join(f'#ca-{i}:checked~#cb-{j}:checked~.cp-{min(i,j)}-{max(i,j)}' for i in range(lg.N) for j in range(lg.N) if i!=j)+'{display:block}'
css+=''.join(f'#ca-{i}:checked~#cb-{i}:checked~.csame{{display:block}}' for i in range(lg.N))
css+=''.join(f'#ct-{k}:checked~.csub label[for="ct-{k}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#ct-{k}:checked~.cpn .cs-{k}{{display:block}}' for k,_ in SUBS)
FL=':is('+','.join(f'#ca-{j}:checked~#cb-{i}:checked~.cp-{i}-{j}' for i in range(lg.N) for j in range(lg.N) if i<j)+')'
flip={'':'--ca:#f59a52;--cb:#7fa6ff','.mcr,.cgh':'grid-template-areas:"b m a"','.mcr>:first-child,.cgh>:first-child':'text-align:right;justify-content:flex-end','.mcr>:last-child,.cgh>:last-child':'text-align:left;justify-content:flex-start',
 '.mvs':'grid-template-areas:"b m a"','.mus.msl':'align-items:flex-end;text-align:right','.mus.msr':'align-items:flex-start;text-align:left',
 '.mus.msl .ch':'align-self:flex-end','.mus.msr .ch':'align-self:flex-start','.cleg':'flex-direction:row-reverse',
 '.cr':'grid-template-areas:"nb vb va na"','.cv.a':'text-align:left;padding:0 0 0 4px','.cv.b':'text-align:right;padding:0 4px 0 0','.cn.a':'flex-direction:row-reverse','.cn.b':'flex-direction:row','.cbp':'grid-template-areas:"nb m na"','.cn.a .cnm':'align-items:flex-end;text-align:right','.cn.a small':'flex-direction:row-reverse','.cn.a .cnm b':'flex-direction:row-reverse','.cn.b .cnm b':'flex-direction:row','.cn.b .cnm':'align-items:flex-start;text-align:left','.cn.b small':'flex-direction:row',
 '.ctg>:first-child':'align-items:flex-end','.ctg>:first-child .ti':'flex-direction:row-reverse','.ctg>:last-child':'align-items:flex-start','.ctg>:last-child .ti':'flex-direction:row',
 '.csr>:first-child':'flex-direction:row-reverse;justify-content:flex-start','.csr>:last-child':'flex-direction:row;justify-content:flex-start',
 '.cpk2>:first-child':'justify-content:flex-end','.cpk2>:last-child':'justify-content:flex-start'}
css+=''.join(f'{FL}{" :is("+k+")" if k else ""}{{{v}}}' for k,v in flip.items())
css+=NFL_CSS
open(P+'cmp_section.html','w',encoding='utf-8').write(html_);open(P+'cmp_css.css','w',encoding='utf-8').write(css)
if __name__=='__main__':
    print(len(html_)//1024,'KB css',len(css)//1024,'KB')
    a,b=H[1],H[2];print(swap(a,b),swap(b,a),[(sn,picks(a,sn)) for sn in SEAS])
    for t in H:print(SHORT[t],round(stt.mean(X['bench'][t]),2),sum(len(picks(t,sn)) for sn in SEAS),[len(picks(t,sn)) for sn in SEAS])
