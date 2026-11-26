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
def sides(moves,m,ref,tix):
    """Trade step as headed columns, one per team that got something (2026-11-24, brief PT-1e): [[team idx, items], ...];
    first the receiving team (m[3], the old "Traded to"), then the From team (m[2]; kept in a two-team trade even when it
    got nothing: "Nothing"), then any other team that got something, in order of first appearance. Items: players, then
    picks (year, round), then FAAB. moves = (kind, id, from, to). In a trade of three or more teams every item is
    [ref, source team idx] (-1 = the data names no source: left untagged); in a two-team trade a plain ref."""
    to,frm=m[3],m[2];o={'player':0,'pick':1,'faab':2}
    tm=[]
    for mm in moves:
        for t in (mm[3],mm[2]):
            if t is not None and t not in tm:tm.append(t)
    multi=len(tm)>2
    order=[to]+([frm] if frm is not None and frm!=to else [])+[mm[3] for mm in moves]
    cols=[];seen=set()
    for t in order:
        if t is None or t in seen:continue
        seen.add(t);r=[]
        for mm in sorted((mm for mm in moves if mm[3]==t),key=lambda mm:(o.get(mm[0],3),str(ref(mm)) if mm[0]=='pick' else '')):
            x=ref(mm)
            if x:r.append([x,tix(mm[2]) if mm[2] is not None else -1] if multi else x)
        if r or (not multi and t in (to,frm)):cols.append([tix(t),r])
    return cols

if _dt_os.path.exists(P+'history/paper/sleeper_2025.json'):
    # ------------------------------------------------------------------ BBP: MFL + Sleeper, picks and players
    PICKS=True
    sys.path.insert(0,P+'history')
    import paper_audit as A
    try:  # approved short team names (DESIGN.md §2.16), single source: PSN in pos/build_pos.py
        import ast;PSN=ast.literal_eval(re.search(r'^PSN=(\{.*?\})',open(P+'pos/build_pos.py',encoding='utf-8').read(),re.M).group(1))
    except Exception:PSN={}
    # short team names for pick labels in the sheet's trade columns only (approved by Nicklaus 2026-11-11): the pipeline's
    # own SH map in full_update.py (roster id -> short name), read as a literal like PSN above (single source; never
    # retyped). Emitted once as PT.N (team name -> short form, only where it differs). PSN / data-ab are not touched.
    try:_SH=ast.literal_eval(re.search(r'^SH=(\{.*?\})',open(P+'full_update.py',encoding='utf-8').read(),re.M).group(1))
    except Exception:_SH={}
    TSH={A.ST[int(k)]:v for k,v in _SH.items() if int(k) in A.ST and v and v!=A.ST[int(k)]}
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
                H[sid].append([y,d,'T',ti(m[3]),ti(m[2]),sides(ev['moves'],m,ref,ti)])
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
                    rows.append([ev['season'],d,'T',ti(m[3]),ti(m[2]),sides(ev['moves'],m,ref,ti)]);own=m[3]
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
            # every asset of the trade as (kind, id, from roster, to roster): players, FAAB, and draft picks (plain text 'x' refs:
            # a redraft league has no pick sheets; none traded so far)
            mv=[('player',s2,drops.get(s2),r2) for s2,r2 in adds.items()]
            mv+=[('pick',f'{dp["season"]} R{dp["round"]} ({RN_(dp["roster_id"])})',dp['previous_owner_id'],dp['owner_id']) for dp in t.get('draft_picks') or []]
            mv+=[('faab',w['amount'],w['sender'],w['receiver']) for w in t.get('waiver_budget') or []]
            rf=lambda mm:'p'+mm[1] if mm[0]=='player' else ('x'+mm[1] if mm[0]=='pick' else f'${mm[1]:g}')
            for mm in mv:
                if mm[0]=='player':pinfo(mm[1])
            for m in mv:
                if m[0]!='player':continue
                sid,frm,rid=m[1],m[2],m[3]
                H[sid].append([y,d,'T',ti(RN_(rid)),ti(RN_(frm)) if frm else -1,sides(mv,m,rf,lambda r:ti(RN_(r)) if r else -1)])
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
# column-head short forms of the sheet's trade step (heads only: not PSN, not items, not holder names), approved by Nicklaus
# 2026-11-24: "Rev. Apache Master" is PSN's approved form (DESIGN.md 2.16), "Chop Wood" new. Tried before any shrink.
HSF={'Reverse Apache Master':'Rev. Apache Master','Chop Wood, Carry Water':'Chop Wood'}
PT=dict(T=T,S={str(k):v for k,v in SRC.items()},P=PL,H=H,K=K,C=C,Z={t:slug(t) for t in T},N={t:v for t,v in (TSH if PICKS else {}).items() if t in TI},HS={t:v for t,v in HSF.items() if t in TI})
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
                # row (2026-11-06, bar pass): tile | holder (drafted: player on line 2) | TRADED count "n×" | VIA bar (flush
                # top-right, traded picks only). .ptbl = zero-size marker on the name's baseline (NFL slot alignment).
                hab=(' data-ab="'+e(PSN[T[own]])+'" title="'+e(T[own])+'"') if PSN.get(T[own]) else ''
                if lab:
                    pl=PL.get(sid) or ['?','','',-1]
                    tile=f'<i class="ptn{"" if pl[1] in PC else " ptn0"}" style="--pc:{PC.get(pl[1],"var(--row-divider)")}"><b>{lab}</b><span>{e(pl[1])}</span></i>'
                    ns=DB.nflslot(pl[0],pl[1],yy) if DB else None
                    if ns=='UDFA':nsh,nsa='<span class="ptns" title="Undrafted free agent"><i>UDFA</i><i class="ptbl"></i></span>',', NFL undrafted free agent'
                    elif ns:nsh,nsa=f'<span class="ptns" title="NFL draft {ns[0]}: round {ns[1]}, pick {ns[2]} overall"><i>RD {ns[1]}</i><i>PK {ns[2]}</i><i class="ptbl"></i></span>',f', NFL round {ns[1]}, pick {ns[2]}'
                    else:nsh,nsa='<span class="ptns"><i>–</i><i class="ptbl"></i></span>',''
                    nsa=f', drafted {e(pl[0])}'+nsa
                    # drafted row (2026-11-26, PS-3): the PLAYER is the headline (line 1, .ptt + his NFL logo), the team the meta line
                    # (line 2, .ptpn + NFL slot). Classes are positional: .ptt = the line-1 name, .ptpn = the line-2 name.
                    tnm=f'<span class="ptpn"{hab}>{e(T[own])}<i class="ptbl"></i></span>'
                    hl=f'<b class="ptt" title="{e(pl[0])}">{e(pl[0])}<i class="ptbl"></i></b>{badge(pl[2]) if pl[2] else ""}'
                    sub=f'<span class="ptl2">{tnm}{nsh}</span>'
                else:
                    tile=f'<i class="ptn ptn0 ptpj"><b>{pj or "R"+str(rr)}</b></i>'
                    sub='';nsa='';hl=f'<b class="ptt"{hab}>{e(T[own])}<i class="ptbl"></i></b>'
                via=own!=o
                # via (2026-11-25, PS-2b): a quiet "via <coach>" (draft_build.own) under the tile, only when the holder is not the
                # original team. TIMES TRADED: the count in a light tile for counts >= 1 (real count, incl. picks traded away and back).
                coach=(DB.own(T[o]) if DB else T[o])
                vc=(f'<small class="ptvt"><i>via</i> {e(coach)}<i class="ptbl"></i></small>' if via else '')
                num=(f'pick {lab}' if lab else f'projected pick {pj}' if pj else f'round {rr}')
                ttl=(' title="via '+e(T[o])+'"') if via else ''
                rows.append(f'<button type="button" class="ptk{"" if lab else " ptk1"}" data-k="{k}"{ttl} aria-label="{y} round {rr}, {num}, {e(T[own])}, traded {n} time{"" if n==1 else "s"}{(", via "+e(T[o])) if via else ""}{nsa}, history">{tile}'
                            f'<span class="ptm"><span class="ptl1">{av(T[own])}{hl}</span>{sub}</span>'
                            f'{f"<i class=ptxn><b>{n}<i class=ptbl></i></b></i>" if n else ""}{vc}</button>')
            mix={bool(K[k][4]) for k in rk};ytr=any(C[k] and sum(1 for x in C[k] if x[2] in('T','M')) for k in ks)   # any traded pick in this year view (none: no TIMES / TRADED label)
            if len(mix)>1:print(f'WARNING paper: {y} R{r} mixes drafted and future picks',file=sys.stderr)
            out.append(f'<div class="ptp"><div class="pthd"><span>R{r}</span>{'<span class="pthp">Player<i class="pthn" aria-hidden="true">NFL</i></span>' if all(K[k][4] for k in rk) else '<span>Team</span>'}<span class="pthx{'' if ytr else ' pthx0'}"{'' if ytr else ' aria-hidden="true"'}><i>Times</i><i>Traded</i></span></div>{"".join(rows)}</div>')
        out.append('</div>')
    out.append('</div>')
out.append(f'<div class="ptv ptv-p"{" hidden" if PICKS else ""}><input class="wq ptq" type="search" placeholder="Search player…" aria-label="Search player" autocomplete="off">'
           '<div class="ptp ptpl"><div class="pthd"><span>Moves</span><span>Player · last move</span><span>Date</span><span>GM</span></div><div class="ptlist"></div></div>'
           '<p class="ptmore"></p></div>')
