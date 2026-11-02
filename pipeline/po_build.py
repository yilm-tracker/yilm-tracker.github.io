import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Playoffs tab: bracket "if the season ended today" (top 6, seeds 1-2 bye, fixed bracket: 1 v 4/5 winner, 2 v 3/6 winner),
# clickable games, and a build-your-own playoff matchup (team A, team B, week 15/16/17) in the same layout as Matchups.
# Projections: week-specific Sleeper projections from po_proj.json when present, otherwise season points per game.
import json,re,html,os,math,sys
from datetime import date
P=__DTP__+''
import sys as _s0;_s0.path.insert(0,P);import lg
sys.path.insert(0,P)
from nfl_colors import badge_c as badge
e=html.escape
s=open(P+'data_block.js',encoding='utf-8').read()
g=lambda n:json.loads(re.search(r'const '+n+r'=(.*?);\n',s).group(1))
T,H,WK=g('T'),g('H'),g('WK');G=len(WK[H[0]])
def norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip();return {'RIPMFL':'Team RIPMFL'}.get(n,n)
R={norm(k):v for k,v in json.load(open(P+'rosters.json',encoding='utf-8')).items()}
K=json.load(open(P+'ro_ranks.json'));K.pop('_bye',None)
AGE=json.load(open(P+'cmp_extra.json',encoding='utf-8'))['age']
A=json.load(open(P+'pull_pts.json'))
INJM={}
if os.path.exists(P+'pull8.json'):
    for pid,m in json.load(open(P+'pull8.json'))['META'].items():
        if m and m[3]:INJM[pid]=m[3]
PROJ=json.load(open(P+'po_proj.json')) if os.path.exists(P+'po_proj.json') else None
SHORT=dict(lg.SHORT)
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
FULL=dict(lg.FULL)
WEEKS=[15,16,17];RND={15:'Wild Card',16:'Semi Finals',17:'Championship'}
tone=lg.tone
chip=lambda r:f'<i class="ch {tone(r)}"><span class="ct">#{r}</span></i>'
seed=lambda t:H.index(t)+1
def age(pid):
    b=AGE.get(pid)
    if not b:return None
    y,m,d=map(int,b.split('-'));return (date.today()-date(y,m,d)).days/365.25
def ppg(pid):
    a=A.get(pid)
    if not a:return 0.0,0
    gp=a[3][:G].count('1');tot=sum(v for v in a[2][:G] if v is not None)
    return (round(tot/gp,2) if gp else 0.0),gp
def proj(pid,w):
    if PROJ and str(w) in PROJ and pid in PROJ[str(w)]:return PROJ[str(w)][pid][0],PROJ[str(w)][pid][1]
    return ppg(pid)[0],None
def pool(t,w):
    out=[]
    for p in R[t]:
        if p[7] in('IR','TX'):continue
        v,opp=proj(p[0],w);out.append(dict(pid=p[0],name=p[1],pos=p[2],nfl=p[3],pj=v,opp=opp,gp=ppg(p[0])[1],inj=INJM.get(p[0])))
    return out
SLOTS=[lg.SLAB.get(x,x) for x in lg.SLOTS]
def best(t,w):return lg.optimal(pool(t,w),pts=lambda q:q['pj'])
BEST={(t,w):best(t,w) for t in H for w in WEEKS}
PT={(t,w):round(sum(q['pj'] for q in BEST[(t,w)] if q),1) for t in H for w in WEEKS}
# finished playoff games (po_actual.json, written for a past season): real scores replace projections
ACT=json.load(open(P+'po_actual.json')) if os.path.exists(P+'po_actual.json') else None
_RN=dict(lg.RN)
AW={(_RN[int(r)],int(w)):v[1] for w,d in (ACT or {}).get('w',{}).items() for r,v in d.items()}
PT.update(AW)
FINAL=any(k[1]==17 for k in AW)  # championship played: the bracket is the result, no projections
def winp(a,b,w):
    if (a,w) in AW and (b,w) in AW:return 100 if AW[(a,w)]>AW[(b,w)] else 0
    x,y=PT[(a,w)],PT[(b,w)];sd=0.215*(x+y)
    return round(100*0.5*(1+math.erf((x-y)/sd/math.sqrt(2)))) if sd else 50
