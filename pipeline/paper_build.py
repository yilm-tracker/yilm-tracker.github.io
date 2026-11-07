import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# PAPER TRAIL tab (Front Office, after Drafts; Nicklaus 2026-11-04). Identical file in both trackers.
#   BBP (dynasty): every draft pick's chain of owners (season + round + ORIGINAL team) and every player's moves since
#     2021, from the normalised MFL 2021-24 + Sleeper 2025+ log (history/paper_audit.py over history/paper/, refreshed
#     by history/paper_pull.mjs in weekly runs). Import picks that only re-create an end-of-MFL roster spot are hidden
#     (carryover); a pick that changed hands with no transaction gets a "commissioner move, no trade logged" step.
#   YILM (redraft): players only, from the saved Sleeper captures (history/raw/<year>/core.json.gz) plus the season's
#     draft (history/drafts.json, CI only).
# Writes paper_section.html (lists, sheet shell, data PT, script) and paper_css.css. Rows of the sheets are rendered by
# the script from PT; deep links #paper-trail/pick/<year>-<round>-<team slug> and #paper-trail/player/<sleeper id>.
import json,html,re,os,sys,gzip,collections,datetime as dt
from zoneinfo import ZoneInfo
P=__DTP__
e=html.escape
ET=ZoneInfo('America/New_York')
sys.path.insert(0,P)
from nfl_colors import badge_c as badge
PC={'QB':'#f7739c','RB':'#3ddcc1','WR':'#5ec6f4','TE':'#fca95c','K':'#c491ff','DEF':'#c98a72'}
def day(ms):return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).astimezone(ET).strftime('%Y-%m-%d')
def slug(t):return re.sub(r'[^a-z0-9]+','-',str(t).lower()).strip('-')
SEASON=int(os.environ.get('DT_SEASON') or 0) or None
def nk(n):
    n=str(n or '');n=re.sub(r"[.'’`,]",'',n.lower()).replace('-',' ');n=re.sub(r'\b(jr|sr|ii|iii|iv|v)\b','',n);return re.sub(r'\s+',' ',n).strip()

T=[];TI={}
def ti(name):
    if name is None:return -1
    if name not in TI:TI[name]=len(T);T.append(name)
    return TI[name]
PL={}        # sid -> [name, pos, nfl, current team idx]
H=collections.defaultdict(list)   # sid -> rows [season, date, kind, a, b, x]
K={};C={}    # picks: key -> [year, round, orig idx, owner idx, used label, used sid]; key -> chain rows
SRC={}       # season -> 'MFL' | 'Sleeper'
PICKS=False

if _dt_os.path.exists(P+'history/paper/sleeper_2025.json'):
    # ------------------------------------------------------------------ BBP: MFL + Sleeper, picks and players
    PICKS=True
    sys.path.insert(0,P+'history')
    import paper_audit as A
    try:  # approved short team names (DESIGN.md §2.16), single source: PSN in pos/build_pos.py
        import ast;PSN=ast.literal_eval(re.search(r'^PSN=(\{.*?\})',open(P+'pos/build_pos.py',encoding='utf-8').read(),re.M).group(1))
    except Exception:PSN={}
    try:import draft_build as DB  # Drafts' NFL draft slot lookup (nflslot: same data, matching and UDFA rule)
    except Exception:DB=None
    SP=A.SP
    for y in A.MY:SRC[y]='MFL'
    for y in A.SY:SRC[y]='Sleeper'
    last=A.SY[max(A.SY)]
    HOLD={}
    for r in last['rosters']:
        for p in r['players'] or []:HOLD[p]=A.ST.get(r['roster_id'])
    for t in sorted(set(A.ST.values())):ti(t)
    def pkey(k):
        m=re.match(r'(\d+) R(\d+) \((.*)\)',k);return (int(m.group(1)),int(m.group(2)),m.group(3)) if m else None
    def kslug(y,r,o):return f'{y}-{r}-{slug(o)}'
    def ref(m):
        if m[0]=='player':return 'p'+str(m[1])
        if m[0]=='pick':
            q=pkey(m[1]);return 'k'+kslug(*q) if q else None
        if m[0]=='faab':return '$'+(f'{m[1]:g}')
    DPOS={}  # fantasy position from the drafts when Sleeper lists a non-fantasy one (Travis Hunter: CB)
    for _y,_d in A.SY.items():
        for _dd in _d['drafts']:
            for _p in _dd['picks'] or []:
                _q=(_p.get('metadata') or {}).get('position')
                if _q in PC:DPOS[str(_p['player_id'])]=_q
    def pinfo(sid):
        if sid not in PL:
            s=SP.get(sid) or [sid,None,None]
            pos=s[1] if s[1] in PC else DPOS.get(sid,s[1] or '')
            PL[sid]=[s[0],pos,s[2] or '',ti(HOLD.get(sid))]
    def dlabel(ev):
        y,r,s=ev['slot']
        if ev.get('kind') in('import','supplemental'):s=ev['pick_no']-(r-1)*10
        return f'{r}.{s:02d}'
    for ev in A.EV:
        y=ev['season'];d=day(ev['ts']);ty=ev['type']
        if ev.get('carryover'):continue
        for m in ev['moves']:
            if m[0]!='player':continue
            sid=str(m[1]);pinfo(sid)
            if ty=='trade':
                ret=[x for x in (ref(mm) for mm in ev['moves'] if m[2] is not None and mm[3]==m[2]) if x]
                wth=[x for x in (ref(mm) for mm in ev['moves'] if mm is not m and mm[2]==m[2] and mm[3]==m[3]) if x]
                H[sid].append([y,d,'T',ti(m[3]),ti(m[2]),ret,wth])
            elif ty=='draft':
                kd={'startup':'s','rookie':'r','import':'i','supplemental':'p'}.get(ev.get('kind'),'r')
                q=pkey(ev['pick']) if ev.get('pick') else None
                H[sid].append([y,d,'R',ti(m[3]),-1,[dlabel(ev),kd,kslug(*q) if q else '']])
            elif ty in('waiver','free_agent','commissioner'):
                if m[3]:
                    k={'waiver':'W','free_agent':'A','commissioner':'CA'}[ty]
                    H[sid].append([y,d,k,ti(m[3]),-1,[f'{ev["bid"]:g}'] if k=='W' and ev.get('bid') is not None else []])
                if m[2]:H[sid].append([y,d,'CD' if ty=='commissioner' else 'D',-1,ti(m[2]),[]])
    # picks: every season/round/team from the first rookie draft to the furthest future pick
    rounds=int((last['league'].get('settings') or {}).get('draft_rounds') or 4)
    yrs=[int(k[:4]) for k in A.CH]+[int(tp['season']) for tp in last.get('traded_picks') or []]
    cur=int(last['league']['season']);Y0=2022;Y1=max(yrs+[cur+2])
    steps=collections.defaultdict(list)
    for ev in A.EV:
        for m in ev['moves']:
            if m[0]=='pick' and pkey(m[1]):steps[pkey(m[1])].append((ev,m))
        if ev['type']=='draft' and ev.get('pick') and pkey(ev['pick']):steps[pkey(ev['pick'])].append((ev,None))
    for y in range(Y0,Y1+1):
        for r in range(1,rounds+1):
            for o in sorted(set(A.ST.values())):
                q=(y,r,o);key=kslug(*q);own=o;rows=[];used=None
                for ev,m in sorted(steps.get(q,[]),key=lambda z:z[0]['ts']):
                    d=day(ev['ts'])
                    if m is None:  # used in a draft
                        by=ev['teams'][0]
                        if by!=own:rows.append([ev['season'],d,'M',ti(by),ti(own),[]]);own=by
                        sid=str(ev['moves'][0][1]);pinfo(sid);used=[dlabel(ev),sid]
                        rows.append([ev['season'],d,'U',ti(by),-1,[dlabel(ev),sid]]);continue
                    if m[2]!=own:rows.append([ev['season'],d,'M',ti(m[2]),ti(own),[]])
                    ret=[x for x in (ref(mm) for mm in ev['moves'] if mm[3]==m[2]) if x]
                    wth=[x for x in (ref(mm) for mm in ev['moves'] if mm is not m and mm[2]==m[2] and mm[3]==m[3]) if x]
                    rows.append([ev['season'],d,'T',ti(m[3]),ti(m[2]),ret,wth]);own=m[3]
                if y<=cur and not used and y<2025 and not rows:continue
                K[key]=[y,r,ti(o),ti(own),used[0] if used else '',used[1] if used else '']
                C[key]=rows
    TEAMNOW=sorted(set(A.ST.values()))
    # projected slot of every undrafted pick (2026-11-06): reverse current H2H seed of the ORIGINAL team, from the same
    # `const H` (data_block.js) the Standings board draws; same slots for every round and year; Median ignored.
    # Weeks 15-17: H stays the final regular-season order (run.py caps at Week 14). Offseason (G=0, every team 0-0):
    # the previous season's final seeds, kept in paper_seeds.json (written whenever G>0; weekly runs commit pipeline/).
    try:
        _db=open(P+'data_block.js',encoding='utf-8').read()
        HS=json.loads(re.search(r'const H=(\[.*?\]);',_db).group(1));_G=int(re.search(r'const G=(\d+);',_db).group(1))
    except Exception:HS,_G=[],0
    _SF=P+'paper_seeds.json'
    if _G>0 and HS:
        _sv={'season':cur,'G':_G,'H':HS}
        if not _dt_os.path.exists(_SF) or json.load(open(_SF,encoding='utf-8'))!=_sv:
            json.dump(_sv,open(_SF,'w',encoding='utf-8'),ensure_ascii=False)
    elif _dt_os.path.exists(_SF):HS=json.load(open(_SF,encoding='utf-8'))['H']
    else:HS=[]
    SLOT={t:len(HS)-i for i,t in enumerate(HS)}
    PAST={v[0] for v in K.values() if v[4]}
    for k,v in K.items():
        s=SLOT.get(T[v[2]]) if v[0] not in PAST else None
        v.append(f'{v[1]}.{s:02d}' if s else '')