out.append('<div class="key"><div>'+('<b>Picks</b> each row names the team that holds or used the pick. TIMES TRADED counts the times the pick changed hands; VIA shows the original team\'s logo and coach when another team holds the pick. '
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
// Trade step (2026-11-24, brief PT-1e; Nicklaus chose V2): no "Traded to" / "From" lines; the row's logo slot holds the
// swap badge (.ptswb, Stats › Trades' .txsw: one component); one headed column per team that got something (sides() in
// the build: [[team, items], ...]; left = the receiving team, right = the From team, any further team under the shorter
// of the two, placed by tPlace()). Head = 18px logo / face (none when the team has no picture) + team name; a 1px rule
// under it, 6px of ink above and below (gapFit); items = what THAT team got, no +/- marks. Items: a ref, or
// [ref, source team] in trades of three or more teams ("from Z" under it; -1 = source unknown, untagged). me = the open
// sheet's own ref: bold, not a link. Pick = "2029 R1 " + "(original team)" (.pttot never breaks inside; data-ab = the SH
// short team name, PT.N). trFit() picks the item forms, hdFit() the head forms and sizes.
const HSF=D.HS||{};  // column-head short forms (heads only), PT.HS from the build
const SWP='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 5.5h9.5M10 3l2.5 2.5L10 8M13 10.5H3.5M6 8l-2.5 2.5L6 13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';  // Stats › Trades swap glyph (sx_build.py SWP), repeated
function titem(q,me){const r=typeof q==='string'?q:q[0],o=typeof q==='string'?-1:q[1],c=r[0],v=r.slice(1);let h='';
 if(c==='p'){const p=D.P[v],n=esc(p?p[0]:v);h=r===me?'<b class="pttme" data-n="'+n+'">'+n+'</b>':'<button type="button" class="ptr" data-p="'+esc(v)+'" data-n="'+n+'">'+n+'</button>'}
 else if(c==='k'){const kv=D.K[v],tn=kv?T[kv[2]]:'',ab=tn&&D.N&&D.N[tn],n=kv?kv[0]+' R'+kv[1]+' <span class="pttot"'+(ab?' data-ab="('+esc(ab)+')" data-f="('+esc(tn)+')"':'')+'>('+esc(tn)+')</span>':esc(v);
  h=r===me?'<b class="pttme">'+n+'</b>':'<button type="button" class="ptr" data-k="'+esc(v)+'"'+(kv?' aria-label="'+esc(KN(v))+'"':'')+'>'+n+'</button>'}
 else if(c==='$')h='<span class="ptr0">$'+esc(v)+' FAAB</span>';
 else if(c==='x'){const m=/^(.*?) (\(.*\))$/.exec(v);h='<span class="ptr0">'+(m?esc(m[1])+' <span class="pttot">'+esc(m[2])+'</span>':esc(v))+'</span>'}
 return '<span class="ptti"><span class="pttx">'+h+(o>=0?'<small class="pttcp">from '+esc(T[o])+'</small>':'')+'</span></span>'}
function thead(i){const n=i>=0?T[i]:'',r=typeof AVR!=='undefined'?AVR[n]:null;
 return '<span class="ptth">'+(r?'<i class="pav av av-'+r+'" aria-hidden="true"></i>':'')+'<b class="ptthn" data-f="'+esc(n)+'"'+(HSF[n]?' data-ab="'+esc(HSF[n])+'"':'')+'>'+esc(n)+'</b></span>'}
function tcols(cols,me){cols=cols||[];const col=(c,k)=>'<span class="pttc'+(k>1?' pttc3':'')+'" role="group" aria-label="'+esc(c[0]>=0?T[c[0]]:'')+' received">'+thead(c[0])
  +'<span class="pttl">'+(c[1].length?c[1].map(q=>titem(q,me)).join(''):'<span class="ptti pttno"><span class="pttx">Nothing</span></span>')+'</span></span>';
 return '<span class="pttr"><span class="pttw">'+(cols[0]?col(cols[0],0):'')+cols.slice(2).map((c,k)=>col(c,k+2)).join('')+'</span><span class="pttw">'+(cols[1]?col(cols[1],1):'')+'</span></span>'}
function tcount(cols){const s=new Set();(cols||[]).forEach(c=>{s.add(c[0]);c[1].forEach(q=>{if(typeof q!=='string'&&q[1]>=0)s.add(q[1])})});return s.size}
function line(r,isPick,me){const[y,d,k,a,b,x,w]=r,ta=a>=0?T[a]:'',tb=b>=0?T[b]:'';let l1='',l2='',l3='',who=a;
 if(k==='T'){const m=r[1],n=tcount(x),mm=+m.slice(5,7),dd=+m.slice(8,10),multi=(x||[]).some(c=>c[1].some(q=>typeof q!=='string'));
  return '<div class="pte ptet'+(multi?' ptet3':'')+'"><span class="ptdt"><i>'+MO[mm-1]+'</i><b>'+dd+'</b></span>'+'<i class="ptswb" role="img" aria-label="Trade">'+SWP+'</i>'
   +'<span class="ptxt">'+(multi?'<span class="ptt3">'+n+'-team trade</span>':'')+tcols(x,me)+'</span></div>'}
 // move-type hooks (2026-11-24, briefs PT-2 .. PT-2d): waiver claims and free-agent adds only (Nicklaus 20:57 ET: "the only adds become
 // attention drawing"). Those rows carry .ptk-w / .ptk-a and a type tile i.ptkr in a fourth grid column; the tile says the type, so
 // line 2 drops the word; a waiver row is one line (PT-2f): its bid "$N" (span.ptkf, value only; title / aria-label "$N FAAB") sits in
 // its own track left of the tile, on line 1's baseline (kSnap). A free-agent add has no line 2. Every other row is today's markup and text. Emitted
 // only where the page's stylesheet defines the move tokens (KH): elsewhere today's markup, byte for byte (a span boundary splits the
 // text run and Chromium then moves every later glyph of the line by 1/64px, which changed Classic's anti-aliasing). Line 1's team may
 // carry data-ab (PT.HS) for l1Fit (KH only).
 const KL={w:'Waiver',a:'Free agent'};let kk='',am='';
 const bt=n=>KH&&HSF[n]?'<b data-f="'+esc(n)+'" data-ab="'+esc(HSF[n])+'">'+esc(n)+'</b>':'<b>'+esc(n)+'</b>';
 if(k==='W'){kk=KH?'w':'';l1='Claimed by '+bt(ta);l2=KH?'':'Waivers'+(x[0]?' · $'+esc(x[0])+' FAAB':'');
  if(KH&&x[0])am='<span class="ptkf" data-d="'+String(x[0]).slice(-1)+'" title="$'+esc(x[0])+' FAAB" aria-label="$'+esc(x[0])+' FAAB"><b>$'+esc(x[0])+'</b></span>'}
 else if(k==='A'){kk=KH?'a':'';l1='Added by '+bt(ta);l2=KH?'':'Free agent'}
 else if(k==='CA'){l1='Added by '+bt(ta);l2='Commissioner'}
 else if(k==='D'){l1='Dropped by '+bt(tb);who=b}
 else if(k==='CD'){l1='Removed from '+bt(tb);l2='Commissioner';who=b}
 else if(k==='R'){l1='Drafted by '+bt(ta);l2=(dk[x[1]]||'Draft')+' · '+esc(x[0])+(x[2]&&D.K[x[2]]&&D.K[x[2]][2]!==a?' · '+refh('k'+x[2]):'')}
 else if(k==='U'){l1='Used by '+bt(ta);l2=esc(x[0])+' · '+refh('p'+x[1])}
 else if(k==='M'){l1='Moved to '+bt(ta);l2='From '+esc(tb)+' · commissioner, no trade logged'}
 const m=+d.slice(5,7),dd=+d.slice(8,10),tile=kk?'<i class="ptkr ptkt-'+kk+'">'+KL[kk]+'</i>':'';
 return '<div class="pte'+(kk?' ptk-'+kk:'')+'"><span class="ptdt"><i>'+MO[m-1]+'</i><b>'+dd+'</b></span>'+av(who)+'<span class="ptx1"><span class="pta">'+l1+'</span>'
   +(l2?'<span class="ptb2">'+l2+'</span>':'')+'</span>'+l3+am+tile+'</div>'}
function body(rows,isPick,me){let h='',cur=null;
 for(const r of rows){const y=r[0];if(y!==cur){cur=y;h+='<div class="ptsy"><span>'+y+'</span><span>'+esc(D.S[y]==='MFL'?'MyFantasyLeague':'Sleeper')+'</span></div>'}h+=line(r,isPick,me)}
 return h||'<p class="ptnone">No moves yet.</p>'}
// per-type counts for the header summary (briefs PT-2 .. PT-2e; KH only): own line under the summary, plain text in its style, order
// of frequency (ties in KT order), plurals; none for a sheet with one move. Items are joined by a space (the break opportunity); each
// item is one unbreakable .ptkn whose "· " is its own ::before (a box of --ptsep = the dot + a space); the items' wrapper .ptkw sits
// --ptsep to the left inside .ptkc (overflow hidden), so on every line the first item's dot is cut off and the space before it is the
// one the line break eats: no line starts or ends with a dot. The block balances its lines. data-d = the item's first glyph (its
// count's first digit), data-e = its last glyph (brief PT-2g): the site CSS moves each dot inside its box by the two glyphs' side
// bearings (from the font outlines), so the ink gap before the dot equals the gap after it.
const KT=[['A','free agent','free agents'],['D','drop','drops'],['W','waiver','waivers'],['T','trade','trades'],['R','draft','drafts'],['C','commissioner move','commissioner moves']];
function kcount(rows){if(!KH||rows.length<2)return '';const n={};rows.forEach(r=>{const k=/^(CA|CD|M)$/.test(r[2])?'C':r[2];n[k]=(n[k]||0)+1});
 const L=KT.filter(t=>n[t[0]]).sort((a,b)=>n[b[0]]-n[a[0]]);if(!L.length)return '';
 return '<span class="ptkc"><span class="ptkw">'+L.map(t=>{const w=n[t[0]]===1?t[1]:t[2];return '<span class="ptkn" data-d="'+String(n[t[0]])[0]+'" data-e="'+w.slice(-1)+'">'+n[t[0]]+' '+w.replace(/ /g,' ')+'</span>'}).join(' ')+'</span></span>'}
// move-type hooks on wherever the page's stylesheet defines the move tokens (retro theme.css, YILM readability.css); BBP Classic
// does not, and keeps today's markup (see line())
const KH=getComputedStyle(document.documentElement).getPropertyValue('--mv-w').trim()!=='';
const S=document.querySelector('.pts'),ST=S.querySelector('.ptst'),SS=S.querySelector('.ptss'),SB=S.querySelector('.ptsb');let back=null,pushed=false;
function show(kind,id,push){let t='',s='',rows=[];
 if(kind==='player'){const p=D.P[id];if(!p)return false;rows=D.H[id]||[];
   t='<span class="ptsn">'+esc(p[0])+'</span>'+nfl(p[2]);
   s='<span class="ptsl">'+(p[1]?'<i class="pz p-'+esc(p[1].toLowerCase())+'">'+esc(p[1])+'</i>':'')+(p[3]>=0?av(p[3])+'<span>On <b>'+esc(T[p[3]])+'</b></span>':'<span>Not on a roster</span>')+'</span>'
     +'<span class="ptsm">'+rows.length+' move'+(rows.length===1?'':'s')+(rows.length?' since '+rows[0][1].slice(0,4):'')+kcount(rows)+'</span>';
   rows=rows.slice().reverse()}
 else{const v=D.K[id];if(!v)return false;rows=D.C[id]||[];
   t='<span class="ptsn">'+v[0]+' · Round '+v[1]+'</span>';
   s='<span class="ptsl">'+av(v[2])+'<span><b>'+esc(T[v[2]])+'</b>’s pick</span></span>'
     +'<span class="ptsm">'+(!v[4]&&v[6]?'Projected '+esc(v[6])+' · ':'')+(v[4]?'Pick '+esc(v[4])+' · used by '+esc(T[v[3]])+' · '+refh('p'+v[5]):(v[3]===v[2]?'Not traded · ':'')+'Owned by '+esc(T[v[3]]))+'</span>';
   rows=rows.slice().reverse()}
 ST.innerHTML=t;SS.innerHTML=s;SB.innerHTML=body(rows,kind==='pick',(kind==='pick'?'k':'p')+id);SB.scrollTop=0;
 if(S.hidden){back=document.activeElement;S.hidden=false;document.documentElement.classList.add('ptlock')}
 trFit();
 const h='#paper-trail/'+kind+'/'+id;if(push&&location.hash!==h){history.pushState({pt:1},'',h);pushed=true}
 requestAnimationFrame(()=>{fitT();trFit();S.querySelector('.ptsx').focus({preventScroll:true})});return true}
function hide(fromPop){if(S.hidden)return;S.hidden=true;document.documentElement.classList.remove('ptlock');
 if(!fromPop){if(pushed&&history.state&&history.state.pt){history.back()}else history.replaceState(null,'','#paper-trail')}pushed=false;
 if(back&&back.focus)back.focus({preventScroll:true})}
// trFit (2026-11-10), trade columns of the open sheet, per item: one line at full form -> approved short form (pick:
// the team's SH short name from full_update.py, PT.N; player: generation suffix dropped, then the LUA abbreviation, as
// slotFit) -> the item wraps inside its own column under its text (the mark column gives the hanging indent; a pick
// breaks before its "(team)": the full name again when that fits the column on its own line, else the short one, which
// itself wraps only if it is wider than the column). Never shrinks, clips or ellipsises. Reads, then writes.
function trFit(){if(S.hidden)return;l1Fit();trFit0();hdFit();tPlace();gapFit();kSnap()}
// kSnap (2026-11-24, briefs PT-2c / PT-2e; KH only): the move-type tiles (i.ptkr) sit with their centre on line 1's cap centre (as the
// Picks TIMES TRADED tile sits on the holder name's cap centre), on the device-pixel grid. The tile is laid out centred in its row; on
// a two-line row (waiver + "$N FAAB") that is between the lines. Line 1's baseline is read from a zero-size marker put at its start
// (an inline formatting context: .pta is a block), its cap centre = baseline - cap height / 2 (--ptcap, IBM Plex Sans .698em, Martian
// Mono at size-adjust .875 .70em); the tile's top = cap centre - half its height, rounded to the nearest device pixel (1 / dpr CSS px;
// the row's text is not on the grid, CSS cannot see where a box meets it), written as a relative `top` (moves nothing else). Runs last
// in trFit (after every show() and on resize) and when the fonts are ready. The waiver bid (.ptkf, PT-2f) takes line 1's baseline the
// same way (a relative `top`; 0 on a one-line row, where both are centred in the row). Clears, reads all, then writes.
function kSnap(){if(!KH||S.hidden)return;const l=[...SB.querySelectorAll('.ptkr')];if(!l.length)return;const u=1/(window.devicePixelRatio||1);
 const cap=parseFloat(getComputedStyle(S).getPropertyValue('--ptcap'))||.698;
 l.forEach(t=>t.style.top='');const mk=l.map(t=>{const a=t.parentElement.querySelector('.pta'),i=document.createElement('i');i.style.cssText='display:inline-block;width:0;height:0;margin:0;padding:0;border:0;vertical-align:baseline';a.insertBefore(i,a.firstChild);return [a,i]});
 const d=l.map((t,k)=>{const[a,i]=mk[k],r=t.getBoundingClientRect(),c=i.getBoundingClientRect().bottom-cap*parseFloat(getComputedStyle(a).fontSize)/2;return Math.round((c-r.height/2)/u)*u-r.top});
 const F=[...SB.querySelectorAll('.ptkf')];F.forEach(f=>f.style.top='');const fm=F.map(f=>{const i=document.createElement('i');i.style.cssText='display:inline-block;width:0;height:0;margin:0;padding:0;border:0;vertical-align:baseline';f.firstChild.appendChild(i);
  const a=f.parentElement.querySelector('.pta'),j=document.createElement('i');j.style.cssText=i.style.cssText;a.insertBefore(j,a.firstChild);return [i,j]});
 const fd=fm.map(([i,j])=>j.getBoundingClientRect().bottom-i.getBoundingClientRect().bottom);
 mk.forEach(m=>m[1].remove());fm.forEach(([i,j])=>{i.remove();j.remove()});l.forEach((t,i)=>{if(Math.abs(d[i])>.001)t.style.top=d[i].toFixed(4)+'px'});
 F.forEach((f,i)=>{if(Math.abs(fd[i])>.001)f.style.top=fd[i].toFixed(4)+'px'})}
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(()=>{if(!S.hidden)kSnap()});
// l1Fit (2026-11-24, briefs PT-2b .. PT-2d; KH only): a line 1 that would wrap takes its team's approved head short form (PT.HS);
// still too long: it wraps as before. Reads, then writes.
function l1Fit(){const L=[...SB.querySelectorAll('.pta b[data-ab]')];if(!L.length)return;L.forEach(b=>{b.textContent=b.dataset.f;b.removeAttribute('title')});
 const one=b=>{const a=b.parentElement,lh=parseFloat(getComputedStyle(a).lineHeight);return a.getBoundingClientRect().height<lh*1.5};
 const O=L.filter(b=>!one(b));O.forEach(b=>{b.textContent=b.dataset.ab;b.title=b.dataset.f})}
function trFit0(){const A=typeof LUA!=='undefined'?LUA:{},N=[...SB.querySelectorAll('.pttx')];if(!N.length)return;
 N.forEach(n=>{n.classList.remove('pttwr','pttwr2');const o=n.querySelector('.pttot[data-f]');if(o)o.textContent=o.dataset.f;const p=n.querySelector('[data-n]');if(p){p.textContent=p.dataset.n;p.removeAttribute('title')}});
 const ov=n=>{const e=n.firstElementChild;return e?e.getBoundingClientRect().width>n.getBoundingClientRect().width+.05:false};
 const O=N.filter(ov);
 O.forEach(n=>{const o=n.querySelector('.pttot[data-ab]'),p=n.querySelector('[data-n]');
  if(o){o.textContent=o.dataset.ab;if(!ov(n))return}
  if(p){const full=p.dataset.n;let w=full.split(' ');const set=t=>{p.textContent=t;p.title=full;return !ov(n)};
   const sx=w.length>2&&/^(Jr\.?|Sr\.?|II|III|IV|V)$/.test(w[w.length-1]);if(sx){w=w.slice(0,-1);if(set(w.join(' ')))return}
   const j=w.findIndex(x=>A[x]);if(j>=0){w[j]=A[w[j]];if(set(w.join(' ')))return}
   p.textContent=full;p.removeAttribute('title')}
  n.classList.add('pttwr');const q=n.querySelector('.pttot'),wd=()=>q.getBoundingClientRect().width>n.getBoundingClientRect().width+.05;
  if(q&&q.dataset.f){q.textContent=q.dataset.f;if(wd())q.textContent=q.dataset.ab}
  if(q&&wd())n.classList.add('pttwr2')})}
// hdFit (2026-11-24): column heads, per head: full name at 12.5px -> the approved head short form (HSF = PT.HS) at 12.5px
// -> shrink in 0.25px steps to 11px (the text floor). Never ellipsised: a head that still does not fit at 11px overflows.
function hdFit(){const Hs=[...SB.querySelectorAll('.ptthn')];if(!Hs.length)return;
 Hs.forEach(h=>{h.style.fontSize='';h.textContent=h.dataset.f;h.removeAttribute('title')});
 const ov=h=>{const r=document.createRange();r.selectNodeContents(h);return r.getBoundingClientRect().right>h.parentElement.getBoundingClientRect().right+.05};
 const O=Hs.filter(ov);
 O.forEach(h=>{if(h.dataset.ab){h.textContent=h.dataset.ab;h.title=h.dataset.f;if(!ov(h))return}let s=parseFloat(getComputedStyle(h).fontSize)||12.5;while(ov(h)&&s>11){s-=.25;h.style.fontSize=s+'px'}})}
// gapFit (2026-11-24): the 1px rule under each column head sits 6px of ink under the head (its picture's lowest ink:
// the box + --ptak, the ring and hard shadow below it; with no picture, the name's lowest glyph) and 6px of ink over the
// column's first item (its highest glyph). Glyph ink from the fonts' own outlines (GT: [top, bottom] per character in
// thousandths of an em above / below the baseline; IBM Plex Sans 400 / 600, and Martian Mono 400 / 600 at wdth 75 with the
// retro face's 87.5% size-adjust), baselines from zero-size markers; padding-bottom of the head and margin-top of the
// item list by layout, no transforms. Reads everything, then writes.
const GT=(()=>{const o={},R={"P400":["!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~’‘“”–—éèáíóúñçÉ·…",[698,-12,740,460,698,0,780,-82,710,-12,710,-12,740,460,760,-137,760,-137,747,388,548,62,117,-133,347,261,117,-12,740,-151,710,-12,698,0,710,0,710,-12,698,0,698,-12,698,-12,698,0,710,-12,710,0,528,-12,528,-133,566,-12,440,172,566,-12,710,-12,708,-121,698,0,698,0,710,-12,698,0,698,0,698,0,710,-12,698,0,698,0,698,-12,698,0,698,0,698,0,698,0,710,-12,698,0,710,-164,698,0,710,-12,698,0,698,-12,698,0,698,0,698,0,698,0,698,0,760,-138,740,-151,760,-138,698,296,-95,-165,779,585,528,-12,740,-12,528,-12,740,-12,528,-12,740,0,586,-212,740,0,740,0,740,-200,740,0,740,0,528,0,528,0,528,-12,528,-200,528,-200,516,0,528,-12,659,0,516,-12,516,0,516,0,516,0,516,-200,516,0,760,-138,760,-138,760,-138,374,236,750,500,740,490,740,490,750,500,342,266,342,266,779,-12,779,-12,779,-12,779,0,779,-12,779,-12,728,0,528,-207,949,0,369,240,117,-12]],"P600":["!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~’‘“”–—éèáíóúñçÉ·…",[698,-12,740,428,698,0,780,-82,710,-12,710,-12,740,428,760,-138,760,-138,747,282,549,63,154,-143,368,241,154,-11,740,-151,710,-12,698,0,710,0,710,-12,698,0,698,-12,698,-12,698,0,710,-12,710,0,534,-11,534,-143,593,-5,468,142,593,-5,710,-12,709,-121,698,0,698,0,710,-12,698,0,698,0,698,0,710,-12,698,0,698,0,698,-11,698,0,698,0,698,0,698,0,710,-12,698,0,710,-178,698,0,710,-12,698,0,698,-12,698,0,698,0,698,0,698,0,698,0,760,-138,740,-151,760,-138,698,283,-75,-183,805,581,534,-12,740,-12,534,-12,740,-12,534,-12,740,0,614,-212,740,0,746,0,746,-200,740,0,740,0,534,0,534,0,534,-12,534,-200,534,-200,522,0,534,-12,665,0,522,-12,522,0,522,0,522,0,522,-200,522,0,760,-138,760,-138,760,-138,392,219,750,465,740,455,740,455,750,465,358,250,358,250,805,-12,805,-12,805,-12,805,0,805,-12,805,-12,744,0,534,-211,969,0,386,221,154,-11]],"M400":["!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~’‘“”–—éèáíóúñçÉ·…",[700,-6,742,401,700,0,788,-88,714,-14,714,-14,742,401,805,-140,805,-140,508,103,516,96,166,-158,350,262,166,-7,742,-149,714,-14,700,0,714,0,714,-14,700,0,700,-14,700,-14,700,0,714,-14,714,0,532,-7,532,-158,552,60,464,149,552,60,714,-6,714,-189,700,0,700,0,714,-14,700,0,700,0,700,0,714,-10,700,0,700,0,700,-14,700,0,700,0,700,0,700,0,714,-14,700,0,714,-189,700,0,714,-14,700,0,700,-14,700,0,700,0,700,0,700,0,700,0,788,-122,742,-149,788,-122,714,472,-44,-131,742,500,539,-12,742,-14,539,-14,742,-14,539,-14,756,0,539,-189,742,0,749,0,749,-189,742,0,742,0,539,0,539,0,539,-14,539,-175,539,-175,539,0,539,-14,662,-14,525,-14,525,0,525,0,525,0,525,-189,525,0,798,-133,752,-52,798,-133,398,214,756,432,742,418,742,418,756,432,350,262,350,262,735,-14,735,-14,735,-12,735,0,735,-14,735,-14,733,0,539,-189,910,0,436,262,166,-7]],"M600":["!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~’‘“”–—éèáíóúñçÉ·…",[700,-7,742,384,700,0,788,-88,716,-16,716,-14,742,384,830,-166,830,-166,522,86,533,79,203,-162,363,250,203,-9,742,-149,716,-16,700,0,716,0,716,-16,700,0,700,-16,700,-16,700,0,716,-16,716,0,542,-9,542,-162,567,46,476,136,567,46,716,-7,716,-182,700,0,700,0,716,-16,700,0,700,0,700,0,716,-12,700,0,700,0,700,-16,700,0,700,0,700,0,700,0,716,-16,700,0,716,-191,700,0,716,-16,700,0,700,-16,700,0,700,0,700,0,700,0,700,0,806,-141,742,-149,806,-141,716,466,-44,-157,742,472,549,-12,742,-14,549,-16,742,-14,549,-16,758,0,548,-191,742,0,769,0,769,-191,742,0,742,0,549,0,549,0,549,-16,548,-175,548,-175,548,0,549,-16,672,-16,534,-16,534,0,534,0,534,0,534,-191,534,0,823,-158,752,-52,823,-158,409,203,758,393,742,377,742,377,758,393,360,252,360,252,747,-16,747,-16,747,-12,747,0,747,-16,747,-16,744,0,549,-191,913,0,455,244,203,-9]]};for(const k in R){const[c,v]=R[k],m={};[...c].forEach((ch,i)=>m[ch]=[v[2*i]/1000,v[2*i+1]/1000]);o[k]=m}return o})();
const gTab=el=>{const c=getComputedStyle(el);return GT[(/Martian/.test(c.fontFamily)?'M':'P')+(+c.fontWeight>=550?600:400)]};
function gInk(t,tab){let a=0,b=0;for(const ch of t){const g=tab[ch];if(g){if(g[0]>a)a=g[0];if(g[1]<b)b=g[1]}else if(ch.trim())a=Math.max(a,.83)}return [a,b]}
function gapFit(){const C=[...SB.querySelectorAll('.pttc')];if(!C.length)return;
 const Q=C.map(c=>{const h=c.querySelector('.ptth'),l=c.querySelector('.pttl'),x=l.querySelector('.pttx'),f=x.firstElementChild,t=f&&!f.classList.contains('pttcp')?f:x,m=document.createElement('i');
  m.style.cssText='display:inline-block;width:0;height:0;vertical-align:baseline';x.insertBefore(m,x.firstChild);h.style.paddingBottom='';l.style.marginTop='';return {h,l,t,m}});
 const R=Q.map(q=>{const h=q.h,n=h.querySelector('.ptthn'),a=h.querySelector('.pav'),z=h.currentCSSZoom||1,cs=getComputedStyle(h),fn=parseFloat(getComputedStyle(n).fontSize),ft=parseFloat(getComputedStyle(q.t).fontSize),
  hb=h.getBoundingClientRect().bottom/z,nb=n.getBoundingClientRect().bottom/z,mb=q.m.getBoundingClientRect().top/z,
  lo=a?a.getBoundingClientRect().bottom/z+(parseFloat(cs.getPropertyValue('--ptak'))||0):nb-gInk(n.textContent,gTab(n))[1]*fn,
  hi=mb-gInk((q.t.textContent||'').replace(/\s+/g,' ').trim(),gTab(q.t))[0]*ft;
  return {pb:parseFloat(cs.paddingBottom),mt:parseFloat(getComputedStyle(q.l).marginTop),rt:hb-1,lo,hi,b:mb}});
 Q.forEach(q=>q.m.remove());
 // the rule's top and the first item's baseline land on device pixels (the engines paint borders and text baselines there)
 const px=window.devicePixelRatio||1,sn=v=>Math.round(v*px)/px;
 Q.forEach((q,i)=>{const r=R[i],dp=sn(r.lo+6)-r.rt,rb=r.rt+dp+1,b=r.hi+dp+(r.b-r.hi),db=sn(rb+6+(r.b-r.hi))-b;
  q.h.style.paddingBottom=(r.pb+dp).toFixed(3)+'px';q.l.style.marginTop=(r.mt+db).toFixed(3)+'px'})}
// tPlace (2026-11-24): a third (fourth ...) team's column goes under the shorter of the first two (tie = left)
function tPlace(){SB.querySelectorAll('.pttr').forEach(R=>{const X3=[...R.querySelectorAll('.pttc3')];if(!X3.length)return;const W=R.querySelectorAll(':scope>.pttw');
 X3.forEach(c=>c.remove());X3.forEach(c=>{const a=W[0].getBoundingClientRect().height,b=W[1].getBoundingClientRect().height;(b<a?W[1]:W[0]).appendChild(c)})})}
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
  if(s<=15||![...Y.querySelectorAll('.ptl1')].some(l1Over))break;Y.style.setProperty('--ptnf',(s-.25)+'px');holdFit();slotFit();ptxFit()}}
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
// nameFit (2026-11-06; PS-3 2026-11-26), Picks: one line-1 size per year view (--ptnf on .ptyx-YYYY, also the pick number and
// the "–"): the largest size in 0.25px steps, 15-17px, at which every full line-1 name fits (drafted years: the PLAYER + his NFL
// logo; future years: the team beside its 36px logo); under 15 the size stays 15 and holdFit gives the row its approved short
// form. Widths scale linearly with the size.
function nameFit(){const Y=[...X.querySelectorAll('.ptv-k .ptyx')].find(y=>y.offsetParent);if(!Y)return;Y.style.setProperty('--ptnf','15px');
 const N=[...Y.querySelectorAll('.ptt')];N.forEach(b=>{b.style.fontSize='';b.style.whiteSpace='';if(b.dataset.full){b.firstChild.nodeValue=b.dataset.full;delete b.dataset.full}});
 // PS-3: the room is line 1's content box less its other in-flow items (future rows: the 36px logo; drafted rows: the NFL logo, the
 // holder logo standing outside the flow) and their gaps, and less any column gap under 12px (the .ptgt lever), so line 1 keeps
 // >= 12px before the right column
 let s=17;N.forEach(b=>{const l=b.parentElement,z=b.currentCSSZoom||1,cs=getComputedStyle(l),g=parseFloat(cs.columnGap||cs.gap)||0,cg=parseFloat(getComputedStyle(l.closest('.ptk')).columnGap)||12,
  it=[...l.children].filter(c=>c!==b&&!c.classList.contains('ptbl')&&getComputedStyle(c).position!=='absolute'),
  room=l.clientWidth-(parseFloat(cs.paddingLeft)||0)-(parseFloat(cs.paddingRight)||0)-it.reduce((v,c)=>v+c.getBoundingClientRect().width/z+g,0)-Math.max(0,12-cg),
  r=document.createRange();r.selectNodeContents(b.firstChild);const w=r.getBoundingClientRect().width/z;if(w>0)s=Math.min(s,Math.floor(15*room/w*4)/4)});
 s=Math.max(15,s);Y.style.setProperty('--ptnf',s+'px');
 // linear scaling can be a pixel off (kerning, rounding): step down while any full name still overflows
 const ov=()=>N.some(b=>l1Over(b.parentElement));while(s>15&&ov()){s-=.25;Y.style.setProperty('--ptnf',s+'px')}}