INJ={'Questionable':'Q','Doubtful':'D','Out':'O','IR':'IR'}
def cell(q,side):
    if q is None:return f'<span class="cn {side}"></span><span class="cv {side}"></span>'
    r=K[q['pid']][0] if K.get(q['pid']) and K[q['pid']][2]>0 else None
    big=r and (r>=100 or (q['pos']=='DEF' and r>=10))
    sq=f'<i class="pq p-{q["pos"].lower()}{" l3" if big else ""}"><span class="pqi"><span>{q["pos"]}</span>{f"<b>{r}</b>" if r else ""}</span></i>'
    nm=q['name'].split(' ')[-1]
    if nm in('Jr.','Sr.','II','III','IV'):nm=q['name'].split(' ')[-2]
    if q['pos']!='DEF' and len(q['name'].split(' '))>2 and q['name'].split(' ')[-2]=='St.':nm='St. '+nm
    ij=f'<i class="inj i-{INJ[q["inj"]]}">{INJ[q["inj"]]}</i>' if q['inj'] in INJ else ''
    sub=(f'vs {q["opp"]}' if q['opp'] else f'{q["gp"]} GP')
    return (f'<span class="cn {side}">{sq}<span class="cnm"><b><span>{e(nm)}</span>{ij}</b>'
            f'<small>{badge(q["nfl"])}<span class="gp">{sub}</span></small></span></span><span class="cv {side}">{q["pj"]:.1f}</span>')
import mu_build as MB
MB.HATILE=False  # home / road shown by the vs / @ tile in each game line
_W8=json.load(open(P+f'wk{G+1}.json'))
RIDN=dict(lg.RID)
HOMEW=json.load(open(P+'po_home.json')) if os.path.exists(P+'po_home.json') else {}
def mp(q,w):
    """player dict -> Matchups row format [pid,pos,name,nfl,proj,act,opp,inj,done,ha,week]"""
    if q is None:return None
    if q['opp']:ha='vs' if q['nfl'] in HOMEW.get(str(w),[]) else '@';opp=q['opp']
    else:ha='';opp='TBD'
    return [q['pid'],q['pos'],q['name'],q['nfl'],q['pj'],0,opp,q['inj'],False,ha,w]
def setlineup(t,w):
    """the team's lineup as currently set in Sleeper, re-projected for week w"""
    pl={q['pid']:q for q in pool(t,w)}
    allp={p[0]:p for p in R[t]}
    out=[]
    for x in _W8['out'][str(RIDN[t])]['st']:
        pid=x[0]
        if pid in pl:out.append(pl[pid])
        elif pid in allp:
            p=allp[pid];v,opp=proj(pid,w);out.append(dict(pid=pid,name=p[1],pos=p[2],nfl=p[3],pj=v,opp=opp,gp=ppg(pid)[1],inj=INJM.get(pid)))
        else:out.append(None)
    return out
def lineup(a,b,w,k='p'):
    sa=[mp(q,w) for q in setlineup(a,w)];sb=[mp(q,w) for q in setlineup(b,w)]
    pa=[mp(q,w) for q in pool(a,w)];pb=[mp(q,w) for q in pool(b,w)]
    ta=sum(p[4] for p in sa if p);tb=sum(p[4] for p in sb if p)
    src='Sleeper projections' if PROJ else f'projection = points per game, Weeks 1–{G} until Sleeper projections are pulled'
    hdr=f'<div class="msh lsh">Lineups</div>{MB.CTL([(MB.VSW,'Order','Lineup',MB.LSW)])}<div class="lnote">set lineup = starters as set in Sleeper now · {src}</div>'
    o=[MB.ptsrow(sa,sb)]
    o+=['<div class="lpv">']+[MB.lrow(x,y,'') for x,y in zip(sa,sb)]+['</div>',MB.sview([x for x in sa if x],[y for y in sb if y])]
    sida={p[0] for p in sa if p};sidb={p[0] for p in sb if p}
    ba=sorted([p for p in pa if p[0] not in sida and p[4]>0],key=lambda p:-p[4]);bb=sorted([p for p in pb if p[0] not in sidb and p[4]>0],key=lambda p:-p[4])
    if ba or bb:
        o.append('<div class="msh lbh">Bench<small>active players, projected</small></div>')
        o+=[MB.lrow(ba[k] if k<len(ba) else None,bb[k] if k<len(bb) else None,'') for k in range(max(len(ba),len(bb)))]
    h=('<div class="lus">'+hdr+'<div class="lus-a">'+''.join(o)+'</div>'+MB.optblock([p for p in sa if p],[p for p in sb if p],pa,pb,ta,tb,True,'<div class="msh lbh">Bench<small>active players, projected</small></div>',lambda p:p[4]>0)+'</div>')
    return h.replace('for="lo-a"',f'for="{k}lo-a"').replace('for="lo-o"',f'for="{k}lo-o"').replace('for="lv-p"',f'for="{k}lv-p"').replace('for="lv-s"',f'for="{k}lv-s"')