else:
    # ------------------------------------------------------------------ YILM: Sleeper captures, players only
    ROOT=P.split('/.season/')[0]+'/pipeline/' if '/.season/' in P else P
    RAW=ROOT+'history/raw/'
    yrs=sorted(int(y) for y in os.listdir(RAW) if y.isdigit() and os.path.exists(RAW+y+'/core.json.gz')) if os.path.isdir(RAW) else []
    if SEASON:yrs=[y for y in yrs if y<=SEASON]
    CORE={y:json.load(gzip.open(RAW+f'{y}/core.json.gz')) for y in yrs}
    PLM={}
    for y in yrs:
        try:PLM.update(next(iter(json.load(gzip.open(RAW+f'{y}/players.json.gz')).values())))
        except Exception:pass
    def g(C_,suf):return next((v for k,v in C_.items() if re.search(r'/league/\d+'+suf+'$',k)),None)
    cy=max(yrs) if yrs else None
    def tname(u):
        md=(u or {}).get('metadata') or {};return md.get('team_name') or (u or {}).get('display_name')
    NOW={}  # owner id -> current team name
    if cy:
        try:
            import lg as _lg;RN=_lg.RN
        except Exception:RN={}
        U={u['user_id']:u for u in g(CORE[cy],'/users') or []}
        for r in g(CORE[cy],'/rosters') or []:NOW[r['owner_id']]=RN.get(r['roster_id']) or tname(U.get(r['owner_id']))
    RT={}   # (year, roster id) -> team name (current name of the same manager when he is still in the league)
    for y in yrs:
        U={u['user_id']:u for u in g(CORE[y],'/users') or []}
        for r in g(CORE[y],'/rosters') or []:RT[(y,r['roster_id'])]=NOW.get(r['owner_id']) or tname(U.get(r['owner_id'])) or f'Team {r["roster_id"]}'
    for t in sorted(set(NOW.values())):ti(t)
    HOLD={}
    if cy:
        for r in g(CORE[cy],'/rosters') or []:
            for p in r.get('players') or []:HOLD[p]=RT.get((cy,r['roster_id']))
    def pinfo(sid):
        if sid not in PL:
            p=PLM.get(sid) or {}
            nm=p.get('full_name') or ' '.join(x for x in (p.get('first_name'),p.get('last_name')) if x) or sid
            PL[sid]=[nm,p.get('position') or '',p.get('team') or '',ti(HOLD.get(sid))]
    EVS=[]
    for y in yrs:
        SRC[y]='Sleeper'
        for k,v in CORE[y].items():
            if '/transactions/' not in k:continue
            for t in v or []:
                if t.get('status')=='complete':EVS.append((y,t))
    by_nm=collections.defaultdict(list)
    for sid,p in PLM.items():by_nm[(nk(p.get('full_name') or ''),p.get('position'))].append(sid)
    DR=json.load(open(P+'history/drafts.json',encoding='utf-8')) if _dt_os.path.exists(P+'history/drafts.json') else {}
    for ys,dd in DR.items():
        try:y=int(ys)
        except Exception:continue
        if y not in yrs:continue
        raw=(dd.get('raw') or {}).get('picks') or []
        nt=int(dd.get('teams') or len(NOW) or 12);dd_=day(dd['start']) if dd.get('start') else f'{y}-08-31'
        for i,row in enumerate(dd.get('picks') or []):
            rd,pk,sl,orig,byn,pname,pos=row[:7]
            c=by_nm.get((nk(pname),pos)) or []
            if len(c)!=1:continue
            rid=raw[i][3] if i<len(raw) and len(raw[i])>3 else None
            team=RT.get((y,rid)) or byn
            sid=c[0];pinfo(sid)
            H[sid].append([y,dd_,'R',ti(team),-1,[f'{rd}.{int(pk)-(int(rd)-1)*nt:02d}','d','']])
    for y,t in sorted(EVS,key=lambda z:z[1].get('status_updated') or z[1].get('created') or 0):
        d=day(t.get('status_updated') or t.get('created'));ty=t['type'];RN_=lambda rid:RT.get((y,rid))
        adds=t.get('adds') or {};drops=t.get('drops') or {}
        if ty=='trade':
            for sid,rid in adds.items():
                pinfo(sid);frm=drops.get(sid)
                ret=['p'+s2 for s2,r2 in adds.items() if frm is not None and r2==frm]+[f'${w["amount"]:g}' for w in t.get('waiver_budget') or [] if frm is not None and w['receiver']==frm]
                wth=['p'+s2 for s2,r2 in adds.items() if s2!=sid and r2==rid and drops.get(s2)==frm]
                H[sid].append([y,d,'T',ti(RN_(rid)),ti(RN_(frm)) if frm else -1,ret,wth])
            continue
        for sid,rid in adds.items():
            pinfo(sid);k={'waiver':'W','free_agent':'A','commissioner':'CA'}.get(ty,'A')
            bid=(t.get('settings') or {}).get('waiver_bid')
            H[sid].append([y,d,k,ti(RN_(rid)),-1,[f'{bid:g}'] if k=='W' and bid is not None else []])
        for sid,rid in drops.items():
            pinfo(sid);H[sid].append([y,d,'CD' if ty=='commissioner' else 'D',-1,ti(RN_(rid)),[]])
    TEAMNOW=sorted(set(NOW.values()))