// line 1 overflows when its content (a Range) runs past its box, or (column gap under 12px) into the 12px before the right column
function l1Over(l){const cg=parseFloat(getComputedStyle(l.closest('.ptk')).columnGap)||12,z=l.currentCSSZoom||1,r=document.createRange();r.selectNodeContents(l);   // by content (a Range), not scrollWidth (DESIGN.md 7)
 return (r.getBoundingClientRect().right-(l.getBoundingClientRect().right-(parseFloat(getComputedStyle(l).paddingRight)||0)*z))/z>.05-Math.max(0,12-cg)}
// holdFit, Picks line 1. Future rows (the team is the headline): full size; if it does not fit, the team's approved short form
// (data-ab, from PSN in pos/build_pos.py: "Rev. Apache Master"); then, below 423 CSS px only, a shrink to 12px, then 11px.
// Drafted rows (PS-3: the player is the headline), only where the name + NFL logo still overflow at 15px: generation suffix
// dropped (Jr., Sr., II-V) -> approved LUA short form (new_tail.js) -> listed in window.__ptForm ("needs an unapproved form",
// left at the best approved form; window.__ptOver = [name, px past the room]). Never shrunk, never hidden.
function holdFit(){window.__ptForm=window.__ptForm||[];window.__ptOver=[];const A=typeof LUA!=='undefined'?LUA:{};
 X.querySelectorAll('.ptv-k .ptt').forEach(b=>{if(!b.offsetParent)return;b.style.fontSize='';b.style.whiteSpace='';if(b.dataset.full){b.firstChild.nodeValue=b.dataset.full;delete b.dataset.full}
  const w=b.parentElement,o=()=>l1Over(w);
  if(!b.closest('.ptk1')){if(!o())return;const full=b.firstChild.nodeValue,set=t=>{b.dataset.full=full;b.firstChild.nodeValue=t;return !o()};let q=full.split(' ');
   if(q.length>2&&/^(Jr\.?|Sr\.?|II|III|IV|V)$/.test(q[q.length-1])){q=q.slice(0,-1);if(set(q.join(' ')))return}
   const j=q.findIndex(x=>A[x]);if(j>=0){q[j]=A[q[j]];if(set(q.join(' ')))return}
   if(window.__ptForm.indexOf(full)<0)window.__ptForm.push(full);window.__ptOver.push([full,b.firstChild.nodeValue,+((w.scrollWidth-w.clientWidth)/1).toFixed(2)]);return}
  if(o()&&b.dataset.ab){b.dataset.full=b.firstChild.nodeValue;b.firstChild.nodeValue=b.dataset.ab}
  if(innerWidth<423){let s=parseFloat(getComputedStyle(b).fontSize);while(o()&&s>12){s-=.5;b.style.fontSize=s+'px'}while(o()&&s>11){s-=.5;b.style.fontSize=s+'px'}}})}  // shrink only below 423 CSS px: to 12px, then to 11px (the text floor) only if 12px still overflows (Nicklaus 2026-11-07; was 13px)
// slotFit: resets the slot form, the tighter-gap lever and line 2's team forms, then slotForm (below) decides them again.
function slotFit(){window.__ptForm=window.__ptForm||[];const V=X.querySelector('.ptv-k');
 if(V){V.classList.remove('ptn1','ptn11','ptgt');V.style.removeProperty('--ptnw');V.style.removeProperty('--ptpk')}  // the normal gaps first
 X.querySelectorAll('.ptv-k .ptns').forEach(n=>{const p=n.parentElement.querySelector('.ptpn');p.style.fontSize='';if(p.dataset.full){p.firstChild.nodeValue=p.dataset.full;delete p.dataset.full}});
 rowFit(1);slotForm()}
// Retro only (html.retro): engines that lay glyphs out on whole pixels (WebKitGTK) get each advance's rounding (probe, as
// theme.js adv()) added, so the widest PK ink still ends on the edge.
const SGX={b:{"R":[.054,.438],"D":[.054,.426],"P":[.053,.432],"K":[.054,.46],"U":[.05,.428],"F":[.054,.402],"A":[.01347,.442],"0":[.046,.429],"1":[.066,.343],"2":[.048,.437],"3":[.044,.418],"4":[.023,.453],"5":[.057,.431],"6":[.05598,.431],"7":[.046,.432],"8":[.052,.423],"9":[.039,.417],"–":[.027,.351]},
 m:{"R":[.06195,.5072],"D":[.053,.49175],"P":[.07075,.49845],"K":[.0815,.49785],"U":[.04775,.47725],"F":[.097,.481],"A":[.0279,.4971],"0":[.03325,.49175],"1":[.07475,.48525],"2":[.05512,.46988],"3":[.05075,.47425],"4":[.03535,.50005],"5":[.0504,.4738],"6":[.04905,.47595],"7":[.06635,.45865],"8":[.04945,.47555],"9":[.04905,.47595],"–":[.03987,.48513]}},
 SGA={"R":.461,"D":.472,"P":.457,"K":.477,"U":.478,"F":.415,"A":.456," ":.2,"–":.377},SGK={"UD":-.009,"DF":-.004,"FA":-.036},_rnd={};
// text style of an element: outline table, size in viewport px, letter / word spacing, Martian?, per-advance rounding (retro)
function sSt(e){const c=getComputedStyle(e),m=/Martian/.test(c.fontFamily),z=e.currentCSSZoom||1,fs=parseFloat(c.fontSize),f=fs*z;let d=0;
 if(document.documentElement.classList.contains('retro')){const k=c.fontWeight+' '+fs+' '+m;if(_rnd[k]==null){const p=document.createElement('span');
  p.style.cssText='position:absolute;left:-999px;top:0;visibility:hidden;white-space:nowrap;letter-spacing:0;word-spacing:0;font:'+c.fontWeight+' '+fs+'px/1 '+c.fontFamily;p.style.fontVariantNumeric='tabular-nums';p.style.setProperty('letter-spacing','0','important');p.style.setProperty('word-spacing','0','important');
  p.textContent='0000000000';document.body.appendChild(p);const r=p.getBoundingClientRect().width/10-(m?.525:.475)*fs;p.remove();_rnd[k]=Math.abs(r)>=.02&&Math.abs(r)<1?r:0}d=_rnd[k]*z}
 return {T:SGX[m?'m':'b'],m,f,ls:(parseFloat(c.letterSpacing)||0)*z,ws:(parseFloat(c.wordSpacing)||0)*z,d}}
// [ink start, ink end, advance end] of a string from its origin, by the outline tables
function sInk(s,S){let x=0,l=null,r=0;for(let i=0;i<s.length;i++){const c=s[i],g=S.T[c];if(c!==' '){if(l==null)l=x+(g?g[0]*S.f:0);r=x+(g?g[1]*S.f:.5*S.f)}
  x+=(S.m?.525:/\d/.test(c)?.475:(SGA[c]||.5))*S.f+S.ls+S.d+(c===' '?S.ws:0)+(!S.m&&i+1<s.length?(SGK[c+s[i+1]]||0)*S.f:0)}return [l||0,r,x]}
// canvas width of a text in an element's font (main's tInk): [advance of all but the last glyph + spacing, first glyph's left ink, last glyph's right ink]
function cW(e,t){const c=getComputedStyle(e),k=(e.currentCSSZoom||1)/50,ls=(parseFloat(c.letterSpacing)||0)*(e.currentCSSZoom||1);if(c.textTransform==='uppercase')t=t.toUpperCase();
 _ic.font=c.fontStyle+' '+c.fontWeight+' '+(parseFloat(c.fontSize)*50)+'px '+c.fontFamily;return [_ic.measureText(t.slice(0,-1)).width*k+ls*(t.length-1),_ic.measureText(t[0]).actualBoundingBoxLeft*k,_ic.measureText(t.slice(-1)).actualBoundingBoxRight*k,_ic.measureText(t).width*k+ls*t.length+(parseFloat(c.wordSpacing)||0)*(e.currentCSSZoom||1)*(t.split(' ').length-1)]}   // [3] = laid-out advance (word spacing too); [0..2] = main's tInk, which has none