def form(t,n=5):return ''.join(f'<i class="fm {"w" if x[2]>x[3] else "l"}"></i>' for x in WK[t][-n:])
def card(a,b,w,label):
    def side(x,cl):
        sd=seed(x);tag=f'<span class="pos sd">Seed {sd}</span>' if sd<=6 else f'<span class="pos sd out">#{sd} · out</span>'
        return f'<div class="mus {cl}">{chip(sd)}<b>{e(x)}</b><span class="mrec">{T[x][0]}-{T[x][1]}</span><span class="mform">{form(x)}</span></div>'
    pa=winp(a,b,w);pb=100-pa
    rows=[('Best lineup',f'{PT[(a,w)]:.1f}',f'{PT[(b,w)]:.1f}',PT[(a,w)],PT[(b,w)]),
          ('Win chance',f'{pa}%',f'{pb}%',pa,pb),
          ('PF / wk',f'{T[a][5]:.1f}',f'{T[b][5]:.1f}',T[a][5],T[b][5]),
          ('PF rank',f'#{T[a][4]}',f'#{T[b][4]}',-T[a][4],-T[b][4]),
          ('All-play',f'{T[a][10]}-{T[a][11]}',f'{T[b][10]}-{T[b][11]}',T[a][10],T[b][10]),
          ('Every-week H2H',*(lambda w,l:(f'{w}-{l}',f'{l}-{w}',w,l))(sum(p[2]>q[2] for p,q in zip(WK[a],WK[b])),sum(p[2]<q[2] for p,q in zip(WK[a],WK[b])))),
          ('Luck',f'{T[a][12]:+.2f}',f'{T[b][12]:+.2f}',None,None),
          (MB.HRLAB,*[MB.hrval(MB.hr_count([mp(q,w) for q in setlineup(x,w)]),MB.hr_count(MB.optimal([mp(q,w) for q in pool(x,w)]))) for x in (a,b)],None,None)]
    cmp=''.join(f'<div class="mcr"><span class="{"up" if va is not None and va>vb else ""}">{x}</span><em>{l}</em><span class="{"up" if va is not None and vb>va else ""}">{y}</span></div>' for l,x,y,va,vb in rows)
    prev=[x for x in WK[a] if FULL[x[1]]==b]
    pv=''.join(f'<div class="mprev">Week {x[0]}: <b class="{"w" if x[2]>x[3] else "l"}">{e(a) if x[2]>x[3] else e(b)}</b> won {max(x[2],x[3]):.1f}–{min(x[2],x[3]):.1f}</div>' for x in prev)
    return (f'<div class="mcard"><div class="mch"><span>{label}</span></div>'
            f'<div class="mvs">{side(a,"msl")}<span class="mv2">vs</span>{side(b,"msr")}</div><div class="mcmp">{cmp}</div>{pv}</div>')
# ---------- bracket
S=H[:6]
def win(a,b,w):return a if PT[(a,w)]>=PT[(b,w)] else b
q1=(S[2],S[5]);q2=(S[3],S[4])
w1=win(*q1,15);w2=win(*q2,15)
s1=(S[0],w2);s2=(S[1],w1)
f=(win(*s1,16),win(*s2,16))
GAMES=[('qf1',15,q1,'Wild Card'),('qf2',15,q2,'Wild Card'),('sf1',16,s1,'Semi Final'),('sf2',16,s2,'Semi Final'),('fin',17,f,'Championship')]
def team_line(t,w,winner,proj_tag=False):
    return (f'<span class="bt{" bw" if t==winner else ""}">{chip(seed(t))}<span class="bn">{e(SHORT[t])}</span>'
            f'{"<i class=bpj>proj.</i>" if proj_tag else ""}<b>{PT[(t,w)]:.1f}</b></span>')