# every row in date order (stable: a draft or claim before a same-day drop)
for sid in H:H[sid].sort(key=lambda r:(r[1],{'R':0,'T':1,'W':2,'A':2,'CA':2,'M':3,'D':4,'CD':4,'U':5}.get(r[2],3)))
PT=dict(T=T,S={str(k):v for k,v in SRC.items()},P=PL,H=H,K=K,C=C,Z={t:slug(t) for t in T})
_js=json.dumps(PT,separators=(',',':'),ensure_ascii=False)
if __name__=='__main__' and '--stats' in sys.argv:
    print('teams',len(T),'players',len(PL),'rows',sum(len(v) for v in H.values()),'picks',len(K),'chain rows',sum(len(v) for v in C.values()),'json',len(_js))
    raise SystemExit

# ====================================================================== page
CUR=max(SRC) if SRC else 0
FIRST=min(SRC) if SRC else 0
def av(t,cls=''):return f'<i class="pav{(" "+cls) if cls else ""}" data-avt="{e(t)}" aria-hidden="true"></i>'
out=[f'<section class="ptx" aria-labelledby="pth"><div class="posh"><b id="pth">Paper Trail</b><span class="wsub">'
     +(f'Every pick and every player move since {FIRST} · tap one for its full history' if PICKS else f'Every player move since {FIRST} · tap a player for his full history')
     +'</span></div>']
if PICKS:
    out.append('<div class="ptsw" role="group" aria-label="Show"><button type="button" class="ptb on" data-v="k" aria-pressed="true">Picks</button>'
               '<button type="button" class="ptb" data-v="p" aria-pressed="false">Players</button></div>')
    years=sorted({v[0] for v in K.values()})
    past={v[0] for v in K.values() if v[4]}
    dflt=next((y for y in years if y not in past),years[-1])
    out.append('<div class="ptv ptv-k">'+''.join(f'<input type="radio" name="pty" id="pty-{y}" class="lr"{" checked" if y==dflt else ""}>' for y in years))
    out.append(f'<div class="ptyb yrs n{len(years)}" role="group" aria-label="Draft year">'+''.join(
        f'<label class="yb" for="pty-{y}"><b>{y}</b><small>{"Drafted" if y in past else "Future"}</small></label>' for y in years)+'</div>')
    for y in years:
        out.append(f'<div class="ptyx ptyx-{y}">')
        ks=[k for k,v in K.items() if v[0]==y]
        for r in sorted({K[k][1] for k in ks}):
            rk=[k for k in ks if K[k][1]==r]
            rk.sort(key=lambda k:(K[k][4] or K[k][6] or 'z',T[K[k][2]]))  # pick order; future picks by projected slot
            rows=[]
            for k in rk:
                yy,rr,o,own,lab,sid,pj=K[k];n=sum(1 for x in C[k] if x[2] in('T','M'))
                # row (2026-11-06): tile | holder (drafted: player on line 2) | TRADED (RPTS-style tile "n×") | VIA (original
                # team logo, or "–" when the holder is the original team). .ptbl = zero-size marker on the name's baseline
                # (ptxFit centres the TRADED tile and the dash on the name's cap centre).
                if lab:
                    pl=PL.get(sid) or ['?','','',-1]
                    tile=f'<i class="ptn{"" if pl[1] in PC else " ptn0"}" style="--pc:{PC.get(pl[1],"var(--row-divider)")}"><b>{lab}</b><span>{e(pl[1])}</span></i>'
                    ns=DB.nflslot(pl[0],pl[1],yy) if DB else None
                    if ns=='UDFA':nsh,nsa='<span class="ptns" title="Undrafted free agent"><i>UDFA</i><i class="ptbl"></i></span>',', NFL undrafted free agent'
                    elif ns:nsh,nsa=f'<span class="ptns" title="NFL draft {ns[0]}: round {ns[1]}, pick {ns[2]} overall"><i>RD {ns[1]}</i><i>PK {ns[2]}</i><i class="ptbl"></i></span>',f', NFL round {ns[1]}, pick {ns[2]}'
                    else:nsh,nsa='<span class="ptns"><i>–</i><i class="ptbl"></i></span>',''
                    nsa=f', drafted {e(pl[0])}'+nsa
                    sub=f'<span class="ptl2"><span class="ptpn" title="{e(pl[0])}">{e(pl[0])}<i class="ptbl"></i></span>{badge(pl[2]) if pl[2] else ""}{nsh}</span>'
                else:
                    tile=f'<i class="ptn ptn0 ptpj"><b>{pj or "R"+str(rr)}</b></i>'
                    sub='';nsa=''
                via=own!=o
                # VIA banner: Drafts' .dfvia with the ORIGINAL team's coach (draft_build.own); rows without one keep its height
                coach=(DB.own(T[o]) if DB else T[o])
                vb=(f'<small class="dfvia ptvb"><i>via</i>{e(coach)}</small>' if via else '<small class="dfvia ptvb ptv0" aria-hidden="true"><i>via</i>X</small>')
                num=(f'pick {lab}' if lab else f'projected pick {pj}' if pj else f'round {rr}')
                ttl=(' title="via '+e(T[o])+'"') if via else ''
                rows.append(f'<button type="button" class="ptk" data-k="{k}"{ttl} aria-label="{y} round {rr}, {num}, {e(T[own])}, traded {n}×{(", via "+e(T[o])) if via else ""}{nsa}, history">{tile}'
                            f'<span class="ptm"><span class="ptl1">{av(T[own])}<b class="ptt"{(' data-ab="'+e(PSN[T[own]])+'" title="'+e(T[own])+'"') if PSN.get(T[own]) else ''}>{e(T[own])}<i class="ptbl"></i></b></span>{sub}</span>'
                            f'<span class="ptxc">{vb}<i class="ptxn{"" if n else " z"}"><b>{n}</b><small>×</small></i></span></button>')
            out.append(f'<div class="ptp"><div class="pthd"><span>R{r}</span><span>Team</span><span class="pthx">Traded</span></div>{"".join(rows)}</div>')
        out.append('</div>')
    out.append('</div>')
out.append(f'<div class="ptv ptv-p"{" hidden" if PICKS else ""}><input class="wq ptq" type="search" placeholder="Search player…" aria-label="Search player" autocomplete="off">'
           '<div class="ptp ptpl"><div class="pthd"><span>Moves</span><span>Player · last move</span><span>Date</span><span>GM</span></div><div class="ptlist"></div></div>'
           '<p class="ptmore"></p></div>')