const cInk=(e,t)=>{const w=cW(e,t);return w[0]+w[1]+w[2]};
// SGMC: Martian Mono [xMin, xMax] em per glyph at wght 600 / 700 (wdth 75, x .875), from the font files
const SGMC={"600":{"A":[0.0279,0.4971],"B":[0.07275,0.49175],"C":[0.05035,0.4905],"D":[0.053,0.49175],"E":[0.08375,0.46775],"F":[0.097,0.481],"G":[0.0437,0.48555],"H":[0.053,0.472],"I":[0.053,0.472],"J":[0.04425,0.46325],"K":[0.0815,0.49785],"L":[0.11875,0.481],"M":[0.03975,0.48525],"N":[0.0503,0.4747],"O":[0.03325,0.49175],"P":[0.07075,0.49845],"Q":[0.03325,0.49175],"R":[0.06195,0.5072],"S":[0.05385,0.4837],"T":[0.03185,0.49315],"U":[0.04775,0.47725],"V":[0.0279,0.4971],"W":[0.0141,0.5109],"X":[0.03047,0.49453],"Y":[0.02045,0.50455],"Z":[0.066,0.459],"0":[0.03325,0.49175],"1":[0.07475,0.48525],"2":[0.05512,0.46988],"3":[0.05075,0.47425],"4":[0.03535,0.50005],"5":[0.0504,0.4738],"6":[0.04905,0.47595],"7":[0.06635,0.45865],"8":[0.04945,0.47555],"9":[0.04905,0.47595]},"700":{"A":[0.02182,0.50318],"B":[0.06262,0.49963],"C":[0.0418,0.49725],"D":[0.044,0.49963],"E":[0.0725,0.4745],"F":[0.0835,0.4855],"G":[0.03672,0.49478],"H":[0.044,0.481],"I":[0.044,0.481],"J":[0.03525,0.47225],"K":[0.07137,0.50618],"L":[0.1075,0.4855],"M":[0.033,0.492],"N":[0.04265,0.48235],"O":[0.02537,0.49963],"P":[0.05725,0.50385],"Q":[0.02537,0.49963],"R":[0.04935,0.5126],"S":[0.0453,0.48685],"T":[0.02555,0.49945],"U":[0.03875,0.48625],"V":[0.02182,0.50318],"W":[0.0123,0.5127],"X":[0.0253,0.4997],"Y":[0.0146,0.5104],"Z":[0.05925,0.46575],"0":[0.02537,0.49963],"1":[0.068,0.492],"2":[0.04725,0.47775],"3":[0.04287,0.48213],"4":[0.02905,0.50815],"5":[0.04095,0.4819],"6":[0.04027,0.48473],"7":[0.06117,0.46383],"8":[0.04135,0.48365],"9":[0.04027,0.48473]}};
// ink width of a text in e's font, viewport px: retro Martian Mono from its outlines (SGMC), else canvas (cInk)
function inkC(e,t){const c=getComputedStyle(e);if(!(document.documentElement.classList.contains('retro')&&/Martian/.test(c.fontFamily)))return cInk(e,t);
 const g=SGMC[+c.fontWeight>=650?700:600],S=sSt(e);t=t.trim().toUpperCase();const a=g[t[0]],b=g[t[t.length-1]];if(!a||!b)return cInk(e,t);
 return (t.length-1)*(.525*S.f+S.ls+S.d)+b[1]*S.f-a[0]*S.f}
// slotForm (2026-11-25 .. 26, briefs PS-1 .. PS-3c): ONE slot form and ONE slot geometry for the whole Picks view, the same in
// every drafted year, all from text (outline tables SGX / SGA / SGK, canvas), never from the layout of hidden years; a slot is never
// hidden. Line 2 = the TEAM name (12.5px) + the slot (one line, 11px: two left-aligned fields, "RD n" --ptpk wide, the box --ptnw
// wide ending on the name column's right edge). Forms: 11px; at <= 430 CSS px also 11px + the tighter gaps (.ptgt). A form is taken
// only if every drafted row of every year keeps >= 12px of ink from its team name, in FULL at 12.5px, to the slot's first glyph.
// Then per row (from text, every year): full name -> data-ab short form at 12.5px -> shrink in 0.5px steps to 11px; rows still
// short go to window.__ptShort (name, px short). Also places the strip's "NFL" label (--pthnr).
// right bearing of glyph ch in e's font, CSS px (Martian Mono from its outlines SGMC, else canvas)
function rBear(e,ch){const c=getComputedStyle(e),f=parseFloat(c.fontSize);if(/Martian/.test(c.fontFamily)){const g=SGMC[+c.fontWeight>=650?700:600][ch];return g?(.525-g[1])*f:0}
 _ic.font=c.fontStyle+' '+c.fontWeight+' '+(f*50)+'px '+c.fontFamily;const m=_ic.measureText(ch);return (m.width-m.actualBoundingBoxRight)/50}
function teInk(e,t){const c=getComputedStyle(e),z=e.currentCSSZoom||1,k=z/50,w=cW(e,t),ls=(parseFloat(c.letterSpacing)||0)*z,l=t.slice(-1);
 _ic.font=c.fontStyle+' '+c.fontWeight+' '+(parseFloat(c.fontSize)*50)+'px '+c.fontFamily;const m=_ic.measureText(l);return w[3]-ls-(m.width-m.actualBoundingBoxRight)*k}  // ink end from the origin, viewport px, at the element's size
function slotForm(){const V=X.querySelector('.ptv-k');if(!V||!V.offsetParent)return;V.dataset.ptn='main';window.__ptShort=[];window.__ptTeam=[];
 const Yv=[...V.querySelectorAll('.ptyx')].find(y=>y.offsetParent);let L0=Yv&&[...Yv.querySelectorAll('.ptl2')].find(l=>l.querySelector('.ptns')&&l.offsetParent);if(!L0)return;
 const A=[...V.querySelectorAll('.ptyx')].filter(y=>y.querySelector('.ptns'));if(!A.length)return;const z=L0.currentCSSZoom||1,vs=V.style,NS=L0.querySelector('.ptns'),PN=L0.querySelector('.ptpn'),f0=parseFloat(getComputedStyle(PN).fontSize);
 // every drafted row: team name (full, short form) and its ink end at 12.5px (viewport px from line 2's origin)
 const R=[];A.forEach(y=>y.querySelectorAll('.ptns').forEach(n=>{const l=n.parentElement,pn=l.querySelector('.ptpn'),I=[...n.querySelectorAll('i:not(.ptbl)')].map(i=>i.textContent),
  full=pn.firstChild.nodeValue,ab=pn.dataset.ab||null;R.push({I,r:n.closest('.ptk'),pn,full,ab,ef:teInk(PN,full),ea:ab?teInk(PN,ab):null})}));
 const DB=window.__ptSlot={rows:R.length,tries:[]},q=location.search;
 let tries=[[11,0]];if(innerWidth<=430)tries.push([11,1]);let last=null;   // the slot is 11px (the via's size)
 for(const [f,g] of tries){V.classList.add('ptn1');V.classList.toggle('ptn11',f==11);V.classList.toggle('ptgt',!!g);if(g){rowFit(1);L0=[...Yv.querySelectorAll('.ptl2')].find(l=>l.querySelector('.ptns')&&l.offsetParent)}
  const S=sSt(NS),Lw=L0.getBoundingClientRect().width,x0=lxOf(L0.closest('.ptk'));
  let rd=0,pk=0,pl=null,wu=0;const off=R.map(q=>{const a=sInk(q.I[0],S);if(q.I.length==2){const b=sInk(q.I[1],S);rd=Math.max(rd,a[1]);pk=Math.max(pk,b[1]);pl=b[0]}else wu=Math.max(wu,a[1]);return a[0]});
  const pkx=pl==null?0:rd+6*z-pl,W=Math.max(pl==null?0:pkx+pk,wu),room=R.map((q,i)=>Lw-W+off[i]-(lxOf(q.r)-x0)*z),gp=R.map((q,i)=>(room[i]-q.ef)/z);   // room = the slot's first ink from line 2's origin
  {let k=0;gp.forEach((v,i)=>{if(v<gp[k])k=i});DB.tries.push([f,g,+gp[k].toFixed(3),R[k].full])}
  last=[f,g,W,pkx,room,Math.min(...off)];if(gp.every(v=>v>=12-.01))break}
 const [f,g,W,pkx,room,o0]=last;
 // the strip's "NFL" label, ink centred over the slot's ink span (first RD glyph .. widest PK ink end = the column's right edge)
 {const lb=V.querySelector('.ptyx .pthn');if(lb){const c=getComputedStyle(lb),ls=parseFloat(c.letterSpacing)||0,rb=rBear(lb,'L'),iw=inkC(lb,'NFL')/z;
  vs.setProperty('--pthnr',((W-o0)/z/2-ls-rb-iw/2).toFixed(3)+'px')}}vs.setProperty('--ptnw',(W/z).toFixed(3)+'px');vs.setProperty('--ptpk',(pkx/z).toFixed(3)+'px');V.dataset.ptn=f+(g?'t':'');
 // team names: full -> short form -> shrink to 11px (text widths scale with the size)
 const SET=R.map((q,i)=>{const m=room[i]-12*z;if(q.ef<=m+.01)return null;if(q.ab&&q.ea<=m+.01)return [q,q.ab,0];const t=q.ab||q.full,e=q.ab?q.ea:q.ef;let s=f0;
  while(s>11&&e*s/f0>m+.01)s-=.5;s=Math.max(11,s);if(e*s/f0>m+.01)window.__ptShort.push([t,+((e*s/f0-m)/z).toFixed(3)]);return [q,t,s]});
 SET.forEach(x=>{if(!x)return;const [q,t,s]=x;if(t!==q.full){q.pn.dataset.full=q.full;q.pn.firstChild.nodeValue=t}if(s&&s<f0)q.pn.style.fontSize=s+'px';window.__ptTeam.push([q.full,t,s||f0])})}