RLAB={15:'Wild Card',16:'Semi Final',17:'Championship'}
def gtile(k,w,pair,lab):
    a,b=pair;wn=win(a,b,w)
    projected={'sf1':[False,True],'sf2':[False,True],'fin':[True,True]}.get(k,[False,False])
    rn=f'<span class="brn">{RLAB[w]} · Wk {w}</span>' if w>15 else ''
    return (f'<label for="bk-{k}" class="bg g-{k}"><span class="bgh">{rn}<span class="bmt">{lab}</span></span>'+team_line(a,w,wn,projected[0])+team_line(b,w,wn,projected[1])+
            f'<span class="bgw">{winp(wn,b if wn==a else a,w)}% · {e(SHORT[wn])}</span></label>')
def byetile(k,t):
    return (f'<div class="bg bye g-{k}"><span class="bgh"><span class="bmt">Bye</span></span>'
            f'<span class="bt bw">{chip(seed(t))}<span class="bn">{e(SHORT[t])}</span></span></div>')
import po_radial
# ---------- finished games: result card + the lineups as played (same rows as Matchups' past weeks)
def fcard(a,b,w,label):
    xa,xb=AW[(a,w)],AW[(b,w)];wa=xa>xb
    side=lambda x,v,cl,won:(f'<div class="mus {cl}"><span class="hres {"w" if won else "l"}">{"WON" if won else "LOST"}</span><b>{e(x)}</b>'
        f'<span class="hsc">{v:.1f}</span><span class="hrk">Seed <i class="ch {tone(seed(x))}"><span class="ct">#{seed(x)}</span></i></span></div>')
    return (f'<div class="mcard"><div class="mch"><span>{label}</span></div>'
            f'<div class="mvs">{side(a,xa,"msl",wa)}<span class="mv2">vs</span>{side(b,xb,"msr",not wa)}</div>'
            f'<div class="hmar">Margin <b>{abs(xa-xb):.1f}</b></div></div>')
if FINAL:MB.W=0  # no current week: never mark a row for the live updater
if ACT:MB.META.update({k:v for k,v in ACT['m'].items() if k not in MB.META})
def flineup(a,b,w):
    A_,B_=ACT['w'][str(w)][str(RIDN[a])],ACT['w'][str(w)][str(RIDN[b])];MB.HW[0]=w
    sa=[MB.hp(x) for x in A_[2].split(',')];sb=[MB.hp(x) for x in B_[2].split(',')]
    hdr=f'<div class="msh lsh">Lineups</div>{MB.CTL([(MB.VSW,'Order','Lineup',MB.LSW)])}<div class="lnote">green = beat projection · red = fell short</div>'
    o=[MB.ptsrow(sa,sb)]+['<div class="lpv">']+[MB.lrow(x,y,'') for x,y in zip(sa,sb)]+['</div>',MB.sview(sa,sb)]
    ba=sorted([MB.hp(x) for x in A_[3].split(',') if x],key=lambda q:-q[5]);bb=sorted([MB.hp(x) for x in B_[3].split(',') if x],key=lambda q:-q[5])
    if ba or bb:o+=[MB.BH_HIST]+[MB.lrow(ba[k] if k<len(ba) else None,bb[k] if k<len(bb) else None,'') for k in range(max(len(ba),len(bb)))]
    h='<div class="lus">'+hdr+'<div class="lus-a">'+''.join(o)+'</div>'+MB.optblock(sa,sb,sa+ba,sb+bb,A_[1],B_[1],False,MB.BH_HIST)+'</div>'
    return h.replace('for="lo-a"','for="blo-a"').replace('for="lo-o"','for="blo-o"').replace('for="lv-p"','for="blv-p"').replace('for="lv-s"','for="blv-s"')