out.append('<div class="key"><div>'+('<b>Picks</b> each row names the team that holds or used the pick. TRADED counts the times the pick changed hands; VIA shows the original team\'s logo. '
           'Future picks show their projected number from the current H2H standings (worst record = 1.01) and update as the standings change. The tile shows the pick number once used. '
           '' if PICKS else '')
           +'<b>Players</b> every draft, trade, waiver claim, free-agent add and drop, newest first in the list; tap for the full history. '
           +('MyFantasyLeague trades (2021-24) carry the date the commissioner entered them. Rosters carried over to Sleeper in March 2025 are not shown as moves. '
             'A pick that changed hands with no recorded trade shows as a commissioner move.' if PICKS else '')
           +'</div></div></section>')
out.append('<div class="pts" role="dialog" aria-modal="true" aria-labelledby="ptsT" hidden><div class="ptsh"><button type="button" class="ptsx" aria-label="Close">'
           '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg></button>'
           '<div class="ptsi"><h3 id="ptsT" class="ptst"></h3><div class="ptss"></div></div></div><div class="ptsb"></div></div>')
JS=r'''<script>document.addEventListener('DOMContentLoaded',function(){
const D=window.PT,X=document.querySelector('.ptx');if(!D||!X)return;
const T=D.T,MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PC={QB:'#f7739c',RB:'#3ddcc1',WR:'#5ec6f4',TE:'#fca95c',K:'#c491ff',DEF:'#c98a72'};
const av=i=>{if(i<0)return '<i class="pav ptfa" aria-hidden="true"></i>';const r=typeof AVR!=='undefined'?AVR[T[i]]:null;return '<i class="pav'+(r?' av av-'+r:' nl')+'" aria-hidden="true"></i>'};
const nfl=t=>t?'<em class="nfl n-'+esc(t)+'"><span class="ct">'+esc(t)+'</span></em>':'';
const KN=k=>{const v=D.K[k];return v?v[0]+' R'+v[1]+' ('+T[v[2]]+')':k};
const refh=r=>{const c=r[0],v=r.slice(1);if(c==='p'){const p=D.P[v];return '<button type="button" class="ptr" data-p="'+esc(v)+'">'+esc(p?p[0]:v)+'</button>'}
 if(c==='k')return '<button type="button" class="ptr" data-k="'+esc(v)+'">'+esc(KN(v))+'</button>';if(c==='$')return '<span class="ptr0">$'+esc(v)+' FAAB</span>';return ''};
const lst=a=>a.length?a.join(', '):'nothing';
const dk={s:'Startup draft',r:'Rookie draft',i:'Sleeper import',p:'Supplemental draft',d:'Draft'};
function line(r,isPick){const[y,d,k,a,b,x,w]=r,ta=a>=0?T[a]:'',tb=b>=0?T[b]:'';let l1='',l2='',who=a;
 if(k==='T'){l1='Traded to <b>'+esc(ta)+'</b>';l2=(tb?'From '+esc(tb)+' · ':'')+(w&&w.length?'with '+w.map(refh).join(', ')+' · ':'')+'for '+lst(x.map(refh))}
 else if(k==='W'){l1='Claimed by <b>'+esc(ta)+'</b>';l2='Waivers'+(x[0]?' · $'+esc(x[0])+' FAAB':'')}
 else if(k==='A'){l1='Added by <b>'+esc(ta)+'</b>';l2='Free agent'}
 else if(k==='CA'){l1='Added by <b>'+esc(ta)+'</b>';l2='Commissioner'}
 else if(k==='D'){l1='Dropped by <b>'+esc(tb)+'</b>';who=b}
 else if(k==='CD'){l1='Removed from <b>'+esc(tb)+'</b>';l2='Commissioner';who=b}
 else if(k==='R'){l1='Drafted by <b>'+esc(ta)+'</b>';l2=(dk[x[1]]||'Draft')+' · '+esc(x[0])+(x[2]&&D.K[x[2]]&&D.K[x[2]][2]!==a?' · '+refh('k'+x[2]):'')}
 else if(k==='U'){l1='Used by <b>'+esc(ta)+'</b>';l2=esc(x[0])+' · '+refh('p'+x[1])}
 else if(k==='M'){l1='Moved to <b>'+esc(ta)+'</b>';l2='From '+esc(tb)+' · commissioner, no trade logged'}
 const m=+d.slice(5,7),dd=+d.slice(8,10);
 return '<div class="pte"><span class="ptdt"><i>'+MO[m-1]+'</i><b>'+dd+'</b></span>'+av(who)+'<span class="ptx1"><span class="pta">'+l1+'</span>'+(l2?'<span class="ptb2">'+l2+'</span>':'')+'</span></div>'}
function body(rows,isPick){let h='',cur=null;
 for(const r of rows){const y=r[0];if(y!==cur){cur=y;h+='<div class="ptsy"><span>'+y+'</span><span>'+esc(D.S[y]==='MFL'?'MyFantasyLeague':'Sleeper')+'</span></div>'}h+=line(r,isPick)}
 return h||'<p class="ptnone">No moves yet.</p>'}
const S=document.querySelector('.pts'),ST=S.querySelector('.ptst'),SS=S.querySelector('.ptss'),SB=S.querySelector('.ptsb');let back=null,pushed=false;
function show(kind,id,push){let t='',s='',rows=[];
 if(kind==='player'){const p=D.P[id];if(!p)return false;rows=D.H[id]||[];
   t='<span class="ptsn">'+esc(p[0])+'</span>'+nfl(p[2]);
   s='<span class="ptsl">'+(p[1]?'<i class="pz p-'+esc(p[1].toLowerCase())+'">'+esc(p[1])+'</i>':'')+(p[3]>=0?av(p[3])+'<span>On <b>'+esc(T[p[3]])+'</b></span>':'<span>Not on a roster</span>')+'</span>'
     +'<span class="ptsm">'+rows.length+' move'+(rows.length===1?'':'s')+(rows.length?' since '+rows[0][1].slice(0,4):'')+'</span>';
   rows=rows.slice().reverse()}
 else{const v=D.K[id];if(!v)return false;rows=D.C[id]||[];
   t='<span class="ptsn">'+v[0]+' · Round '+v[1]+'</span>';
   s='<span class="ptsl">'+av(v[2])+'<span><b>'+esc(T[v[2]])+'</b>’s pick</span></span>'
     +'<span class="ptsm">'+(!v[4]&&v[6]?'Projected '+esc(v[6])+' · ':'')+(v[4]?'Pick '+esc(v[4])+' · used by '+esc(T[v[3]])+' · '+refh('p'+v[5]):(v[3]===v[2]?'Not traded · ':'')+'Owned by '+esc(T[v[3]]))+'</span>';
   rows=rows.slice().reverse()}
 ST.innerHTML=t;SS.innerHTML=s;SB.innerHTML=body(rows,kind==='pick');SB.scrollTop=0;
 if(S.hidden){back=document.activeElement;S.hidden=false;document.documentElement.classList.add('ptlock')}
 const h='#paper-trail/'+kind+'/'+id;if(push&&location.hash!==h){history.pushState({pt:1},'',h);pushed=true}
 requestAnimationFrame(()=>{fitT();S.querySelector('.ptsx').focus({preventScroll:true})});return true}
function hide(fromPop){if(S.hidden)return;S.hidden=true;document.documentElement.classList.remove('ptlock');
 if(!fromPop){if(pushed&&history.state&&history.state.pt){history.back()}else history.replaceState(null,'','#paper-trail')}pushed=false;
 if(back&&back.focus)back.focus({preventScroll:true})}
function fitT(){const n=ST.querySelector('.ptsn');if(!n)return;n.style.fontSize='';let s=parseFloat(getComputedStyle(n).fontSize);while(ST.scrollWidth>ST.clientWidth+.5&&s>17){s-=.5;n.style.fontSize=s+'px'}}
document.addEventListener('click',ev=>{const b=ev.target.closest&&ev.target.closest('[data-k],[data-p]');
 if(b&&(X.contains(b)||S.contains(b))){if(b.classList.contains('ptb'))return;ev.preventDefault();b.dataset.k?show('pick',b.dataset.k,true):show('player',b.dataset.p,true)}});
S.querySelector('.ptsx').addEventListener('click',()=>hide(false));
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&!S.hidden){ev.preventDefault();hide(false)}});
function route(){const m=/^#paper-trail\/(pick|player)\/([^/]+)$/i.exec(location.hash||'');if(m){if(!show(m[1].toLowerCase(),decodeURIComponent(m[2]),false))hide(true)}else hide(true)}
addEventListener('popstate',route);addEventListener('hashchange',route);
// players list
const L=X.querySelector('.ptlist'),Q=X.querySelector('.ptq'),MORE=X.querySelector('.ptmore');
const last={};for(const id in D.H){const h=D.H[id];if(h.length)last[id]=h[h.length-1]}
const ORD=Object.keys(last).sort((a,b)=>last[b][1]<last[a][1]?-1:last[b][1]>last[a][1]?1:0);
const lastTxt=r=>{const[y,d,k,a,b]=r,t=(k==='D'||k==='CD')?b:a;return esc({T:'Traded to',W:'Claimed by',A:'Added by',CA:'Added by',D:'Dropped by',CD:'Removed from',R:'Drafted by'}[k]||'')+' '+av(t)+'<span class="ptln">'+esc(t>=0?T[t]:'')+'</span>'};
const lastTxt0=r=>{const[y,d,k,a,b]=r,t=(k==='D'||k==='CD')?b:a;return ({T:'Traded to',W:'Claimed by',A:'Added by',CA:'Added by',D:'Dropped by',CD:'Removed from',R:'Drafted by'}[k]||'')+' '+(t>=0?T[t]:'')};
function rowP(id){const p=D.P[id],h=D.H[id],r=h[h.length-1],d=r[1],m=+d.slice(5,7);
 return '<button type="button" class="ptk ptkp" data-p="'+esc(id)+'"><i class="ptn'+(PC[p[1]]?'':' ptn0')+'" style="--pc:'+(PC[p[1]]||'var(--row-divider)')+'"><b>'+h.length+'</b><span>'+esc(p[1]||'–')+'</span></i>'
  +'<span class="ptm"><span class="ptl1"><b class="ptt" data-f="'+esc(p[0])+'">'+esc(p[0])+'</b>'+nfl(p[2])+'</span><span class="ptl2 ptd" title="'+esc(lastTxt0(r))+'">'+lastTxt(r)+'</span></span>'
  +'<span class="ptdt ptdl"><i>'+MO[m-1]+' '+(+d.slice(8,10))+'</i><b>'+d.slice(0,4)+'</b></span>'
  +'<span class="ptg">'+(p[3]>=0?av(p[3]):'<i class="ptfa0">FA</i>')+'</span></button>'}
function draw(){const q=(Q.value||'').trim().toLowerCase();const ids=q?ORD.filter(id=>D.P[id][0].toLowerCase().includes(q)):ORD;
 L.innerHTML=ids.slice(0,50).map(rowP).join('')||'<p class="ptnone">No player found.</p>';
 MORE.textContent=ids.length>50?'Showing 50 of '+ids.length+(q?' matches':' players')+' · search to find any player':'';fitN()}
function fitN(){if(!X.offsetParent)return;L.querySelectorAll('.ptl2').forEach(b=>{b.style.fontSize='';b.classList.remove('ptlo');let s=parseFloat(getComputedStyle(b).fontSize);while(b.scrollWidth>b.clientWidth+.5&&s>11.5){s-=.25;b.style.fontSize=s+'px'}if(b.scrollWidth>b.clientWidth+.5){b.style.fontSize='';b.classList.add('ptlo')}});L.querySelectorAll('.ptt').forEach(b=>{b.style.fontSize='';const w=b.parentElement;
  const o=()=>w.scrollWidth>w.clientWidth+.5||b.scrollWidth>b.clientWidth+.5;let s=parseFloat(getComputedStyle(b).fontSize);while(o()&&s>13){s-=.5;b.style.fontSize=s+'px'}});
 ptxFit();nameFit();holdFit();slotFit();ptxFit();
 // the name size sets the TRADED tile, the tile the column, the column the room: re-check line 1 after ptxFit and step down
 {const Y=[...X.querySelectorAll('.ptv-k .ptyx')].find(y=>y.offsetParent);for(let i=0;Y&&i<12;i++){const s=parseFloat(Y.style.getPropertyValue('--ptnf'))||15;
  if(s<=15||![...Y.querySelectorAll('.ptl1')].some(l=>l.scrollWidth>l.clientWidth+.5))break;Y.style.setProperty('--ptnf',(s-.25)+'px');holdFit();slotFit();ptxFit()}}
 pjFit();
}
// Shared ink helpers: one canvas (_ic); text measured at 50x its size because canvas rounds bounding boxes to whole
// pixels; uppercase and letter-spacing aware; vertical ink from a zero-size .ptbl marker on the text's baseline.
const _ic=document.createElement('canvas').getContext('2d');
function tInk(el){let t=el.textContent;if(!t)return null;const c=getComputedStyle(el),z=el.currentCSSZoom||1,k=z/50;if(c.textTransform==='uppercase')t=t.toUpperCase();
 const ls=(parseFloat(c.letterSpacing)||0)*z;_ic.font=c.fontStyle+' '+c.fontWeight+' '+(parseFloat(c.fontSize)*50)+'px '+c.fontFamily;
 const r=document.createRange();r.selectNodeContents(el);const b=r.getBoundingClientRect(),f=_ic.measureText(t[0]),l=_ic.measureText(t.slice(-1)),w=t.length>1?_ic.measureText(t.slice(0,-1)).width*k+ls*(t.length-1):0;
 return [b.left-f.actualBoundingBoxLeft*k,b.left+w+l.actualBoundingBoxRight*k]}
function yInk(el,base,t){const c=getComputedStyle(el),k=(el.currentCSSZoom||1)/50;_ic.font=c.fontStyle+' '+c.fontWeight+' '+(parseFloat(c.fontSize)*50)+'px '+c.fontFamily;
 const m=_ic.measureText(t||el.textContent);return [base-m.actualBoundingBoxAscent*k,base+m.actualBoundingBoxDescent*k]}
const _bl=el=>{const m=el.querySelector('.ptbl');return m?m.getBoundingClientRect().top:null};
// nameFit (2026-11-06), Picks: one holder-name size per year view (--ptnf on .ptyx-YYYY, also the pick number and the
// "–"): the largest size in 0.25px steps, 15-17px, at which every full holder name fits line 1 beside its 28px logo; under
// 15 the size stays 15 and holdFit gives the row its approved short form. Widths scale linearly with the size.
function nameFit(){const Y=[...X.querySelectorAll('.ptv-k .ptyx')].find(y=>y.offsetParent);if(!Y)return;Y.style.setProperty('--ptnf','15px');
 const N=[...Y.querySelectorAll('.ptt')];N.forEach(b=>{b.style.fontSize='';b.style.whiteSpace='';if(b.dataset.full){b.firstChild.nodeValue=b.dataset.full;delete b.dataset.full}});
 let s=17;N.forEach(b=>{const l=b.parentElement,a=l.querySelector('.pav'),cs=getComputedStyle(l),room=l.clientWidth-(a?a.getBoundingClientRect().width/(b.currentCSSZoom||1)+parseFloat(cs.columnGap||cs.gap||0):0),
  r=document.createRange();r.selectNodeContents(b.firstChild);const w=r.getBoundingClientRect().width/(b.currentCSSZoom||1);if(w>0)s=Math.min(s,Math.floor(15*room/w*4)/4)});
 s=Math.max(15,s);Y.style.setProperty('--ptnf',s+'px');
 // linear scaling can be a pixel off (kerning, rounding): step down while any full name still overflows
 const ov=()=>N.some(b=>{const l=b.parentElement;return l.scrollWidth>l.clientWidth+.5});while(s>15&&ov()){s-=.25;Y.style.setProperty('--ptnf',s+'px')}}
// holdFit, Picks line 1 (holder): full size; if it does not fit, the team's approved short form (data-ab, from PSN in
// pos/build_pos.py: "Rev. Apache Master"); then, below 423 CSS px only, a shrink to 13px (never below).
function holdFit(){X.querySelectorAll('.ptv-k .ptt').forEach(b=>{if(!b.offsetParent)return;b.style.fontSize='';b.style.whiteSpace='';if(b.dataset.full){b.firstChild.nodeValue=b.dataset.full;delete b.dataset.full}
  const w=b.parentElement,o=()=>w.scrollWidth>w.clientWidth+.5;if(o()&&b.dataset.ab){b.dataset.full=b.firstChild.nodeValue;b.firstChild.nodeValue=b.dataset.ab}
  if(innerWidth<423){let s=parseFloat(getComputedStyle(b).fontSize);while(o()&&s>13){s-=.5;b.style.fontSize=s+'px'}}})}  // 13px shrink only below 423 CSS px (Nicklaus 2026-11-06)
// slotFit (2026-11-06), NFL slot on a drafted row's line 2, per row: full size -> generation suffix dropped (Jr., Sr., II-V)
// -> the approved abbreviation (LUA, the lineup list in new_tail.js: the matching surname word, on the suffix-less name) ->
// slot hidden (the pick sheet and aria-label keep it; expected only below 423 CSS px).
// Fits when >= 12px separate the NFL logo's box (its ink lies inside) from the slot's first glyph ink once the slot's
// last glyph sits on the name column's right edge. Names that would need an unapproved form go to window.__ptForm.
function slotFit(){const A=typeof LUA!=='undefined'?LUA:{};window.__ptForm=window.__ptForm||[];
 const N=[...X.querySelectorAll('.ptv-k .ptns')].filter(n=>n.closest('.ptp').offsetParent);
 N.forEach(n=>{n.classList.remove('pthide');const p=n.parentElement.querySelector('.ptpn');if(p.dataset.full){p.firstChild.nodeValue=p.dataset.full;delete p.dataset.full}});
 const gap=n=>{const L=n.parentElement,its=[...n.querySelectorAll('i:not(.ptbl)')],a=tInk(its[0]),b=tInk(its[its.length-1]),d=L.querySelector('.nfl')||L.querySelector('.ptpn'),z=n.currentCSSZoom||1;
  return a&&b?((L.getBoundingClientRect().right-(b[1]-a[0]))-d.getBoundingClientRect().right)/z:99};
 const G=N.map(gap);
 N.forEach((n,i)=>{if(G[i]>=12)return;const p=n.parentElement.querySelector('.ptpn'),full=p.firstChild.nodeValue,set=t=>{p.dataset.full=full;p.firstChild.nodeValue=t;return gap(n)>=12};
  let w=full.split(' ');const sx=w.length>2&&/^(Jr\.?|Sr\.?|II|III|IV|V)$/.test(w[w.length-1]);if(sx){w=w.slice(0,-1);if(set(w.join(' ')))return}  // generation suffix dropped
  const j=w.findIndex(x=>A[x]);if(j>=0){w[j]=A[w[j]];if(set(w.join(' ')))return}                                         // approved abbreviation
  if(p.dataset.full){p.firstChild.nodeValue=full;delete p.dataset.full}
  if(innerWidth>=423&&window.__ptForm.indexOf(full)<0)window.__ptForm.push(full);
  n.classList.add('pthide')})}
// ptxFit (2026-11-06), Picks right-hand stack: VIA banner (Drafts' .dfvia, original team's coach) over the trade count.
// Column (--ptxa, set on .ptv-k) = the widest of the TRADED header ink, the banners and the counts in the shown year; the
// banners' boxes and the counts' "×" ink end on the 16px inset; the header label's ink too. Reads, then writes.
function ptxFit(){const V=X.querySelector('.ptv-k');if(!V||!V.offsetParent)return;const P=[...V.querySelectorAll('.ptp')].filter(p=>p.offsetParent);if(!P.length)return;
 const cnt=[],heads=[],slots=[],bans=[];P.forEach(p=>{p.querySelectorAll('.ptxn').forEach(t=>cnt.push(t));p.querySelectorAll('.pthx').forEach(h=>heads.push(h));p.querySelectorAll('.ptns').forEach(n=>slots.push(n));p.querySelectorAll('.ptvb:not(.ptv0)').forEach(b=>bans.push(b))});
 cnt.forEach(t=>t.style.transform='');heads.forEach(h=>h.style.transform='');slots.forEach(n=>n.style.transform='');
 const z=(P[0].querySelector('.ptt')||P[0]).currentCSSZoom||1,ci=t=>{const a=tInk(t.querySelector('b')),b=tInk(t.querySelector('small'));return a&&b?[a[0],b[1]]:null};
 const w=Math.max(0,...heads.map(h=>{const i=tInk(h);return i?(i[1]-i[0])/z:0}),...bans.map(b=>b.getBoundingClientRect().width/z),...cnt.map(t=>{const i=ci(t);return i?(i[1]-i[0])/z:0}));
 V.style.setProperty('--ptxa',Math.ceil(w)+'px');
 const W=[];
 cnt.forEach(t=>{const C=t.parentElement.getBoundingClientRect(),i=ci(t);if(i)W.push([t,'translateX('+((C.right-i[1])/z).toFixed(3)+'px)'])});
 heads.forEach(h=>{const x=tInk(h),C=h.getBoundingClientRect();if(x)W.push([h,'translateX('+((C.right-x[1])/z).toFixed(3)+'px)'])});
 // NFL slot: last glyph's ink on the name column's right edge, baseline on the player name's baseline
 slots.forEach(n=>{const L=n.parentElement,C=L.getBoundingClientRect(),pb=_bl(L.querySelector('.ptpn')),sb=_bl(n),its=[...n.querySelectorAll('i:not(.ptbl)')],x=tInk(its[its.length-1]);
  if(pb==null||sb==null||!x)return;W.push([n,'translate('+((C.right-x[1])/z).toFixed(3)+'px,'+((pb-sb)/z).toFixed(3)+'px)'])});
 W.forEach(([el,v])=>el.style.transform=v)}
// pjFit: a future pick's number ("1.01") centred in its tile by glyph ink, not by advance box (the "1" bearings)
function pjFit(){const B=[...X.querySelectorAll('.ptv-k .ptpj b')].filter(b=>b.offsetParent);B.forEach(b=>b.style.transform='');
 const D=B.map(b=>{const i=tInk(b),t=b.parentElement.getBoundingClientRect(),z=b.currentCSSZoom||1;return i?((t.right-i[1])-(i[0]-t.left))/2/z:0});
 B.forEach((b,i)=>{if(Math.abs(D[i])>.01)b.style.transform='translateX('+D[i].toFixed(3)+'px)'})}
Q&&Q.addEventListener('input',draw);draw();
X.querySelectorAll('.ptb').forEach(b=>b.addEventListener('click',()=>{X.querySelectorAll('.ptb').forEach(x=>{const on=x===b;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on)});
 X.querySelectorAll('.ptv').forEach(v=>v.hidden=!v.classList.contains('ptv-'+b.dataset.v));fitN()}));
document.addEventListener('change',()=>requestAnimationFrame(fitN));addEventListener('resize',()=>requestAnimationFrame(()=>{fitN();if(!S.hidden)fitT()}));document.fonts&&document.fonts.ready.then(()=>{fitN();route()});
route();
})</script>'''
SEC=''.join(out)+f'<script>window.PT={_js};</script>'+JS
yrs_css=''.join(f'#pty-{y}:checked~.ptyx-{y}{{display:block}}@media(min-width:1100px){{#pty-{y}:checked~.ptyx-{y}{{display:grid}}}}#pty-{y}:checked~.ptyb label[for="pty-{y}"] b{{background:var(--chalk);color:var(--ink)}}#pty-{y}:checked~.ptyb label[for="pty-{y}"] small{{color:var(--steel)}}' for y in sorted({v[0] for v in K.values()}))
CSS=('#tab-pt:checked~.tnav .tsub label[for="tab-pt"]{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}.ptx{--ptg:44px}'
 '.ptx .pav,.pts .pav{display:block;flex:none;border-radius:50%;background-color:var(--deck-2);background-position:center;background-size:cover;background-repeat:no-repeat}.ptx .pav.nl,.pts .pav.nl{visibility:hidden}'
 +('.ptx .pav.av,.pts .pav.av{box-shadow:0 0 0 1px var(--line-strong),1px 1px 0 .5px rgba(0,0,0,.4),1px 1px 3px .5px rgba(0,0,0,.25)!important}' if PICKS else '')+  # BBP logos: the Stats tab's halved ring + shadow; YILM faces stay bare

 '.ptx .posh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}.ptx .wsub{font-size:12.5px;color:var(--steel)}'
 # Picks / Players switch: The Wire's position pill (same font, padding, shadow), two equal halves
 '.ptsw{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:4px 0 14px}'
 '.ptb{font:700 13px/1 var(--display);letter-spacing:.06em;text-transform:uppercase;padding:10px 12px 9px;border-radius:9px;border:1px solid var(--frame);background:var(--deck);color:var(--label);box-shadow:var(--sh-hard);cursor:pointer}'
 '.ptb.on{background:var(--chalk);color:var(--ink)}'
 '.ptv[hidden]{display:none!important}.ptyx{display:none}'
 '@media(min-width:1100px){.ptsw{max-width:420px}.ptyx .ptp{margin:0}#pty-0:checked{}'
 '.ptv-k .ptyx{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 16px;align-items:start}.ptv-p{max-width:760px}}'

 '.ptyb{margin:0 0 14px auto}.ptyb .yb{cursor:pointer}'
 '@media(max-width:759px){.ptyb{grid-auto-flow:row;grid-template-columns:repeat(4,minmax(0,1fr));width:100%}}'
 '.ptq{display:block;width:100%;box-sizing:border-box;margin:0 0 14px}'
 # panel and rows: four-step depth (frame, divider, panel, lighter row), 16px inset
 '.ptp{background:var(--deck);border:2px solid var(--frame);border-radius:var(--r-panel);box-shadow:var(--sh-hard);overflow:hidden;margin:0 0 14px}'
 '.pthd{display:grid;grid-template-columns:52px minmax(0,1fr) var(--ptxa,64px);column-gap:12px;align-items:center;padding:10px 0 9px;font:700 12px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim);background:var(--deck)}'
 '.pthd>span:first-child{text-align:center}.pthd>span:last-child{text-align:center}'
 '.ptpl .pthd{grid-template-columns:52px minmax(0,1fr) 46px var(--ptg)}.ptpl .pthd>span:nth-child(3){text-align:right}'
 '.ptk{all:unset;box-sizing:border-box;display:grid;grid-template-columns:52px minmax(0,1fr) var(--ptxa,64px);column-gap:12px;align-items:stretch;width:100%;min-height:52px;cursor:pointer;'
 'border-top:1px solid var(--row-divider);background:var(--deck)}'
 '.ptp .ptk:nth-of-type(odd){background:var(--row-lt)}'
 '.ptlist .ptk:nth-child(odd){background:var(--row-lt)}.ptlist .ptk:nth-child(even){background:var(--deck)}'
 '.ptkp{grid-template-columns:52px minmax(0,1fr) 46px var(--ptg)}'
 '.ptk:focus-visible{outline:2px solid var(--chalk);outline-offset:-2px}'
 '.ptn{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;background:var(--pc);color:var(--ink);font-style:normal}'
 '.ptn b{font:700 15px/1 var(--display);text-box:trim-both cap alphabetic}.ptn span{font:700 10px/1 var(--display);letter-spacing:.06em;text-box:trim-both cap alphabetic}'
 '.ptn0{background:var(--row-divider);color:var(--chalk)}'
 '.ptm{min-width:0;display:flex;flex-direction:column;justify-content:center;gap:5px;padding:9px 0}'
 '.ptl1{display:flex;align-items:center;gap:8px;min-width:0;white-space:nowrap}'
 '.ptl1 .pav{width:22px;height:22px}.ptv-k .ptl1 .pav{width:28px;height:28px}.ptv-k .ptt{font-size:var(--ptnf,15px)}.ptv-k .ptn b{font-size:var(--ptnf,15px)}'
 '.ptt{font:600 15px/1.15 var(--body);color:var(--chalk);min-width:0}'
 '.ptl2{display:flex;align-items:center;gap:6px;min-width:0;font:400 12.5px/1.25 var(--body);color:var(--chalk)}.ptl2.ptd,.ptd{color:var(--text-dim)}'
 '@media(max-width:380px){.ptx{--ptg:40px}.pthd,.ptk{grid-template-columns:44px minmax(0,1fr) var(--ptxa,64px);column-gap:8px}.ptpl .pthd,.ptkp{grid-template-columns:44px minmax(0,1fr) 40px var(--ptg)}.ptpl .pthd>span:first-child{font-size:11px;letter-spacing:.06em}}'
 # Picks view (2026-11-06): no GM column (line 1 names the holder), 16px right inset; "via" + 18px logo + original team on line 2
 '.ptv-k .pthd,.ptv-k .ptk{padding-right:16px}.ptv-k .pthd>span:nth-child(2){text-align:left}.ptv-k .pthd>.pthx{text-align:right}.ptv-k .ptl2>*{flex:none}'
 # Picks rows (2026-11-06): tile | holder (+ player line on drafted rows) | TRADED tile | VIA logo; rows: flexible top/bottom
 # tracks (>= 9px) around line 1 (and line 2), min 52px, so one-line rows centre and the tile spans the full height
 '.ptv-k .ptk{grid-template-rows:minmax(13px,1fr) auto auto minmax(13px,1fr);row-gap:0;min-height:57px}.ptv-k .ptl2{min-height:20px}'  # 57: >= 10px above the VIA banner and below the count; line 2 as tall as an NFL badge on every row
 '.ptv-k .ptn{grid-column:1;grid-row:1/-1}.ptv-k .ptm{display:contents}'
 '.ptv-k .ptl1{grid-column:2;grid-row:2}.ptv-k .ptl2{grid-column:2;grid-row:3;margin-top:5px}'
 # right-hand stack (2026-11-06): VIA banner over the trade count, right-aligned to the 16px inset, centred in the row
 '.ptxc{grid-column:3;grid-row:1/-1;display:flex;flex-direction:column;align-items:flex-end;justify-content:center;gap:4px;min-width:0}'
 '.ptx .ptvb{font-size:11px!important;padding:3px 6px 2px}.ptvb.ptv0{visibility:hidden}'
 '.ptxn{display:block;font:700 22px/1 var(--display);font-variant-numeric:tabular-nums;color:var(--chalk);font-style:normal;white-space:nowrap;text-box:trim-both cap alphabetic}'
 '.ptxn b{font-weight:700}.ptxn small{font:700 13px/1 var(--display);color:var(--text-dim)}.ptxn.z b{color:var(--steel)}'
 # NFL draft slot (2026-11-06): Drafts' slot type on one line, right edge of the name column (ink-aligned by ptxFit), >= 12px clear of the logo
 '.ptns.pthide{display:none}.ptns{margin-left:auto;padding-left:6px;display:block;font:600 11px/1 var(--display);letter-spacing:.04em;text-transform:uppercase;font-variant-numeric:tabular-nums;color:var(--text-dim);white-space:nowrap}.ptns i{font-style:normal}.ptns i+i:not(.ptbl){margin-left:6px}'  # inline, not flex: the .ptbl marker must sit on the baseline
 '.ptbl{display:inline-block;width:0;height:0;vertical-align:baseline}'
 '.ptpn{min-width:0}.ptl2{white-space:nowrap}.ptl2 .pav{width:18px;height:18px}.ptl2.ptlo .ptln{display:none}'
 '.ptc{margin-left:auto;flex:none;font:700 12px/1 var(--display);letter-spacing:.04em;color:var(--text-dim);font-style:normal;padding-right:2px}'
 '.ptg{display:flex;align-items:center;justify-content:center;border-left:3px solid var(--pg)}'
 '.ptg .pav{width:28px;height:28px}'
 '.ptfa0{font:700 12px/1 var(--display);letter-spacing:.06em;color:var(--text-dim);font-style:normal}'
 '.ptdt{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-style:normal}'
 '.ptdt i{font:600 11px/1 var(--display);letter-spacing:.06em;text-transform:uppercase;color:var(--text-dim);font-style:normal;text-box:trim-both cap alphabetic}'
 '.ptdt b{font:700 17px/1 var(--display);color:var(--chalk);text-box:trim-both cap alphabetic}'
 '.ptdl{align-items:flex-end}.ptdl b{font-size:12px;color:var(--text-dim);font-weight:600;letter-spacing:.06em}.ptdl i{color:var(--chalk);font-size:12px}'
 '.ptmore{margin:-4px 0 14px;font-size:12px;color:var(--steel)}.ptmore:empty{display:none}'
 '.ptnone{margin:0;padding:16px;color:var(--text-dim);font-size:13px}'
 # the sheet: full-height panel on phones, side panel on desktop
 'html.ptlock,html.ptlock body{overflow:hidden}'
 '.pts{position:fixed;inset:0;z-index:1000;display:flex;flex-direction:column;background:var(--deck);color:var(--chalk)}.pts[hidden]{display:none}'
 '@media(min-width:1100px){.pts{left:auto;width:460px;border-left:2px solid var(--frame);box-shadow:var(--sh-hard)}html.ptlock,html.ptlock body{overflow:auto}}'
 '.ptsh{display:grid;grid-template-columns:minmax(0,1fr) 40px;column-gap:12px;align-items:start;padding:16px 16px 14px;background:var(--deck);border-bottom:2px solid var(--frame)}'
 '.ptsi{min-width:0;grid-column:1;grid-row:1}.ptsx{grid-column:2;grid-row:1}'
 '.ptsx{all:unset;box-sizing:border-box;width:40px;height:40px;display:flex;align-items:center;justify-content:center;border-radius:9px;background:var(--row-lt);color:var(--chalk);border:1px solid var(--frame);box-shadow:var(--sh-hard);cursor:pointer}'
 '.ptsx:focus-visible{outline:2px solid var(--chalk);outline-offset:2px}'
 '.ptst{margin:0;display:flex;align-items:center;gap:8px;min-width:0;white-space:nowrap;font:700 26px/1.1 var(--display);letter-spacing:.02em;text-transform:uppercase;color:var(--chalk)}'
 '.ptss{display:flex;flex-direction:column;gap:6px;margin-top:8px}'
 '.ptsl{display:flex;align-items:center;gap:8px;font:400 14px/1.2 var(--body);color:var(--chalk)}.ptsl .pav{width:24px;height:24px}.ptsl b{font-weight:600}'
 '.ptsm{font:400 12.5px/1.35 var(--body);color:var(--text-dim)}'
 '.ptsb{flex:1 1 auto;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;padding-bottom:max(16px,env(safe-area-inset-bottom))}'
 '.ptsy{display:flex;justify-content:space-between;align-items:center;padding:10px 16px 9px;font:700 12px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim);background:var(--pg)}'
 '.pte{display:grid;grid-template-columns:32px 28px minmax(0,1fr);column-gap:12px;align-items:center;padding:12px 16px;border-top:1px solid var(--row-divider);background:var(--deck)}'
 '.ptsy+.pte{border-top:0}.pte:nth-child(odd){background:var(--row-lt)}'
 '.pte .pav{width:28px;height:28px}.pte .ptfa{visibility:hidden}'
 '.ptx1{min-width:0;display:flex;flex-direction:column;gap:5px}'
 '.pta{font:400 14px/1.25 var(--body);color:var(--chalk)}.pta b{font-weight:600}'
 '.ptb2{font:400 12.5px/1.35 var(--body);color:var(--text-dim)}'
 '.ptr{all:unset;cursor:pointer;color:var(--chalk);text-decoration:underline;text-decoration-color:var(--text-dim);text-underline-offset:2px}'
 '.ptr:focus-visible{outline:2px solid var(--chalk);outline-offset:1px}.ptr0{color:var(--chalk)}'
 '.ptsm .ptr{font-weight:600}'
 '.ptx .nfl,.pts .nfl{flex:none}'
 +yrs_css)
if __name__=='__main__':
    open(P+'paper_section.html','w',encoding='utf-8').write(SEC)
    open(P+'paper_css.css','w',encoding='utf-8').write(CSS)