// Drafted-row layout (2026-11-25 .. 26, briefs PS-2 .. PS-3c): the holder's 36px picture stands beside both lines (absolute,
// centred on the text block from line 1's cap top to line 2's baseline); line 1 = the player (--ptnf) + NFL logo, line 2 = the team
// (12.5px) + NFL slot, starting at --ptlx per row = 44px + line 1's first-glyph left bearing - line 2's (SLT: [xMin, xMax, advance,
// yMin, yMax] em per glyph, IBM Plex Sans 400 / 600, Barlow Condensed 600, Martian Mono 400 / 600 at wdth 75 x .875, read from the
// font files), so both first glyphs' ink share one x. Line gap: line 1's baseline -> line 2's cap top = --ptg1 (10px, both looks).
// One right column (--ptvw = max(widest tile, widest via ink, TIMES / TRADED head ink) over every year): the TIMES TRADED tile and
// a quiet "via Nate" (.ptvt, the Drafts list's .dfvia declarations repeated), both right-aligned to the 16px inset; the via on line
// 2's baseline, lowered only as far as needed for 4px + one page unit of ink under the tile's hard shadow (future rows: tile over
// via, centred as a pair on the row).
const SLT={"P400":[{"!":[0.081,0.203,0.284,-0.012,0.698],"\"":[0.085,0.334,0.419,0.46,0.74],"#":[0.06,0.647,0.713,0.0,0.698],"$":[0.052,0.539,0.598,-0.082,0.78],"%":[0.065,0.862,0.927,-0.012,0.71],"&":[0.072,0.668,0.694,-0.012,0.71],"'":[0.085,0.157,0.242,0.46,0.74],"(":[0.083,0.34,0.335,-0.137,0.76],")":[-0.005,0.252,0.335,-0.137,0.76],"*":[0.036,0.414,0.45,0.388,0.747],"+":[0.067,0.533,0.6,0.062,0.548],",":[0.039,0.197,0.272,-0.133,0.117],"-":[0.069,0.33,0.399,0.261,0.347],".":[0.075,0.197,0.272,-0.012,0.117],"/":[0.009,0.342,0.383,-0.151,0.74],"0":[0.06,0.54,0.6,-0.012,0.71],"1":[0.051,0.547,0.6,0.0,0.698],"2":[0.069,0.533,0.6,0.0,0.71],"3":[0.042,0.505,0.6,-0.012,0.71],"4":[0.038,0.556,0.6,0.0,0.698],"5":[0.077,0.53,0.6,-0.012,0.698],"6":[0.067,0.533,0.6,-0.012,0.698],"7":[0.069,0.527,0.6,0.0,0.698],"8":[0.058,0.542,0.6,-0.012,0.71],"9":[0.067,0.533,0.6,0.0,0.71],":":[0.085,0.207,0.292,-0.012,0.528],";":[0.049,0.207,0.292,-0.133,0.528],"<":[0.09,0.51,0.6,-0.012,0.566],"=":[0.067,0.533,0.6,0.172,0.44],">":[0.09,0.51,0.6,-0.012,0.566],"?":[0.023,0.44,0.477,-0.012,0.71],"@":[0.065,0.826,0.891,-0.121,0.708],"A":[0.023,0.618,0.641,0.0,0.698],"B":[0.093,0.59,0.653,0.0,0.698],"C":[0.058,0.584,0.621,-0.012,0.71],"D":[0.093,0.613,0.671,0.0,0.698],"E":[0.093,0.519,0.583,0.0,0.698],"F":[0.093,0.509,0.559,0.0,0.698],"G":[0.058,0.623,0.695,-0.012,0.71],"H":[0.093,0.614,0.707,0.0,0.698],"I":[0.06,0.34,0.4,0.0,0.698],"J":[0.028,0.422,0.51,-0.012,0.698],"K":[0.093,0.612,0.634,0.0,0.698],"L":[0.093,0.474,0.501,0.0,0.698],"M":[0.093,0.719,0.812,0.0,0.698],"N":[0.093,0.614,0.707,0.0,0.698],"O":[0.058,0.65,0.708,-0.012,0.71],"P":[0.093,0.566,0.606,0.0,0.698],"Q":[0.058,0.65,0.708,-0.164,0.71],"R":[0.093,0.586,0.64,0.0,0.698],"S":[0.042,0.529,0.581,-0.012,0.71],"T":[0.022,0.55,0.572,0.0,0.698],"U":[0.088,0.59,0.678,-0.012,0.698],"V":[0.02,0.589,0.609,0.0,0.698],"W":[0.02,0.871,0.891,0.0,0.698],"X":[0.024,0.589,0.613,0.0,0.698],"Y":[0.013,0.58,0.593,0.0,0.698],"Z":[0.036,0.544,0.58,0.0,0.698],"[":[0.093,0.257,0.317,-0.138,0.76],"\\":[0.04,0.371,0.383,-0.151,0.74],"]":[0.06,0.224,0.317,-0.138,0.76],"^":[0.05,0.55,0.6,0.296,0.698],"_":[0.03,0.535,0.565,-0.165,-0.095],"`":[0.187,0.345,0.6,0.585,0.779],"a":[0.044,0.505,0.534,-0.012,0.528],"b":[0.085,0.53,0.58,-0.012,0.74],"c":[0.047,0.475,0.503,-0.012,0.528],"d":[0.05,0.495,0.58,-0.012,0.74],"e":[0.047,0.502,0.549,-0.012,0.528],"f":[0.029,0.304,0.324,0.0,0.74],"g":[0.043,0.52,0.528,-0.212,0.586],"h":[0.085,0.488,0.568,0.0,0.74],"i":[0.076,0.174,0.25,0.0,0.74],"j":[0.001,0.174,0.25,-0.2,0.74],"k":[0.085,0.51,0.527,0.0,0.74],"l":[0.085,0.241,0.272,0.0,0.74],"m":[0.085,0.793,0.873,0.0,0.528],"n":[0.085,0.488,0.568,0.0,0.528],"o":[0.047,0.513,0.56,-0.012,0.528],"p":[0.085,0.53,0.58,-0.2,0.528],"q":[0.05,0.495,0.58,-0.2,0.528],"r":[0.085,0.35,0.367,0.0,0.516],"s":[0.036,0.431,0.487,-0.012,0.528],"t":[0.029,0.307,0.351,0.0,0.659],"u":[0.08,0.483,0.568,-0.012,0.516],"v":[0.018,0.474,0.492,0.0,0.516],"w":[0.031,0.737,0.768,0.0,0.516],"x":[0.021,0.486,0.507,0.0,0.516],"y":[0.017,0.482,0.499,-0.2,0.516],"z":[0.033,0.431,0.464,0.0,0.516],"{":[0.022,0.283,0.343,-0.138,0.76],"|":[0.123,0.191,0.314,-0.138,0.76],"}":[0.06,0.321,0.343,-0.138,0.76],"~":[0.061,0.539,0.6,0.236,0.374],"\u2019":[0.044,0.202,0.273,0.5,0.75],"\u2013":[0.036,0.552,0.588,0.266,0.342]," ":[0,0,0.236,0,0]},0.698],"P600":[{"!":[0.074,0.235,0.309,-0.012,0.698],"\"":[0.073,0.398,0.471,0.428,0.74],"#":[0.025,0.629,0.656,0.0,0.698],"$":[0.038,0.553,0.6,-0.082,0.78],"%":[0.054,0.906,0.96,-0.012,0.71],"&":[0.056,0.703,0.713,-0.012,0.71],"'":[0.073,0.187,0.26,0.428,0.74],"(":[0.051,0.348,0.337,-0.138,0.76],")":[-0.011,0.287,0.337,-0.138,0.76],"*":[0.033,0.523,0.556,0.282,0.747],"+":[0.067,0.533,0.6,0.063,0.549],",":[0.037,0.229,0.299,-0.143,0.154],"-":[0.058,0.344,0.402,0.241,0.368],".":[0.069,0.229,0.299,-0.011,0.154],"/":[0.005,0.399,0.437,-0.151,0.74],"0":[0.04,0.56,0.6,-0.012,0.71],"1":[0.04,0.57,0.6,0.0,0.698],"2":[0.05,0.546,0.6,0.0,0.71],"3":[0.024,0.529,0.6,-0.012,0.71],"4":[0.032,0.564,0.6,0.0,0.698],"5":[0.055,0.553,0.6,-0.012,0.698],"6":[0.049,0.556,0.6,-0.012,0.698],"7":[0.059,0.543,0.6,0.0,0.698],"8":[0.045,0.555,0.6,-0.012,0.71],"9":[0.044,0.551,0.6,0.0,0.71],":":[0.079,0.239,0.319,-0.011,0.534],";":[0.047,0.239,0.319,-0.143,0.534],"<":[0.099,0.501,0.6,-0.005,0.593],"=":[0.067,0.533,0.6,0.142,0.468],">":[0.099,0.501,0.6,-0.005,0.593],"?":[0.017,0.463,0.493,-0.012,0.71],"@":[0.062,0.84,0.899,-0.121,0.709],"A":[0.021,0.651,0.672,0.0,0.698],"B":[0.082,0.616,0.663,0.0,0.698],"C":[0.052,0.611,0.642,-0.012,0.71],"D":[0.082,0.637,0.689,0.0,0.698],"E":[0.082,0.542,0.6,0.0,0.698],"F":[0.082,0.531,0.577,0.0,0.698],"G":[0.052,0.641,0.712,-0.012,0.71],"H":[0.082,0.637,0.719,0.0,0.698],"I":[0.053,0.37,0.423,0.0,0.698],"J":[0.026,0.467,0.545,-0.011,0.698],"K":[0.082,0.663,0.678,0.0,0.698],"L":[0.082,0.489,0.521,0.0,0.698],"M":[0.082,0.735,0.817,0.0,0.698],"N":[0.082,0.637,0.719,0.0,0.698],"O":[0.052,0.66,0.712,-0.012,0.71],"P":[0.082,0.603,0.641,0.0,0.698],"Q":[0.052,0.66,0.712,-0.178,0.71],"R":[0.082,0.616,0.664,0.0,0.698],"S":[0.039,0.561,0.611,-0.012,0.71],"T":[0.026,0.555,0.58,0.0,0.698],"U":[0.077,0.612,0.689,-0.012,0.698],"V":[0.016,0.622,0.638,0.0,0.698],"W":[0.026,0.922,0.949,0.0,0.698],"X":[0.018,0.637,0.655,0.0,0.698],"Y":[0.01,0.622,0.632,0.0,0.698],"Z":[0.038,0.561,0.599,0.0,0.698],"[":[0.082,0.276,0.329,-0.138,0.76],"\\":[0.037,0.431,0.437,-0.151,0.74],"]":[0.053,0.247,0.329,-0.138,0.76],"^":[0.044,0.556,0.6,0.283,0.698],"_":[0.03,0.529,0.559,-0.183,-0.075],"`":[0.161,0.364,0.6,0.581,0.805],"a":[0.037,0.529,0.559,-0.012,0.534],"b":[0.074,0.555,0.6,-0.012,0.74],"c":[0.039,0.488,0.513,-0.012,0.534],"d":[0.045,0.526,0.6,-0.012,0.74],"e":[0.039,0.519,0.558,-0.012,0.534],"f":[0.023,0.335,0.35,0.0,0.74],"g":[0.028,0.545,0.545,-0.212,0.614],"h":[0.074,0.52,0.588,0.0,0.74],"i":[0.063,0.213,0.275,0.0,0.746],"j":[-0.006,0.213,0.275,-0.2,0.746],"k":[0.074,0.557,0.562,0.0,0.74],"l":[0.074,0.271,0.294,0.0,0.74],"m":[0.074,0.82,0.888,0.0,0.534],"n":[0.074,0.52,0.588,0.0,0.534],"o":[0.039,0.524,0.563,-0.012,0.534],"p":[0.074,0.555,0.6,-0.2,0.534],"q":[0.045,0.526,0.6,-0.2,0.534],"r":[0.074,0.373,0.393,0.0,0.522],"s":[0.029,0.46,0.499,-0.012,0.534],"t":[0.025,0.337,0.374,0.0,0.665],"u":[0.068,0.514,0.588,-0.012,0.522],"v":[0.012,0.513,0.524,0.0,0.522],"w":[0.023,0.797,0.819,0.0,0.522],"x":[0.019,0.525,0.544,0.0,0.522],"y":[0.009,0.514,0.524,-0.2,0.522],"z":[0.037,0.465,0.502,0.0,0.522],"{":[0.02,0.31,0.363,-0.138,0.76],"|":[0.134,0.242,0.376,-0.138,0.76],"}":[0.053,0.344,0.363,-0.138,0.76],"~":[0.055,0.545,0.6,0.219,0.392],"\u2019":[0.038,0.227,0.292,0.465,0.75],"\u2013":[0.036,0.552,0.588,0.25,0.358]," ":[0,0,0.236,0,0]},0.698],"B600":[{"!":[0.064,0.205,0.269,0.002,0.7],"\"":[0.018,0.287,0.306,0.477,0.697],"#":[0.042,0.565,0.606,0.023,0.674],"$":[0.032,0.404,0.434,-0.081,0.788],"%":[0.054,0.717,0.772,-0.009,0.709],"&":[0.032,0.542,0.581,-0.009,0.708],"'":[0.018,0.133,0.152,0.48,0.699],"(":[0.0,0.218,0.279,-0.096,0.76],")":[0.062,0.28,0.279,-0.096,0.76],"*":[0.021,0.3407,0.361,0.395,0.746],"+":[0.027,0.413,0.439,0.121,0.507],",":[0.0328,0.1616,0.199,-0.091,0.157],"-":[0.027,0.298,0.325,0.251,0.351],".":[0.035,0.176,0.211,-0.002,0.14],"/":[0.0202,0.3418,0.386,0.0,0.7],"0":[0.038,0.412,0.45,-0.011,0.711],"1":[0.01,0.23,0.274,0.0,0.7],"2":[0.029,0.404,0.425,0.0,0.708],"3":[0.028,0.387,0.426,-0.008,0.7],"4":[0.017,0.443,0.459,0.0,0.7],"5":[0.039,0.4,0.428,-0.008,0.7],"6":[0.039,0.401,0.429,-0.008,0.708],"7":[0.016,0.38,0.392,0.0,0.7],"8":[0.038,0.396,0.434,-0.008,0.712],"9":[0.022,0.384,0.423,-0.008,0.708],":":[0.057,0.198,0.252,0.002,0.475],";":[0.035,0.183,0.218,-0.089,0.479],"<":[0.027,0.413,0.439,0.0574,0.511],"=":[0.027,0.413,0.439,0.181,0.46],">":[0.027,0.413,0.439,0.057,0.5106],"?":[0.021,0.391,0.413,-0.001,0.71],"@":[0.038,0.722,0.759,-0.078,0.641],"A":[0.0135,0.442,0.456,0.0,0.7],"B":[0.054,0.435,0.462,0.0,0.7],"C":[0.042,0.42,0.457,-0.008,0.708],"D":[0.054,0.426,0.472,0.0,0.7],"E":[0.054,0.403,0.435,0.0,0.7],"F":[0.054,0.402,0.415,0.0,0.7],"G":[0.042,0.42,0.462,-0.008,0.708],"H":[0.054,0.423,0.477,0.0,0.7],"I":[0.054,0.17,0.224,0.0,0.7],"J":[0.017,0.388,0.443,-0.008,0.7],"K":[0.054,0.46,0.477,0.0,0.7],"L":[0.054,0.403,0.415,0.0,0.7],"M":[0.051,0.487,0.538,0.0,0.7],"N":[0.054,0.453,0.507,0.0,0.7],"O":[0.042,0.425,0.467,-0.008,0.708],"P":[0.053,0.432,0.457,0.0,0.701],"Q":[0.042,0.413,0.455,-0.104,0.708],"R":[0.054,0.438,0.461,0.0,0.7],"S":[0.032,0.404,0.434,-0.008,0.708],"T":[0.028,0.425,0.452,0.0,0.7],"U":[0.05,0.428,0.478,-0.008,0.7],"V":[0.027,0.4436,0.471,0.0,0.7],"W":[0.023,0.6423,0.665,0.0,0.7],"X":[0.03,0.43,0.46,0.0,0.7],"Y":[0.029,0.4268,0.456,0.001,0.7],"Z":[0.025,0.377,0.406,0.0,0.7],"[":[0.027,0.237,0.33,-0.138,0.791],"\\":[0.045,0.367,0.386,0.0,0.7],"]":[0.093,0.302,0.33,-0.138,0.791],"^":[0.0302,0.383,0.413,0.301,0.7],"_":[0.017,0.388,0.405,0.0,0.089],"`":[0.024,0.183,0.206,0.575,0.7],"a":[0.029,0.397,0.434,-0.008,0.519],"b":[0.046,0.399,0.437,-0.008,0.7],"c":[0.038,0.393,0.422,-0.008,0.519],"d":[0.038,0.391,0.437,-0.008,0.7],"e":[0.038,0.392,0.426,-0.008,0.519],"f":[0.022,0.265,0.291,0.0,0.704],"g":[0.038,0.391,0.431,-0.206,0.519],"h":[0.046,0.397,0.439,0.0,0.7],"i":[0.036,0.177,0.215,0.0,0.723],"j":[-0.047,0.174,0.211,-0.205,0.723],"k":[0.046,0.41,0.433,0.0,0.7],"l":[0.042,0.158,0.199,0.0,0.7],"m":[0.046,0.623,0.665,0.0,0.519],"n":[0.046,0.397,0.439,0.0,0.519],"o":[0.038,0.395,0.432,-0.008,0.519],"p":[0.05,0.403,0.441,-0.189,0.519],"q":[0.038,0.391,0.441,-0.189,0.519],"r":[0.046,0.3034,0.313,0.001,0.517],"s":[0.03,0.377,0.398,-0.006,0.517],"t":[0.017,0.26,0.282,0.0,0.638],"u":[0.042,0.393,0.438,-0.007,0.511],"v":[0.019,0.3965,0.415,0.0,0.512],"w":[0.019,0.5736,0.592,0.0,0.512],"x":[0.018,0.399,0.417,0.0,0.511],"y":[0.016,0.3875,0.403,-0.199,0.512],"z":[0.024,0.346,0.368,0.0,0.511],"{":[0.027,0.291,0.319,-0.138,0.791],"|":[0.027,0.143,0.171,-0.08,0.76],"}":[0.027,0.291,0.319,-0.138,0.791],"~":[0.0293,0.4497,0.48,0.213,0.372],"\u2019":[0.0024,0.1609,0.165,0.482,0.7],"\u2013":[0.027,0.351,0.377,0.234,0.334]," ":[0,0,0.2,0,0]},0.7],"M400":[{"!":[0.1934,0.3316,0.525,-0.0061,0.7],"\"":[0.1216,0.4034,0.525,0.4007,0.742],"#":[0.0368,0.4883,0.525,0.0,0.7],"$":[0.07,0.4778,0.525,-0.0875,0.7875],"%":[0.0306,0.4944,0.525,-0.014,0.714],"&":[0.056,0.497,0.525,-0.014,0.714],"'":[0.21,0.315,0.525,0.4007,0.742],"(":[0.175,0.4025,0.525,-0.14,0.805],")":[0.1225,0.35,0.525,-0.14,0.805],"*":[0.0499,0.4751,0.525,0.1032,0.5084],"+":[0.0525,0.4725,0.525,0.0963,0.5162],",":[0.1864,0.3404,0.525,-0.1575,0.1663],"-":[0.0525,0.4725,0.525,0.2625,0.35],".":[0.1934,0.3316,0.525,-0.007,0.1663],"/":[0.0919,0.4331,0.525,-0.1488,0.742],"0":[0.0481,0.4769,0.525,-0.014,0.714],"1":[0.0875,0.4725,0.525,0.0,0.7],"2":[0.07,0.455,0.525,0.0,0.714],"3":[0.0656,0.4594,0.525,-0.014,0.714],"4":[0.0473,0.4848,0.525,0.0,0.7],"5":[0.0683,0.4585,0.525,-0.014,0.7],"6":[0.0656,0.4594,0.525,-0.014,0.7],"7":[0.0761,0.4489,0.525,0.0,0.7],"8":[0.0648,0.4603,0.525,-0.014,0.714],"9":[0.0656,0.4594,0.525,0.0,0.714],":":[0.1934,0.3316,0.525,-0.007,0.532],";":[0.1864,0.3404,0.525,-0.1575,0.532],"<":[0.0875,0.4375,0.525,0.0604,0.5521],"=":[0.0788,0.4463,0.525,0.1488,0.4637],">":[0.0875,0.4375,0.525,0.0604,0.5521],"?":[0.077,0.4445,0.525,-0.0061,0.714],"@":[0.0385,0.483,0.525,-0.189,0.714],"A":[0.0394,0.4856,0.525,0.0,0.7],"B":[0.0919,0.4769,0.525,0.0,0.7],"C":[0.0665,0.4778,0.525,-0.014,0.714],"D":[0.07,0.4769,0.525,0.0,0.7],"E":[0.105,0.455,0.525,0.0,0.7],"F":[0.1225,0.4725,0.525,0.0,0.7],"G":[0.0569,0.4681,0.525,-0.0105,0.714],"H":[0.07,0.455,0.525,0.0,0.7],"I":[0.07,0.455,0.525,0.0,0.7],"J":[0.0613,0.4463,0.525,-0.014,0.7],"K":[0.1006,0.4821,0.525,0.0,0.7],"L":[0.14,0.4725,0.525,0.0,0.7],"M":[0.0525,0.4725,0.525,0.0,0.7],"N":[0.0648,0.4603,0.525,0.0,0.7],"O":[0.0481,0.4769,0.525,-0.014,0.714],"P":[0.0963,0.4883,0.525,0.0,0.7],"Q":[0.0481,0.4769,0.525,-0.189,0.714],"R":[0.0858,0.497,0.525,0.0,0.7],"S":[0.07,0.4778,0.525,-0.014,0.714],"T":[0.0438,0.4813,0.525,0.0,0.7],"U":[0.0648,0.4603,0.525,-0.014,0.7],"V":[0.0394,0.4856,0.525,0.0,0.7],"W":[0.0175,0.5075,0.525,0.0,0.7],"X":[0.0403,0.4848,0.525,0.0,0.7],"Y":[0.0315,0.4935,0.525,0.0,0.7],"Z":[0.0788,0.4463,0.525,0.0,0.7],"[":[0.21,0.4025,0.525,-0.1225,0.7875],"\\":[0.0919,0.4331,0.525,-0.1488,0.742],"]":[0.1225,0.315,0.525,-0.1225,0.7875],"^":[0.0823,0.4427,0.525,0.4725,0.714],"_":[0.0525,0.4725,0.525,-0.1313,-0.0438],"`":[0.1208,0.4042,0.525,0.5005,0.742],"a":[0.0613,0.4323,0.525,-0.0123,0.539],"b":[0.0805,0.4708,0.525,-0.014,0.742],"c":[0.0796,0.4655,0.525,-0.014,0.539],"d":[0.0542,0.4445,0.525,-0.014,0.742],"e":[0.077,0.4603,0.525,-0.014,0.539],"f":[0.0998,0.511,0.525,0.0,0.756],"g":[0.056,0.4393,0.525,-0.189,0.539],"h":[0.0875,0.4463,0.525,0.0,0.742],"i":[0.1094,0.4594,0.525,0.0,0.749],"j":[0.0656,0.399,0.525,-0.189,0.749],"k":[0.119,0.4848,0.525,0.0,0.742],"l":[0.0963,0.4463,0.525,0.0,0.742],"m":[0.0586,0.4699,0.525,0.0,0.539],"n":[0.0875,0.4463,0.525,0.0,0.539],"o":[0.0648,0.4603,0.525,-0.014,0.539],"p":[0.0805,0.4708,0.525,-0.175,0.539],"q":[0.0542,0.4445,0.525,-0.175,0.539],"r":[0.0735,0.476,0.525,0.0,0.539],"s":[0.084,0.4515,0.525,-0.014,0.539],"t":[0.0665,0.4585,0.525,-0.014,0.6615],"u":[0.0788,0.4375,0.525,-0.014,0.525],"v":[0.0525,0.4725,0.525,0.0,0.525],"w":[0.021,0.504,0.525,0.0,0.525],"x":[0.0525,0.4725,0.525,0.0,0.525],"y":[0.0525,0.4725,0.525,-0.189,0.525],"z":[0.0945,0.4305,0.525,0.0,0.525],"{":[0.1488,0.4287,0.525,-0.133,0.798],"|":[0.2214,0.3036,0.525,-0.0525,0.7525],"}":[0.0963,0.3762,0.525,-0.133,0.798],"~":[0.07,0.455,0.525,0.2144,0.3981],"\u2019":[0.1864,0.3404,0.525,0.4323,0.756],"\u2013":[0.0569,0.4681,0.525,0.2625,0.35]," ":[0,0,0.525,0,0]},0.7],"M600":[{"!":[0.1776,0.3474,0.525,-0.0074,0.7],"\"":[0.0927,0.4323,0.525,0.3837,0.742],"#":[0.0282,0.4968,0.525,0.0,0.7],"$":[0.0538,0.4837,0.525,-0.0875,0.7875],"%":[0.0242,0.5008,0.525,-0.0157,0.7157],"&":[0.0424,0.5072,0.525,-0.014,0.7157],"'":[0.1938,0.3312,0.525,0.3837,0.742],"(":[0.158,0.4195,0.525,-0.1655,0.8305],")":[0.1055,0.367,0.525,-0.1655,0.8305],"*":[0.0337,0.4913,0.525,0.0858,0.5216],"+":[0.0355,0.4895,0.525,0.0792,0.5333],",":[0.1677,0.3612,0.525,-0.1618,0.2028],"-":[0.0355,0.4895,0.525,0.2497,0.3628],".":[0.1742,0.3508,0.525,-0.0087,0.2028],"/":[0.0804,0.4446,0.525,-0.1488,0.742],"0":[0.0332,0.4918,0.525,-0.0157,0.7157],"1":[0.0747,0.4853,0.525,0.0,0.7],"2":[0.0551,0.4699,0.525,0.0,0.7157],"3":[0.0507,0.4743,0.525,-0.0157,0.7157],"4":[0.0353,0.5001,0.525,0.0,0.7],"5":[0.0504,0.4738,0.525,-0.0157,0.7],"6":[0.049,0.476,0.525,-0.0157,0.7],"7":[0.0663,0.4587,0.525,0.0,0.7],"8":[0.0494,0.4756,0.525,-0.0157,0.7157],"9":[0.049,0.476,0.525,0.0,0.7157],":":[0.1742,0.3508,0.525,-0.0087,0.5422],";":[0.1677,0.3612,0.525,-0.1618,0.5422],"<":[0.0705,0.4545,0.525,0.0459,0.5666],"=":[0.0788,0.4463,0.525,0.136,0.4765],">":[0.0705,0.4545,0.525,0.0459,0.5666],"?":[0.0685,0.4573,0.525,-0.0074,0.7157],"@":[0.0308,0.4873,0.525,-0.1822,0.7157],"A":[0.0279,0.4971,0.525,0.0,0.7],"B":[0.0727,0.4918,0.525,0.0,0.7],"C":[0.0503,0.4905,0.525,-0.0157,0.7157],"D":[0.053,0.4918,0.525,0.0,0.7],"E":[0.0837,0.4678,0.525,0.0,0.7],"F":[0.097,0.481,0.525,0.0,0.7],"G":[0.0437,0.4856,0.525,-0.0122,0.7157],"H":[0.053,0.472,0.525,0.0,0.7],"I":[0.053,0.472,0.525,0.0,0.7],"J":[0.0442,0.4633,0.525,-0.0157,0.7],"K":[0.0815,0.4979,0.525,0.0,0.7],"L":[0.1187,0.481,0.525,0.0,0.7],"M":[0.0397,0.4853,0.525,0.0,0.7],"N":[0.0503,0.4747,0.525,0.0,0.7],"O":[0.0332,0.4918,0.525,-0.0157,0.7157],"P":[0.0707,0.4985,0.525,0.0,0.7],"Q":[0.0332,0.4918,0.525,-0.1907,0.7157],"R":[0.0619,0.5072,0.525,0.0,0.7],"S":[0.0538,0.4837,0.525,-0.0157,0.7157],"T":[0.0318,0.4932,0.525,0.0,0.7],"U":[0.0477,0.4773,0.525,-0.0157,0.7],"V":[0.0279,0.4971,0.525,0.0,0.7],"W":[0.0141,0.5109,0.525,0.0,0.7],"X":[0.0305,0.4945,0.525,0.0,0.7],"Y":[0.0204,0.5046,0.525,0.0,0.7],"Z":[0.066,0.459,0.525,0.0,0.7],"[":[0.193,0.4195,0.525,-0.1412,0.8062],"\\":[0.0804,0.4446,0.525,-0.1488,0.742],"]":[0.1055,0.332,0.525,-0.1412,0.8062],"^":[0.061,0.464,0.525,0.4657,0.7157],"_":[0.0355,0.4895,0.525,-0.1568,-0.0438],"`":[0.1025,0.4217,0.525,0.4716,0.742],"a":[0.0451,0.4501,0.525,-0.0123,0.5492],"b":[0.066,0.4844,0.525,-0.014,0.742],"c":[0.0656,0.4766,0.525,-0.0157,0.5492],"d":[0.0406,0.459,0.525,-0.014,0.742],"e":[0.0625,0.4717,0.525,-0.0157,0.5492],"f":[0.081,0.5263,0.525,0.0,0.7577],"g":[0.0458,0.4563,0.525,-0.1907,0.5475],"h":[0.0705,0.4616,0.525,0.0,0.742],"i":[0.0945,0.4785,0.525,0.0,0.7686],"j":[0.0499,0.4101,0.525,-0.1907,0.7686],"k":[0.0952,0.4975,0.525,0.0,0.742],"l":[0.0814,0.4654,0.525,0.0,0.742],"m":[0.042,0.4865,0.525,0.0,0.5492],"n":[0.0705,0.4616,0.525,0.0,0.5492],"o":[0.052,0.473,0.525,-0.0157,0.5492],"p":[0.066,0.4844,0.525,-0.175,0.5475],"q":[0.0406,0.459,0.525,-0.175,0.5475],"r":[0.0624,0.4888,0.525,0.0,0.5475],"s":[0.0712,0.4651,0.525,-0.0157,0.5492],"t":[0.0554,0.4738,0.525,-0.0157,0.6717],"u":[0.0634,0.4545,0.525,-0.0157,0.5335],"v":[0.0397,0.4853,0.525,0.0,0.5335],"w":[0.0176,0.5074,0.525,0.0,0.5335],"x":[0.0355,0.4895,0.525,0.0,0.5335],"y":[0.0402,0.4857,0.525,-0.1907,0.5335],"z":[0.0792,0.4458,0.525,0.0,0.5335],"{":[0.1317,0.4458,0.525,-0.1577,0.8227],"|":[0.2099,0.3151,0.525,-0.0525,0.7525],"}":[0.0792,0.3933,0.525,-0.1577,0.8227],"~":[0.07,0.455,0.525,0.2033,0.4092],"\u2019":[0.1677,0.3612,0.525,0.3931,0.7577],"\u2013":[0.0399,0.4851,0.525,0.2523,0.3602]," ":[0,0,0.525,0,0]},0.7]};
const sltK=e=>{const c=getComputedStyle(e),w=+c.fontWeight>=500?600:400;return /Martian/.test(c.fontFamily)?'M'+w:/Barlow/.test(c.fontFamily)?'B600':'P'+w};
const sltG=(e,ch)=>{const t=SLT[sltK(e)];return t&&t[0][ch]?t[0][ch]:[0,.5,.55,0,.7]};const sltC=e=>{const t=SLT[sltK(e)];return t?t[1]:.7};
const PN0f=l=>parseFloat(getComputedStyle(l.querySelector('.ptpn')).fontSize);
function lxOf(r,fp){const t=r.querySelector('.ptt'),p=r.querySelector('.ptpn');if(!t||!p)return 44;const ct=t.textContent.trim()[0],cp=p.textContent.trim()[0];
 return (parseFloat(getComputedStyle(r.querySelector('.ptl1')).paddingLeft)||44)+sltG(t,ct)[0]*parseFloat(getComputedStyle(t).fontSize)-sltG(p,cp)[0]*(fp||parseFloat(getComputedStyle(p).fontSize))}