import po_cols
def _plive(t,w):
    """bracket row: (points, projection, started) - the live week from the Matchups data, played weeks as scored"""
    if w==MB.W and not FINAL and str(RIDN[t]) in MB.LW['out']:
        st=[p for p in MB.LW['out'][str(RIDN[t])]['st'] if p];on=any(MB.lval(p)[1] or p[5]!=0 for p in st)
        return sum(p[5] for p in st),MB._lp(t)[0],on
    if (t,w) in AW:return AW[(t,w)],PT[(t,w)],True
    return 0.0,PT[(t,w)],False
# bracket names: the league's short names where it has them; otherwise long names cut to two words, or initial + last word
def _bn(t):
    if SHORT0.get(t,t)!=t:return SHORT0[t]
    if len(t)<=15:return t
    w=t.replace(',','').split();two=' '.join(w[:2])
    return two if len(two)<=15 else f'{w[0][0]}. {w[-1]}'
_BN={t:_bn(t) for t in H}
br,BRCSS,_RH=po_cols.build(S,GAMES,win,winp,PT,_BN,seed,e,tone,(lambda a,b,w:f'+{abs(PT[(a,w)]-PT[(b,w)]):.1f}') if FINAL else None,
                           av=lambda t:f'av-{MB._AVR[t]}' if t in MB._AVR else '',live=_plive)
bpan=''.join(f'<div class="bkp bkp-{k}">{fcard(a,b,w,f"Week {w} · {lab} · Final")}{flineup(a,b,w)}</div>' if FINAL else f'<div class="bkp bkp-{k}">{card(a,b,w,f"Week {w} · {lab}")}{lineup(a,b,w,'b')}</div>' for k,w,(a,b),lab in GAMES)
# ---------- build-a-matchup (team A, team B, week)
def dd(k,lab):
    return (f'<details class="dd dd-{k}"><summary><span class="ddk">{lab}</span>'+''.join(f'<span class="sv sv-{i}">{e(SHORT[t])}</span>' for i,t in enumerate(H))+
            '<svg viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></summary>'
            f'<div class="ddm">'+''.join(f'<label for="p{k}-{i}"><i>{i+1}</i>{e(t)}</label>' for i,t in enumerate(H))+'</div></details>')
WSP=len({json.dumps([[q and q['pid'] for q in BEST[(t,w)]] for t in H]) for w in WEEKS})>1 or bool(PROJ)
def bpanel(i,j):
    a,b=H[i],H[j]
    if WSP:
        return ''.join(f'<div class="ppn pp-{i}-{j}-{w}">{card(a,b,w,f"Week {w} · {RND[w]}")}{lineup(a,b,w)}</div>' for w in WEEKS)
    lab=''.join(f'<span class="pwl pwl-{w}">Week {w} · {RND[w]}</span>' for w in WEEKS)
    return f'<div class="ppn pp-{i}-{j}">{card(a,b,15,lab)}{lineup(a,b,15)}</div>'
