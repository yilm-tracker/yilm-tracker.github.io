import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Lineups for a week not yet played, shared by the Playoffs builder (po_build.py, Weeks 15-17) and Matchups' future weeks
# (mu_build.py, the remaining regular-season weeks; 2026-11-13, brief A5). Moved out of po_build.py unchanged, except:
#   proj()  a week the Playoffs pull (po_proj.json) does not cover yet reads fut_proj.json (the season sim's Sleeper
#           projections, points only) before falling back to points per game
#   mp()    a team with no game in a week whose NFL games are known (kick.json) is on bye: no opponent (BYE), not "TBD"
# Identical in both repos.
import json,re,os
P=__DTP__+''
_s=open(P+'data_block.js',encoding='utf-8').read()
_g=lambda n:json.loads(re.search(r'const '+n+r'=(.*?);\n',_s).group(1))
H,WK=_g('H'),_g('WK');G=len(WK[H[0]])
def norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip();return {'RIPMFL':'Team RIPMFL'}.get(n,n)
R={norm(k):v for k,v in json.load(open(P+'rosters.json',encoding='utf-8')).items()}
A=json.load(open(P+'pull_pts.json'))
INJM={}
if os.path.exists(P+'pull8.json'):
    for pid,m in json.load(open(P+'pull8.json'))['META'].items():
        if m and m[3]:INJM[pid]=m[3]
PROJ=json.load(open(P+'po_proj.json')) if os.path.exists(P+'po_proj.json') else None
FPJ=json.load(open(P+'fut_proj.json')) if os.path.exists(P+'fut_proj.json') else {}
HOMEW=json.load(open(P+'po_home.json')) if os.path.exists(P+'po_home.json') else {}
KICK=json.load(open(P+'kick.json')) if os.path.exists(P+'kick.json') else {}
RID={v:int(k) for k,v in json.load(open(P+'cmp_extra.json',encoding='utf-8'))['rn'].items()}
_W8=json.load(open(P+f'wk{G+1}.json'))
def ppg(pid):
    a=A.get(pid)
    if not a:return 0.0,0
    gp=a[3][:G].count('1');tot=sum(v for v in a[2][:G] if v is not None)
    return (round(tot/gp,2) if gp else 0.0),gp
def proj(pid,w):
    if PROJ and str(w) in PROJ and pid in PROJ[str(w)]:return PROJ[str(w)][pid][0],PROJ[str(w)][pid][1]
    if not (PROJ and str(w) in PROJ) and pid in FPJ.get(str(w),{}):return float(FPJ[str(w)][pid]),None
    return ppg(pid)[0],None
def src(w):
    """the projection source of week w, as the lineup note says it"""
    return 'Sleeper projections' if (PROJ and str(w) in PROJ) or str(w) in FPJ else f'projection = points per game, Weeks 1–{G} until Sleeper projections are pulled'
def pool(t,w):
    out=[]
    for p in R[t]:
        if p[7] in('IR','TX'):continue
        v,opp=proj(p[0],w);out.append(dict(pid=p[0],name=p[1],pos=p[2],nfl=p[3],pj=v,opp=opp,gp=ppg(p[0])[1],inj=INJM.get(p[0])))
    return out
def bye(nfl,w):
    """the NFL team has no game in week w (only when that week's games are known)"""
    return bool(nfl) and str(w) in KICK and nfl not in KICK[str(w)]
def mp(q,w):
    """player dict -> Matchups row format [pid,pos,name,nfl,proj,act,opp,inj,done,ha,week]"""
    if q is None:return None
    if q['opp']:ha='vs' if q['nfl'] in HOMEW.get(str(w),[]) else '@';opp=q['opp']
    elif bye(q['nfl'],w):ha='';opp=None
    else:ha='';opp='TBD'
    return [q['pid'],q['pos'],q['name'],q['nfl'],q['pj'],0,opp,q['inj'],False,ha,w]
def setlineup(t,w):
    """the team's lineup as currently set in Sleeper, re-projected for week w"""
    pl={q['pid']:q for q in pool(t,w)}
    allp={p[0]:p for p in R[t]}
    out=[]
    for x in _W8['out'][str(RID[t])]['st']:
        pid=x[0]
        if pid in pl:out.append(pl[pid])
        elif pid in allp:
            p=allp[pid];v,opp=proj(pid,w);out.append(dict(pid=pid,name=p[1],pos=p[2],nfl=p[3],pj=v,opp=opp,gp=ppg(pid)[1],inj=INJM.get(pid)))
        else:out.append(None)
    return out