// ink width of a via text: canvas advance (kerning included) + spacing, less the first glyph's left and the last glyph's right bearing
function viaInk(e){const t=e.textContent,c=getComputedStyle(e),f=parseFloat(c.fontSize),ls=parseFloat(c.letterSpacing)||0,ws=parseFloat(c.wordSpacing)||0;
 _ic.font=c.fontStyle+' '+c.fontWeight+' '+(f*50)+'px '+c.fontFamily;const a=_ic.measureText(t).width/50+ls*(t.length-1)+ws*(t.split(' ').length-1),g0=sltG(e,t[0]),g1=sltG(e,t[t.length-1]);
 return a-g0[0]*f-(g1[2]-g1[1])*f}
// box-shadow ink above / below an element's box: hard shadows only (blur 0), [top, bottom] px
function shExt(e){let t=0,b=0;(getComputedStyle(e).boxShadow||'').split(/,(?![^(]*\))/).forEach(x=>{if(/inset/.test(x))return;const n=(x.replace(/rgba?\([^)]*\)|oklch\([^)]*\)|#[0-9a-f]+|[a-z]+\([^)]*\)/gi,'').match(/-?[\d.]+px/g)||[]).map(parseFloat);
 if(n.length<2||(n[2]||0)>0)return;const oy=n[1],sp=n[3]||0;t=Math.max(t,sp-oy);b=Math.max(b,oy+sp)});return [t,b]}
// [lowest yMin, highest yMax] (em) over the glyphs of every text matched by sel in V, by e's font
function yExt(V,sel,e){const T=SLT[sltK(e)];let lo=0,hi=0;if(!T)return [-.25,.75];V.querySelectorAll(sel).forEach(x=>{for(const c of x.textContent){const g=T[0][c];if(g){lo=Math.min(lo,g[3]);hi=Math.max(hi,g[4])}}});return [lo,hi]}
function rowFit(early){const V=X.querySelector('.ptv-k');if(!V||!V.offsetParent)return;const Y=[...V.querySelectorAll('.ptyx')].find(y=>y.offsetParent);if(!Y)return;
 const K=[...Y.querySelectorAll('.ptk')].filter(r=>r.offsetParent),D=K.filter(r=>!r.classList.contains('ptk1')&&r.querySelector('.ptl2')),z=(K[0]&&K[0].currentCSSZoom)||1,up=v=>Math.ceil(v*100)/100,
  u=1/((window.visualViewport&&visualViewport.scale)||1),setv=(e,k,v)=>{if(e.style.getPropertyValue(k)!==v)e.style.setProperty(k,v)};
 // the one right column: max(widest tile, widest via, TIMES / TRADED head ink), every year
 {let tw=0;const b0=[...V.querySelectorAll('.ptxn b')].find(b=>b.offsetParent)||V.querySelector('.ptxn b'),f0=b0?parseFloat(getComputedStyle(b0).fontSize):15,rt=b0&&document.documentElement.classList.contains('retro')&&/Martian/.test(getComputedStyle(b0).fontFamily);
  V.querySelectorAll('.ptxn b').forEach(b=>{const t=b.firstChild?b.firstChild.nodeValue.trim():'';if(rt){tw=Math.max(tw,inkC(b0,t));return}let x=0,L=null,R=0;for(const c of t){const m=BC7[c];if(!m)return;if(L==null)L=m[0]*f0;R=x+m[1]*f0;x+=m[4]*f0}if(L!=null)tw=Math.max(tw,R-L)});
  const tile=tw?Math.round((tw+16)/u)*u:0,vw=Math.max(tile,...[...V.querySelectorAll('.ptvt')].map(viaInk),...[...V.querySelectorAll('.pthx i')].slice(0,2).map(h=>inkC(h,h.textContent)));setv(V,'--ptvw',up(vw)+'px')}
 // 1. one text left edge (writes only)
 D.forEach(r=>setv(r.querySelector('.ptl2'),'--ptlx',lxOf(r).toFixed(3)+'px'));
 if(early)return;
 // 2. the row model, from a shown drafted row, or (future-only view) a hidden probe cloned from any drafted year
 let ref=D.find(r=>!r.querySelector('.ptt').style.fontSize)||D[0],probe=null;
 if(!ref){const src=[...V.querySelectorAll('.ptk:not(.ptk1)')].find(r=>r.querySelector('.nfl'))||V.querySelector('.ptk:not(.ptk1)'),P0=[...Y.querySelectorAll('.ptp')].find(p=>p.offsetParent);
  if(src&&P0){probe=src.cloneNode(true);probe.setAttribute('aria-hidden','true');probe.style.visibility='hidden';probe.querySelectorAll('[style]').forEach(e=>e.removeAttribute('style'));P0.appendChild(probe);ref=probe;setv(probe.querySelector('.ptl2'),'--ptlx',lxOf(probe).toFixed(3)+'px')}}
 let M=null;
 if(ref){const t=ref.querySelector('.ptt'),p=ref.querySelector('.ptpn'),l1=ref.querySelector('.ptl1'),l2=ref.querySelector('.ptl2'),ft=parseFloat(getComputedStyle(t).fontSize),fp=parseFloat(getComputedStyle(p).fontSize),capT=sltC(t)*ft,capP=sltC(p)*fp;
  // line gap: line 1's baseline -> line 2's cap top = --ptg1 (one value, every row and width; PS-2b rule 1)
  const G=parseFloat(getComputedStyle(V).getPropertyValue('--ptg1'))||13;
  {const tb=_bl(t),pb=_bl(p),g=(pb-capP*z-tb)/z,m=parseFloat(getComputedStyle(l2).marginTop)||0;if(Math.abs(g-G)>.005)V.style.setProperty('--ptlg',(m+G-g).toFixed(3)+'px')}
  const y0=l1.getBoundingClientRect().top,tb=(_bl(t)-y0)/z,pb=(_bl(p)-y0)/z,bb=(l2.getBoundingClientRect().bottom-y0)/z,a=l1.querySelector(':scope>.pav'),ah=a?a.getBoundingClientRect().height/z:36,ar=a?shExt(a):[0,0],
   nf=V.querySelector('.ptk:not(.ptk1) .nfl')?ref.querySelector('.nfl'):null,nb=nf?(nf.getBoundingClientRect().bottom-y0)/z:-1e9,nt=nf?(nf.getBoundingClientRect().top-y0)/z:1e9,   // the NFL logo hangs from line 1
   T0=V.querySelector('.ptxn'),th=parseFloat(V.style.getPropertyValue('--ptch'))||(()=>{const f0=ft*z,c=Math.max(1,Math.round(.7*f0/u))*u,Hn=f0*1.15,cd=Math.round(c/u);let hd=Math.round(Hn/u);if((hd-cd)%2)hd+=(Hn/u>hd?1:-1);return hd*u/z})(),/* a view without tiles: tileSnap's own height rule */ts=T0?shExt(T0):[0,0],tc=tb-capT/2,
   v0=V.querySelector('.ptvt'),fv=v0?parseFloat(getComputedStyle(v0).fontSize):11,vy=v0?yExt(V,'.ptvt',v0):[0,0],
   te=yExt(V,'.ptk:not(.ptk1) .ptt',t),pe=yExt(V,'.ptpn',p),c=(tb-capT+pb)/2,
   // the via on the player's baseline, lowered only as far as needed for 4px of ink under the tile's hard shadow (rule 4)
   vo=v0&&T0?Math.max(0,(tc+th/2+ts[1]+4+u)-(pb-vy[1]*fv)):0;   // + one page unit, so the painted gap stays >= 4px after snapping
  // tileSnap puts each tile's baseline on the page's point grid: with every row a whole number of points tall, every tile of a view
  // sits the same distance dl from the model (team cap centre); read it from the tiles on show (any row), else half a point up
  const dl=(()=>{const v=K.map(r=>{const x=r.querySelector('.ptxn'),q=r.querySelector('.ptt');if(!x||!q)return null;const f=parseFloat(getComputedStyle(q).fontSize)*z;
   return (x.getBoundingClientRect().top-(_bl(q)-sltC(q)*f/2))/z+th/2}).filter(v=>v!=null);return v.length?Math.min(...v):-u/2})(),
   tt=tc-th/2+dl,
   rb=(parseFloat(getComputedStyle(ref).borderTopWidth)||0)+(parseFloat(getComputedStyle(ref).borderBottomWidth)||0),
   top=Math.min(c-ah/2-ar[0],tb-te[1]*ft,nt,T0?tt:1e9),bot=Math.max(c+ah/2+ar[1],pb-pe[0]*fp,nb,T0?tc+th/2+ts[1]:-1e9,v0?pb+vo-vy[0]*fv:-1e9);
  let kt=12-top,kb=12+bot-bb;{const T=kt+bb+kb+rb,e=Math.ceil(T/u-1e-6)*u-T;kt+=e/2;kb+=e/2}   // a whole number of points, the extra split top / bottom
  M={vo,d:pb+vo-(tc-th/2),ds:-vy[0]*fv,kh:kt+bb+kb+rb};
  setv(V,'--ptfo',((ar[0]-ar[1])/2).toFixed(3)+'px');setv(V,'--ptkt',kt.toFixed(3)+'px');setv(V,'--ptkb',kb.toFixed(3)+'px');setv(V,'--ptkh',M.kh.toFixed(3)+'px');window.__ptRow={G,kt:+kt.toFixed(3),kb:+kb.toFixed(3),h:+M.kh.toFixed(3),vo:+vo.toFixed(3),top:+top.toFixed(3),bot:+bot.toFixed(3),bb:+bb.toFixed(3)}}
 if(probe)probe.remove();
 // 3. holder logo centred on the text block (team cap top .. player baseline); reads, then writes
 const LG=D.map(r=>{const t=r.querySelector('.ptt'),p=r.querySelector('.ptpn'),l1=r.querySelector('.ptl1'),a=l1.querySelector(':scope>.pav');if(!a)return null;
  const ft=parseFloat(getComputedStyle(t).fontSize)*z;return [a,((_bl(t)-sltC(t)*ft+_bl(p))/2-l1.getBoundingClientRect().top)/z-a.getBoundingClientRect().height/z/2]});
 LG.forEach(x=>{if(x)x[0].style.top=x[1].toFixed(3)+'px'});
 // 4. future rows: the team name's cap centre on the logo's centre
 const F=K.filter(r=>r.classList.contains('ptk1'));F.forEach(r=>{const t=r.querySelector('.ptt');if(t)t.style.top=''});
 const FT=F.map(r=>{const t=r.querySelector('.ptt'),a=r.querySelector('.ptl1>.pav');if(!t||!a)return null;const q=a.getBoundingClientRect(),ft=parseFloat(getComputedStyle(t).fontSize)*z;return [t,((q.top+q.bottom)/2-(_bl(t)-sltC(t)*ft/2))/z]});
 FT.forEach(x=>{if(x)x[0].style.top=x[1].toFixed(3)+'px'});
 // 5. via: last glyph's ink on the inset; drafted rows on line 2's baseline (+ the rule-4 offset); future rows: tile over via as
 // the drafted rows' pair (tile top -> via baseline = M.d), centred on the row
 const VT=K.map(r=>[r,r.querySelector('.ptvt')]).filter(x=>x[1]);VT.forEach(([r,v])=>{v.style.top='';const c=getComputedStyle(v),f=parseFloat(c.fontSize),t=v.textContent,g=sltG(v,t[t.length-1]);
  v.style.marginRight=(-((g[2]-g[1])*f+(parseFloat(c.letterSpacing)||0))).toFixed(3)+'px'});
 const vo=M?M.vo:0,dd=M?M.d:20,ds=M?M.ds:2,VY=VT.map(([r,v])=>{const p=r.querySelector('.ptpn');if(p)return [v,(_bl(p)-_bl(v))/z+vo];
  const T=r.querySelector('.ptxn'),R=r.getBoundingClientRect(),fv=parseFloat(getComputedStyle(v).fontSize)*z,cv=sltC(v)*fv,mid=(R.top+R.bottom)/2,vb=_bl(v);
  if(!T)return [v,(mid+cv/2-vb)/z];const Tr=T.getBoundingClientRect(),top=mid-(dd+ds)*z/2,dt=Math.round((top-Tr.top)/z/u)*u;   // pair = tile top .. the vias' lowest descender, centred on the row
  return [v,(Tr.top+dt*z+dd*z-vb)/z,T,dt]});
 VY.forEach(([v,dy,T,dt])=>{v.style.top=dy.toFixed(3)+'px';if(T)T.style.top=((parseFloat(T.style.top)||0)+dt).toFixed(4)+'px'})}