radios=('<input type="radio" name="pview" id="pv-b" class="lr" checked><input type="radio" name="pview" id="pv-c" class="lr">'+''.join(f'<input type="radio" name="bk" id="bk-{k}" class="lr"{" checked" if n==0 else ""}>' for n,(k,*_) in enumerate(GAMES))+
        ''.join(f'<input type="radio" name="pa" id="pa-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(lg.N))+
        ''.join(f'<input type="radio" name="pb" id="pb-{i}" class="lr"{" checked" if i==1 else ""}>' for i in range(lg.N))+
        ''.join(f'<input type="radio" name="pw" id="pw-{w}" class="lr"{" checked" if w==17 else ""}>' for w in WEEKS)+
        ''.join(f'<input type="radio" name="{k}lopt" id="{k}lo-a" class="lr" checked><input type="radio" name="{k}lopt" id="{k}lo-o" class="lr"><input type="radio" name="{k}lview" id="{k}lv-p" class="lr" checked><input type="radio" name="{k}lview" id="{k}lv-s" class="lr">' for k in 'bp'))
import gzip,base64
if FINAL:PPX=''
elif WSP:
    _M={f'{i}-{j}-{w}':f'<div class="ppn">{card(H[i],H[j],w,f"Week {w} · {RND[w]}")}{lineup(H[i],H[j],w)}</div>' for i in range(lg.N) for j in range(lg.N) if i!=j for w in WEEKS}
    open(P+'po_static.html','w',encoding='utf-8').write(''.join(f'<div class="ppn pp-{k}">{v[17:]}' for k,v in _M.items()))
    open(P+'po_static.css','w').write(','.join(f'#pa-{i}:checked~#pb-{j}:checked~#pw-{w}:checked~.pp-{i}-{j}-{w}' for i in range(lg.N) for j in range(lg.N) if i!=j for w in WEEKS)+'{display:block}')
    _Z=base64.b64encode(gzip.compress(json.dumps(_M,separators=(",",":")).encode(),9,mtime=0)).decode()
    PPX=('<div class="ppx" aria-live="polite"></div><script type="text/plain" id="ppz">'+_Z+'</script>'
         '<script>(function(){var M=null,P=null,x=document.querySelector(".ppx");'
         'function v(n){var r=document.querySelector("input[name="+n+"]:checked");return r?r.id.split("-")[1]:null}'
         'function load(){if(P)return P;var b=atob(document.getElementById("ppz").textContent),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);'
         'P=new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream("gzip"))).text().then(function(t){M=JSON.parse(t)});return P}'
         'function draw(){var a=v("pa"),b=v("pb"),w=v("pw");if(a===b){x.innerHTML="";return}'
         'load().then(function(){x.innerHTML=M[a+"-"+b+"-"+w]||""}).catch(function(){x.innerHTML=\'<div class="psame" style="display:block">This browser cannot open the matchup builder.</div>\'})}'
         'document.addEventListener("change",function(e){var n=e.target&&e.target.name;if(n==="pa"||n==="pb"||n==="pw")draw()});'
         'if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",draw);else draw()})()</script>')
else:
    PPX=''.join(bpanel(i,j) for i in range(lg.N) for j in range(lg.N) if i!=j)
wk='<div class="pseg pwk" role="group" aria-label="Week">'+''.join(f'<label for="pw-{w}">Wk {w}</label>' for w in WEEKS)+'</div>'
def placings():
    # places 1-6 from the placement games (1st, 3rd, 5th) in the winners bracket; 7-10 by regular-season seed
    if not ACT:return ''
    RNi={int(k):v for k,v in _RN.items()};pl={}
    for m in ACT['bracket']:
        if m.get('p') in(1,3,5) and m.get('w'):pl[m['p']]=RNi[m['w']];pl[m['p']+1]=RNi[m['l']]
    if len(pl)<6:return ''
    for i,t in enumerate(H[6:]):pl[7+i]=t
    rows=''.join(f'<div class="pfpr{" pfp1" if p_==1 else ""}"><em>{p_}</em>{chip(seed(pl[p_]))}<b>{e(pl[p_])}</b><span class="pfprc">{T[pl[p_]][0]}-{T[pl[p_]][1]}</span></div>' for p_ in sorted(pl))
    return '<div class="msh pfph">Final placings<small>playoff results, then regular-season seed</small></div><div class="pfpx">'+rows+'</div>'
if FINAL:
    sec=('<section class="pox" aria-labelledby="poh">'+radios+
         '<div class="posh"><b id="poh">Playoffs</b></div><div class="prsub">Final · seeds by record, then points for</div>'+br+
         '<div class="bkx">'+bpan+'</div>'+placings()+'</section>')
else:
    sec=('<section class="pox" aria-labelledby="poh">'+radios+
     '<div class="posh"><b id="poh">Playoffs</b></div><div class="prsub">If the season ended today · seeds by record, then points for</div>'
     '<div class="pseg pvw" role="group" aria-label="Playoff view"><label for="pv-b">Bracket</label><label for="pv-c">Custom</label></div>'+br+
     '<div class="bkx">'+bpan+'</div>'
     '<div class="cpk ppk">'+dd('a','A')+dd('b','B')+'</div>'+wk+
     '<div class="psame">Pick two different teams.</div>'+PPX+'</section>')
def _lc(k,sc):
    q=lambda r,t:','.join(f'#{k}{r}:checked~{c} {t}' for c in sc)
    return (q('lo-a',f'.lsw label[for="{k}lo-a"]')+','+q('lo-o',f'.lsw label[for="{k}lo-o"]')+','+q('lv-p',f'.lvw label[for="{k}lv-p"]')+','+q('lv-s',f'.lvw label[for="{k}lv-s"]')+'{background:var(--chalk);color:var(--ink)}'
            +q('lo-o','.hrv-a')+'{display:none}'+q('lo-o','.hrv-o')+'{display:inline}'+q('lo-o','.lus-a')+'{display:none}'+q('lo-o','.lus-o')+'{display:block}'+q('lv-s','.lsv')+'{display:block}'+q('lv-s','.lpv')+'{display:none}')
css=_lc('b',['.bkx'])+_lc('p',['.ppx','.ppn'])
css+=('.pvw{display:inline-flex;margin:0 0 14px}#pv-b:checked~.pvw label[for="pv-b"],#pv-c:checked~.pvw label[for="pv-c"]{background:var(--chalk);color:var(--ink)}'
      '#pv-c:checked~.prd,#pv-c:checked~.rkey,#pv-c:checked~.bkx,'
      '#pv-b:checked~.ppk,#pv-b:checked~.pwk,#pv-b:checked~.psame,#pv-b:checked~.ppx,#pv-b:checked~.ppn{display:none!important}')
css+=BRCSS+''.join(f'#bk-{k}:checked~.pbr label[for="bk-{k}"]{{border-color:var(--chalk);box-shadow:inset 0 0 0 1px var(--chalk)}}#bk-{k}:checked~.prd label[for="bk-{k}"]{{border-color:var(--chalk);background:var(--deck-2)}}#bk-{k}:checked~.bkx .bkp-{k}{{display:block}}' for k,*_ in GAMES)
css+=''.join(f'#pa-{i}:checked~.ppk .dd-a .sv-{i},#pb-{i}:checked~.ppk .dd-b .sv-{i}{{display:inline}}#pa-{i}:checked~.ppk .dd-a label[for="pa-{i}"],#pb-{i}:checked~.ppk .dd-b label[for="pb-{i}"]{{background:var(--chalk);color:var(--ink)}}#pa-{i}:checked~#pb-{i}:checked~.psame{{display:block}}' for i in range(lg.N))
css+=''.join(f'#pw-{w}:checked~.pwk label[for="pw-{w}"]{{background:var(--chalk);color:var(--ink)}}' for w in WEEKS)
if WSP:
    css+='.ppx .ppn{display:block}'
else:
    css+=','.join(f'#pa-{i}:checked~#pb-{j}:checked~.pp-{i}-{j}' for i in range(lg.N) for j in range(lg.N) if i!=j)+'{display:block}'
    css+=''.join(f'#pw-{w}:checked~.ppn .pwl-{w}{{display:inline}}' for w in WEEKS)
css+=('.pox .pfph{margin-top:22px;display:flex;justify-content:space-between;align-items:baseline;gap:10px}.pox .pfph small{font-family:var(--body);font-weight:500;font-size:11px;letter-spacing:0;text-transform:none;color:var(--steel)}.pfph{margin-bottom:8px}.pfpx{display:flex;flex-direction:column;gap:4px}'
      '.pfpr{display:grid;grid-template-columns:1.6em 2.9em minmax(0,1fr) auto;align-items:center;gap:8px;padding:7px 10px;border:1px solid var(--hair);border-radius:6px;background:var(--ink)}'
      '.pfpr>em{font-style:normal;font-family:var(--display);font-weight:700;font-size:15px;color:var(--steel);text-align:right;font-variant-numeric:tabular-nums}'
      '.pfpr>b{font-weight:600;color:var(--chalk);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'
      '.pfpr .pfprc{color:var(--steel);font-variant-numeric:tabular-nums;font-size:.92em}'
      '.pfpr.pfp1>em{color:#e8c15a}.pfpr>.ch{justify-self:start}') if FINAL else ''
open(P+'po_section.html','w',encoding='utf-8').write(sec);open(P+'po_css.css','w',encoding='utf-8').write(css)
if __name__=='__main__':
    print('seeds',[SHORT[t] for t in S],'WSP',WSP,'size',len(sec))
    for k,w,(a,b),lab in GAMES:print(k,w,SHORT[a],PT[(a,w)],SHORT[b],PT[(b,w)],winp(a,b,w))