// ptxFit (2026-11-07; 2026-11-26, PS-3c): Picks right-hand column and strip; reads everything, then writes.
// TIMES TRADED: tile width --ptcw = the widest count's digit ink in the shown year + 2 x 8px (tileSnap then sets the final
// width, height, figure size and placement). Strip: TIMES and TRADED right-aligned so each line's last glyph's ink (not the retro
// 1px shadow; as the via text) sits on the 16px inset (margin-right = -(letter-spacing + right bearing)). NFL slot: baseline on
// the team name's, by layout (position:relative; top).
function ptxFit(){const V=X.querySelector('.ptv-k');if(!V||!V.offsetParent)return;const P=[...V.querySelectorAll('.ptp')].filter(p=>p.offsetParent);if(!P.length)return;
 const q=s=>P.flatMap(p=>[...p.querySelectorAll(s)]),cnt=q('.ptxn'),hx=q('.pthx i'),slots=q('.ptns');
 [...hx,...slots].forEach(e=>e.style.transform='');hx.forEach(h=>h.style.marginRight='');slots.forEach(e=>e.style.top='');cnt.forEach(t=>{t.style.top=t.style.left='';const b=t.querySelector('b');b.style.left=b.style.top=''});V.style.removeProperty('--ptch');V.style.removeProperty('--ptcf');
 const z=(P[0].querySelector('.ptt')||P[0]).currentCSSZoom||1,iw=e=>{const i=tInk(e);return i?(i[1]-i[0])/z:0},up=v=>(Math.ceil(v*100)/100)+'px';
 const tw=Math.max(0,...cnt.map(t=>{const b=t.querySelector('b'),k=dInk(b);return k?(k[1]-k[0])/z:iw(b)}))+16;
 V.style.setProperty('--ptcw',up(tw));
 const W=[];
 hx.forEach(h=>{const c=getComputedStyle(h),t=h.textContent.trim().toUpperCase();h.style.marginRight=(-((parseFloat(c.letterSpacing)||0)+rBear(h,t.slice(-1)))).toFixed(3)+'px'});
 slots.forEach(n=>{const L=n.parentElement,pb=_bl(L.querySelector('.ptpn')),sb=_bl(n);if(pb==null||sb==null)return;
  // the baseline offset by layout (position:relative; top), not a transform: WebKit paints a transformed slot's glyphs on its own
  // device-pixel rounding, one pixel off the name's when the two baselines' fractions differ
  W.push([n,'',((pb-sb)/z).toFixed(3)+'px'])});
 W.forEach(([el,v,t])=>{if(t!=null){el.style.transform=v;el.style.top=t}else el.style.transform=v});tileSnap(V,cnt,z);rowFit()}
// BC7: Barlow Condensed 700 digit outlines from the font file (fontTools, 2026-11-07): [xMin, xMax, yMax, -yMin, advance]
// in em. WebKit's canvas measureText gives no glyph ink (actualBoundingBoxLeft/Right = 0 / advance, seen in WebKitGTK
// 2.52) and canvas has no tabular figures, so the TIMES TRADED tiles use these fixed outlines, not canvas, for the ink.
const BC7={"0":[.03,.423,.711,.011,.453],"1":[.009,.248,.7,0,.284],"2":[.024,.421,.708,0,.438],"3":[.023,.404,.7,.008,.436],"4":[.014,.47,.7,0,.484],"5":[.031,.416,.7,.008,.439],"6":[.031,.417,.708,.008,.44],"7":[.013,.397,.7,0,.407],"8":[.03,.41,.713,.008,.44],"9":[.018,.403,.708,.008,.435]};
// dInk(b) -> [L, R, A, D] in viewport px: ink left / right from the text origin, ink above / below the baseline
function dInk(b){const t=b.firstChild.nodeValue.trim(),f=parseFloat(getComputedStyle(b).fontSize)*(b.currentCSSZoom||1);let x=0,L=null,R=0,A=0,D=0;
 for(const c of t){const m=BC7[c];if(!m)return null;if(L==null)L=m[0]*f;R=x+m[1]*f;A=Math.max(A,m[2]*f);D=Math.max(D,m[3]*f);x+=m[4]*f}return [L,R,A,D]}
// tileSnap (2026-11-07): TIMES TRADED digits centred by ink in screenshots, both engines, by layout (relative left/top, no
// transforms). Browsers paint tile edges on device pixels and move text vertically in steps: WebKitGTK at DPR 3 by device
// pixels, headless Chromium at DPR 2-3 by whole CSS px (with the phones' 0.85 page scale, by whole points); horizontally
// both place glyphs in sub-pixel steps. So: the digits' flat height (.70em, from BC7) is a whole number of units
// u = 1 / visualViewport.scale (1 CSS px of the unscaled page, a whole number of device pixels at any DPR; size nudged by
// under half a unit); the baseline sits on the u grid nearest the holder name's cap-height centre; the tile's height and
// width are whole units with the vertical leftover an even number of them, top = baseline - cap - half of it (equal by
// construction), left on the u grid (Chromium snaps the tile box to it; a device-pixel grid left the digits up to 1px
// off there); the origin exactly at the ink-centred x. Reads, writes, read, write.
function tileSnap(V,cnt,z){if(!cnt.length)return;const sc=(window.visualViewport&&visualViewport.scale)||1,u=1/sc,dp=u,
  gu=(v,o=scrollY)=>Math.round((v+o)/u)*u-o,gd=v=>gu(v,scrollX);  // grid anchored to the document origin (engines snap in page space)
 // figure size: the name's size, nudged so the flat-digit height (.70em) is a whole number of units u (FreeType hints a
 // part-pixel cap to a whole one, CoreText does not: a whole-unit cap reads the same in both)
 const f0=parseFloat(getComputedStyle(cnt[0]).fontSize)*z,c=Math.max(1,Math.round(.7*f0/u))*u;V.style.setProperty('--ptcf',(c/.7/z).toFixed(4)+'px');
 const M=cnt.map(t=>{const b=t.querySelector('b'),r=document.createRange();r.selectNodeContents(b.firstChild);const o=r.getBoundingClientRect(),k=dInk(b);
  if(k)return {t,b,L:k[0],R:k[1]};const i=tInk(b);return {t,b,L:i[0]-o.left,R:i[1]-o.left}});
 // height: whole units, leftover (H - cap) an even number of them, nearest the nominal 1.15 x --ptnf; width: whole units
 const Hn=cnt[0].getBoundingClientRect().height,cd=Math.round(c/dp);let hd=Math.round(Hn/dp);if((hd-cd)%2)hd+=(Hn/dp>hd?1:-1);
 const H=hd*dp,Wd=gd(Math.max(...M.map(m=>m.R-m.L))+16*z);
 V.style.setProperty('--ptcw',(Wd/z).toFixed(4)+'px');V.style.setProperty('--ptch',(H/z).toFixed(4)+'px');
 // second pass: baseline on the unit grid nearest the name's cap-height centre + cap/2; tile top = baseline - cap - half the
 // leftover (whole units); tile left on the grid; origin exactly at the ink-centred x
 const P2=M.map(m=>{const T=m.t.getBoundingClientRect(),n=m.t.parentElement.querySelector('.ptt'),nb=n&&_bl(n),h=nb!=null?yInk(n,nb,'H'):null,bl=_bl(m.b),r=document.createRange();r.selectNodeContents(m.b.firstChild);
  return {T,cap:h?(h[0]+h[1])/2:(T.top+T.bottom)/2,bl,ox:r.getBoundingClientRect().left}});
 M.forEach((m,k)=>{const p=P2[k],B=gu(p.cap+c/2),top=B-c-(H-c)/2,left=gd((p.T.left+p.T.right)/2-Wd/2),O=left+(Wd-m.L-m.R)/2;
  m.t.style.top=((top-p.T.top)/z).toFixed(4)+'px';m.t.style.left=((left-p.T.left)/z).toFixed(4)+'px';
  m.b.style.top=((B-(p.bl+top-p.T.top))/z).toFixed(4)+'px';m.b.style.left=((O-(p.ox+left-p.T.left))/z).toFixed(4)+'px'})}
// pjFit: a future pick's number ("1.01") centred in its tile by glyph ink, not by advance box (the "1" bearings)
function pjFit(){const B=[...X.querySelectorAll('.ptv-k .ptpj b')].filter(b=>b.offsetParent);B.forEach(b=>b.style.transform='');
 const D=B.map(b=>{const i=tInk(b),t=b.parentElement.getBoundingClientRect(),z=b.currentCSSZoom||1;return i?((t.right-i[1])-(i[0]-t.left))/2/z:0});
 B.forEach((b,i)=>{if(Math.abs(D[i])>.01)b.style.transform='translateX('+D[i].toFixed(3)+'px)'})}
Q&&Q.addEventListener('input',draw);draw();
X.querySelectorAll('.ptb').forEach(b=>b.addEventListener('click',()=>{X.querySelectorAll('.ptb').forEach(x=>{const on=x===b;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on)});
 X.querySelectorAll('.ptv').forEach(v=>v.hidden=!v.classList.contains('ptv-'+b.dataset.v));fitN()}));
document.addEventListener('change',()=>requestAnimationFrame(fitN));addEventListener('resize',()=>requestAnimationFrame(()=>{fitN();if(!S.hidden){fitT();trFit()}}));document.fonts&&document.fonts.ready.then(()=>{fitN();route()});
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
 '.ptb{font:700 17px/1.4 var(--display);letter-spacing:.06em;text-transform:uppercase;padding:7px 12px 6px;border-radius:9px;border:1px solid var(--frame);background:var(--deck);color:var(--label);box-shadow:var(--sh-hard);cursor:pointer}'
 '.ptb.on{background:var(--chalk);color:var(--ink)}'
 '.ptv[hidden]{display:none!important}.ptyx{display:none}'
 '@media(min-width:1100px){.ptsw{max-width:420px}.ptyx .ptp{margin:0}#pty-0:checked{}'
 '.ptv-k .ptyx{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 16px;align-items:start}.ptv-p{max-width:760px}}'

 '.ptyb{margin:0 0 14px auto}.ptyb .yb{cursor:pointer}'
 '.ptyb.yrs .yb b{font-size:15px;padding:7.8px 0 8.2px}.ptyb.yrs .yb small{font-size:12px}'  # 2026-11-06: Paper Trail year buttons larger than the season buttons (15px / 12px); 7.8/8.2 = the season buttons' 6.83/7.17 digit correction scaled to 15px
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
 '.ptl1 .pav{width:22px;height:22px}.ptv-k .ptl1 .pav{width:36px;height:36px}.ptv-k .ptt{font-size:var(--ptnf,15px)}.ptv-k .ptn b{font-size:var(--ptnf,15px)}'
 '.ptt{font:600 15px/1.15 var(--body);color:var(--chalk);min-width:0}'
 '.ptl2{display:flex;align-items:center;gap:6px;min-width:0;font:400 12.5px/1.25 var(--body);color:var(--chalk)}.ptl2.ptd,.ptd{color:var(--text-dim)}'
 '@media(max-width:380px){.ptx{--ptg:40px}.pthd,.ptk{grid-template-columns:44px minmax(0,1fr) var(--ptxa,64px);column-gap:8px}.ptpl .pthd,.ptkp{grid-template-columns:44px minmax(0,1fr) 40px var(--ptg)}.ptpl .pthd>span:first-child{font-size:11px;letter-spacing:.06em}}'
 # Picks view (2026-11-26, briefs PS-2 .. PS-3c): pick tile | name column | one right column (--ptvw: TIMES TRADED tile over the quiet
 # via, both right-aligned to the 16px inset); 12px gaps. Strip: R · PLAYER (drafted years; "NFL" over the slot) or R · TEAM (future
 # years), TIMES over TRADED right-aligned by glyph ink (ptxFit), hidden in a year view without a traded pick (.pthx0, build time).
 '.ptv-k .pthd,.ptv-k .ptk{grid-template-columns:52px minmax(0,1fr) var(--ptvw,40px);padding-right:16px}.ptv-k .pthd>span:nth-child(2){text-align:left}.ptv-k .pthd{padding-top:8.72px;padding-bottom:10.28px}'  # 46px header, cap ink 11.28px from top and bottom
 '@media(max-width:380px){.ptv-k .pthd,.ptv-k .ptk{grid-template-columns:44px minmax(0,1fr) var(--ptvw,40px)}}'
 '.ptv-k .pthd>.pthx{display:flex;flex-direction:column;align-items:flex-end;gap:3px;white-space:nowrap}.ptv-k .pthx i{display:block;font-style:normal}.ptv-k .pthx0{visibility:hidden}'
 # "NFL" over the slot (the Drafts .dfhn habit, declarations repeated): the strip's own font, absolute on the PLAYER label's line, so on
 # its baseline; ink centred over the slot's ink span by --pthnr (slotForm)
 '.ptv-k .pthd>.pthp{position:relative;white-space:nowrap}.ptv-k .pthn{position:absolute;top:0;right:var(--pthnr,0px);font-style:normal;text-indent:0}'
 '.ptv-k .ptl2>*{flex:none}.ptv-k .ptk{row-gap:0}.ptv-k .ptl2{min-height:20px}'
 '.ptv-k .ptn{grid-column:1;grid-row:1/-1}.ptv-k .ptm{display:contents}'
 '.ptv-k .ptl1{grid-column:2;grid-row:2}.ptv-k .ptl2{grid-column:2;grid-row:3;margin-top:5px}'
 # TIMES TRADED (2026-11-07, light tile): the FAAB tile's colours (--faab fill, --faab-ink figures, --sh-hard: a light element,
 # DESIGN.md 2.12), 4px radius, Barlow 700, on line 1: as tall as line 1's line box (1.15 x --ptnf), figure at line 1's size
 # (Barlow digit cap = Plex cap, .70em); one width per year view (--ptcw = widest digit ink + 2 x 8px), placed by tileSnap.
 # Proportional figures, not tabular: canvas has no tabular-nums, so tabular digits put the "1" up to 1.6px off centre.
 '.ptv-k .ptxn{grid-column:3;grid-row:2;align-self:center;justify-self:end;display:block;box-sizing:border-box;width:var(--ptcw,24px);height:var(--ptch,calc(var(--ptnf,15px) * 1.15));padding:0;position:relative;display:flex;align-items:center;justify-content:center;border-radius:4px;background:var(--faab);box-shadow:var(--sh-hard);'
 'font:700 var(--ptnf,15px)/1 var(--display);line-height:calc(var(--ptnf,15px) * 1.15);font-size:var(--ptcf,var(--ptnf,15px));letter-spacing:0;font-variant-numeric:normal;font-feature-settings:normal;color:var(--faab-ink);font-style:normal;text-align:center;white-space:nowrap}'
 '.ptv-k .ptxn b{display:block;position:relative;font-weight:700;line-height:1;text-box:trim-both cap alphabetic}'
 # 36px Picks logos: the halved Paper Trail ring + shadow, blur scaled 3 -> 4px (offsets stay 1px)
 +('.ptv-k .ptl1 .pav.av{box-shadow:0 0 0 1px var(--line-strong),1px 1px 0 .5px rgba(0,0,0,.4),1px 1px 4px .5px rgba(0,0,0,.25)!important}' if PICKS else '')+
 # NFL slot: the Drafts list's slot type; one line, 11px (slotForm gives the view .ptn1.ptn11): two LEFT-aligned fields, "RD n"
 # inline-block --ptpk wide (widest RD ink + 6px of ink - P's left bearing), "PK n" after it; the box --ptnw wide (widest PK ink end)
 # on the name column's right edge; "UDFA" / "–" start on the RD x; baseline on the team name's (ptxFit, by layout)
 '.ptns{margin-left:auto;padding-left:6px;display:block;font:600 11px/1 var(--display);letter-spacing:.04em;text-transform:uppercase;font-variant-numeric:tabular-nums;color:var(--text-dim);white-space:nowrap}.ptns i{font-style:normal}.ptns i+i:not(.ptbl){margin-left:6px}'  # inline, not flex: the .ptbl marker must sit on the baseline
 '.ptv-k .ptns{position:relative}.ptv-k.ptn1 .ptns{width:var(--ptnw);padding-left:0;text-align:left;margin-right:0;font-size:11px}'
 # drafted rows: the 36px picture beside both lines, line 2 on line 1's first-glyph x (rowFit: --ptlx per row, --ptlg, the logo's top);
 # line 1 = player + NFL logo (6px, line 2's gap); nothing shrinks (nameFit / holdFit read the overflow)
 '.ptv-k .ptk:not(.ptk1) .ptl1{position:relative;padding-left:44px;gap:6px}.ptv-k .ptk:not(.ptk1) .ptl1>.pav{position:absolute;left:0;top:0}.ptv-k .ptk:not(.ptk1) .ptl1>*{flex:none}'
 '.ptv-k .ptk:not(.ptk1) .ptl2{margin-left:var(--ptlx,44px);margin-top:var(--ptlg,5px)}'
 # equal rows: line 1's track as tall as the tile (--ptch) or the 20px NFL logo line; drafted rows' top / bottom tracks --ptkt / --ptkb
 # and every row's height --ptkh from rowFit's row model (nearest ink 12px from both edges, whole points); line 1 baseline -> line 2
 # cap top --ptg1 (10px, both looks: the smallest whole px >= 8 with >= 3px of ink between the lines)
 '.ptv-k{--ptg1:10px}.ptv-k .ptk{position:relative}.ptv-k .ptk:not(.ptk1) .ptl1{min-height:max(var(--ptch,0px),20px)}'
 '.ptv-k .ptk:not(.ptk1){grid-template-rows:var(--ptkt,13px) auto auto var(--ptkb,13px);min-height:0}.ptv-k[style*="--ptkh"] .ptk:not(.ptk1){height:var(--ptkh)}'
 '.ptv-k .ptk1{grid-template-rows:1fr auto auto 1fr;height:var(--ptkh,83px);min-height:0}.ptv-k .ptk1 .ptt{position:relative}.ptv-k .ptk1 .ptl1{position:relative;top:var(--ptfo,0px)}'   # --ptfo: the logo's ring / shadow ink centred, not its box
 # the <= 430 CSS px lever (slotForm's last form): logo-to-name 7px, column gaps 8px
 '.ptv-k.ptgt .pthd,.ptv-k.ptgt .ptk{column-gap:8px}.ptv-k.ptgt .ptk:not(.ptk1) .ptl1{padding-left:43px}.ptv-k.ptgt .ptk1 .ptl1{gap:7px}'
 '.ptv-k .ptvt{display:block;grid-column:3;grid-row:3;justify-self:end;align-self:start;white-space:nowrap;margin-top:0;word-spacing:.5625px;padding:0;border-radius:0;background:none;box-shadow:none;font:600 11px/1 var(--display)!important;letter-spacing:0;text-transform:none;color:var(--text-dim)!important}'
 '.ptv-k .ptvt{position:relative}.ptv-k .ptvt i{font-style:normal;font-weight:600;color:inherit}.ptv-k .ptk1 .ptvt{position:absolute;right:16px;top:0;margin:0}'
 '.ptv-k.ptn1 .ptns i+i:not(.ptbl){margin-left:0}.ptv-k.ptn1 .ptns i:nth-last-child(3){display:inline-block;width:var(--ptpk)}'
 '.ptbl{display:inline-block;width:0;height:0;vertical-align:baseline}'
 '.ptpn{min-width:0}.ptl2{white-space:nowrap}.ptl2 .pav{width:18px;height:18px}.ptl2.ptlo .ptln{display:none}'
 '.ptc{margin-left:auto;flex:none;font:700 12px/1 var(--display);letter-spacing:.04em;color:var(--text-dim);font-style:normal;padding-right:2px}'
 '.ptg{display:flex;align-items:center;justify-content:center;border-left:3px solid var(--pg)}'
 '.ptg .pav{width:28px;height:28px}'
 '.ptfa0{font:700 12px/1 var(--display);letter-spacing:.06em;color:var(--text-dim);font-style:normal}'
 '.ptdt{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-style:normal}'
 '.ptdt i{font:600 var(--ptfdm,11px)/1 var(--display);letter-spacing:.06em;text-transform:uppercase;color:var(--text-dim);font-style:normal;text-box:trim-both cap alphabetic}'
 '.ptdt b{font:700 var(--ptfdd,17px)/1 var(--display);color:var(--chalk);text-box:trim-both cap alphabetic}'
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
 '.ptsl{display:flex;align-items:center;gap:8px;font:400 var(--ptfl,14px)/1.2 var(--body);color:var(--chalk)}.ptsl .pav{width:24px;height:24px}.ptsl b{font-weight:600}'
 '.ptsm{font:400 var(--ptfm,12.5px)/1.35 var(--body);color:var(--text-dim)}'
 '.ptsb{flex:1 1 auto;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;padding-bottom:max(16px,env(safe-area-inset-bottom))}'
 '.ptsy{display:flex;justify-content:space-between;align-items:center;padding:10px 16px 9px;font:700 var(--ptfy,12px)/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim);background:var(--pg)}'
 '.pte{display:grid;grid-template-columns:32px 28px minmax(0,1fr);column-gap:12px;align-items:center;padding:12px 16px;border-top:1px solid var(--row-divider);background:var(--deck)}'
 '.ptsy+.pte{border-top:0}.pte:nth-child(odd){background:var(--row-lt)}'
 '.pte .pav{width:28px;height:28px}.pte .ptfa{visibility:hidden}'
 '.ptx1{min-width:0;display:flex;flex-direction:column;gap:5px}'
 '.pta{font:400 var(--ptf1,14px)/1.25 var(--body);color:var(--chalk)}.pta b{font-weight:600}'
 '.ptb2{font:400 var(--ptf2,12.5px)/1.35 var(--body);color:var(--text-dim)}'
 '.ptr{all:unset;cursor:pointer;color:var(--chalk);text-decoration:underline;text-decoration-color:var(--text-dim);text-underline-offset:2px}'
 '.ptr:focus-visible{outline:2px solid var(--chalk);outline-offset:1px}.ptr0{color:var(--chalk)}'
 '.ptsm .ptr{font-weight:600}'
 # trade step (2026-11-24, brief PT-1e): no line 1 / line 2; the content column holds headed columns, one per team that got
 # something. Row 1 keeps main's height (line 1 14px/1.25 + 5px + line 2 12.5px/1.35 = 39.375px) so the date block and the
 # logo slot do not move; the columns start at the row's content top and span both rows. Head: 18px logo / face + name, Plex
 # 600 12.5px --chalk, the name's box trimmed to cap top / baseline and centred on the 18px picture (a shrunk name keeps the
 # baseline); head margin-top -1.41px puts the name's cap top where line 1's cap top was. A 1px rule under the head (declared
 # --row-divider; readability.css's border rule paints every border --frame, as the sheet's row dividers) with 6px of ink
 # above (the picture's lowest ink = its box + --ptak; no picture: the name's lowest glyph) and below (the first item's
 # highest glyph): gapFit sets the head's padding-bottom and the list's margin-top (the values below are its starting point).
 '.pte.ptet{grid-template-rows:calc(var(--ptf1,14px) * 1.25 + 5px + var(--ptf2,12.5px) * 1.35) auto}.ptet>.ptdt,.ptet>.ptswb{grid-row:1}'
 '.ptxt{grid-column:3;grid-row:1/span 2;align-self:start;min-width:0;display:flex;flex-direction:column}'
 '.ptt3{display:block;font:600 var(--ptf3,11px)/1 var(--display);letter-spacing:.06em;text-transform:uppercase;color:var(--text-dim);text-box:trim-both cap alphabetic;margin:4.23px 0 8px}'
 '.pttr{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:16px;align-items:start}'
 '.pttw,.pttc{display:flex;flex-direction:column;min-width:0}.pttc3{margin-top:12px}'
 '.ptth{display:flex;align-items:flex-start;gap:6px;box-sizing:content-box;height:18px;margin-top:var(--ptthm,-1.41px);padding-bottom:var(--ptthp,7.1px);border-bottom:1px solid var(--row-divider);white-space:nowrap;min-width:0}'
 '.ptth .pav{width:18px;height:18px}.pts{--ptak:0px}'
 +('.pts{--ptak:1.125px}' if PICKS else '')+  # BBP logo: ring + shadow ink 1.125px under its box (WebKitGTK 3x); YILM: its readability.css

 '.ptthn{display:block;font:600 var(--ptfh,12.5px)/1 var(--body);color:var(--chalk);white-space:nowrap;text-box:trim-both cap alphabetic;margin-top:calc(9px - var(--ptfh,12.5px) * var(--ptcap,.698) / 2 + (var(--ptfh,12.5px) - 1em) * var(--ptcap,.698))}'
 '.pttl{display:flex;flex-direction:column;gap:5px;margin-top:var(--pttlm,2.27px)}'
 '.ptti{display:block;font:400 var(--ptfi,12.5px)/1.35 var(--body);color:var(--chalk)}'
 '.pttx{display:block;min-width:0;white-space:nowrap}.pttx.pttwr{white-space:normal}.pttot{white-space:nowrap}.pttx.pttwr2 .pttot{white-space:normal}'
 '.pttx>*{display:inline-block;max-width:none}.pttx.pttwr>*{display:inline}'
 '.pttme{font-weight:600;color:var(--chalk)}.pttno{color:var(--text-dim)}'
 '.pttx>.pttcp,.pttx.pttwr>.pttcp{display:block;font:400 var(--ptfc,11px)/1.3 var(--body);color:var(--text-dim);white-space:normal;margin-top:1px}'
 # swap badge (2026-11-24, V2): the logo slot of a trade row holds the Stats › Trades swap badge (.txsw: its glyph, fill
 # --swap-fill (DESIGN.md 4), glyph --frame, --sh-hard, 4px corner; declarations repeated here, never read from Stats CSS),
 # sized to the 28px logo slot (glyph 14 -> 18px, the badge's ratio), centred where the logo was
 '.ptswb{grid-column:2;width:28px;height:28px;box-sizing:border-box;display:grid;place-items:center;background:var(--swap-fill);box-shadow:var(--sh-hard);border-radius:4px;color:var(--frame);font-style:normal}'
 '.ptswb svg{display:block;width:18px;height:18px}'
 '.ptx .nfl,.pts .nfl{flex:none}'
 # per-type counts (KH only, briefs PT-2d / PT-2e): own line in the summary's style; items unbreakable, lines balanced, the separator
 # is each item's ::before (--ptsep wide: "· " in the site's body font), cut off at every line start by .ptkc's overflow
 # waiver bid (KH only, brief PT-2f): own track between line 1 and the tile; line 1's font, --chalk, 600, tabular figures; the box
 # stops (8px - the last digit's right bearing) before the tile: the column gap is 12px, so margin-right = -4px - --ptrb (site CSS
 # gives --ptrb per last digit, data-d, from its font's outlines), and every bid's last digit ink ends 8px before the tile
 '.pte.ptk-w .pta{text-wrap:balance}'   # the W row's tracks (... max-content tile) are in the site CSS, with --ptkw
 '.ptkf{grid-column:4;align-self:center;position:relative;font:600 var(--ptf1,14px)/1.25 var(--body);color:var(--chalk);font-variant-numeric:tabular-nums;white-space:nowrap;margin-right:calc(-4px - var(--ptrb,0em))}.ptkf b{font-weight:600}'
 '.ptkc{display:block;overflow:hidden}.ptkw{display:block;margin-left:calc(-1 * var(--ptsep,.56em));text-wrap:balance}'
 '.ptkn{white-space:nowrap}.ptkn::before{content:"\\00b7";display:inline-block;width:var(--ptsep,.56em);text-align:left}'
 +yrs_css)
if __name__=='__main__':
    open(P+'paper_section.html','w',encoding='utf-8').write(SEC)
    open(P+'paper_css.css','w',encoding='utf-8').write(CSS)
