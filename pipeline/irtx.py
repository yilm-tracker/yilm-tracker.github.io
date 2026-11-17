import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# IR / taxi lists per week (2026-11-17, brief irtaxi). Identical in both repos.
# Sleeper keeps no IR / taxi flag per week: a completed week's matchup lists every rostered player. This file keeps the
# rosters' reserve / taxi lists as each run saw them, so a completed week's best lineup, Bench and bands leave out a player
# who was on IR / taxi when his own game kicked off.
#   irtx.json  {"<week>": {"seed": bool, "s": [[first_seen, last_seen, {"<roster id>": {"ir": [ids], "tx": [ids]}}], ...]}}
#   BBP pipeline/irtx.json; YILM pipeline/history/raw/<year>/irtx.json (season_replay.py copies it into the workspace).
# Rule (out): a player leaves roster r's pool in week w when, in the last snapshot taken before HIS game's kickoff
# (kick.json[w][his NFL team]; no game / bye: the week's first kickoff), he is on r's IR or taxi list. Snapshots more
# than 7 days older than the week's first kickoff are ignored. A Sleeper starter is never left out (NOTE on stderr).
# Seeded weeks (seed: true, rebuilt from git history, BBP / YILM Weeks 8-10 of 2026) also need the first snapshot AFTER
# his kickoff to list him (bracket rule: the history has gaps of days). Weeks without an entry (2026 Weeks 1-7): nothing
# is left out, as before. No file, a bad file or a missing kickoff: nothing is left out. Never raises.
# record() appends the current lists for the coming week; CI runs only (GITHUB_ACTIONS), never into a seeded week, and
# only while a game of that week has not kicked off. Live runs do not commit, so they add nothing that lasts.
import json,sys
from datetime import datetime,timedelta,timezone
P=__DTP__
PATH=_dt_os.environ.get('DT_IRTX') or P+'irtx.json'
_C={}
def _w(*a):print('WARNING irtx:',*a,file=sys.stderr)
def _t(s):
    d=datetime.fromisoformat(s.replace('Z','+00:00'))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
def load():
    if 'd' not in _C:
        d={}
        try:
            if _dt_os.path.exists(PATH):
                for w,v in json.load(open(PATH,encoding='utf-8')).items():
                    d[int(w)]=(bool(v.get('seed')),[(_t(a),_t(b),{str(r):(set(x.get('ir') or []),set(x.get('tx') or [])) for r,x in L.items()}) for a,b,L in v.get('s') or []])
        except Exception as ex:_w('cannot read',PATH,ex);d={}
        _C['d']=d
    return _C['d']
def kicks(w):
    k=_C.setdefault('k',{})
    if w not in k:
        try:
            K=json.load(open(P+'kick.json')).get(str(w)) or {} if _dt_os.path.exists(P+'kick.json') else {}
            k[w]={t:_t(v[0] if isinstance(v,list) else v) for t,v in K.items() if v}
        except Exception as ex:_w('kick.json',ex);k[w]={}
    return k[w]
def out(w,rid,players,starters=()):
    """players: iterable of (player id, NFL team) on roster rid's week-w list; returns {player id: 'IR' | 'TX'} to leave out"""
    try:
        e=load().get(int(w))
        if not e:return {}
        seed,S=e;K=kicks(int(w))
        if not K:_w('no kickoffs for week',w,'- nothing left out');return {}
        first=min(K.values());r=str(rid);o={}
        for pid,tm in players:
            if not pid or pid=='0':continue
            k=K.get(tm) or first
            i=max((j for j,s in enumerate(S) if s[0]<k),default=None)
            if i is None or S[i][1]<first-timedelta(days=7):continue
            ir,tx=S[i][2].get(r,((),()))
            tag='IR' if pid in ir else 'TX' if pid in tx else None
            if not tag:continue
            if seed and S[i][1]<=k:
                if i+1>=len(S):continue
                a=S[i+1][2].get(r,((),()))
                if pid not in a[0] and pid not in a[1]:continue
            if pid in starters:print('NOTE irtx: week',w,'roster',rid,'starter',pid,'is on the',tag,'list; kept',file=sys.stderr);continue
            o[pid]=tag
        return o
    except Exception as ex:
        _w('week',w,'roster',rid,ex);return {}
def record(w,lists,now=None,force=False,path=None):
    """lists: {roster id: {'ir': [ids], 'tx': [ids]}} (Sleeper reserve / taxi) as pulled now, for week w; path: another
    irtx.json (YILM: the repo's history/raw/<year>/ copy)"""
    try:
        if not (force or _dt_os.environ.get('GITHUB_ACTIONS')):return
        now=now or datetime.now(timezone.utc);w=int(w);F=path or PATH
        K=kicks(w)
        if K and now>=max(K.values()):return
        D=json.load(open(F,encoding='utf-8')) if _dt_os.path.exists(F) else {}
        e=D.setdefault(str(w),{'seed':False,'s':[]})
        if e.get('seed'):return
        L={str(r):{'ir':sorted(set(x.get('ir') or [])),'tx':sorted(set(x.get('tx') or []))} for r,x in sorted(lists.items(),key=lambda x:int(x[0]))}
        ts=now.astimezone(timezone.utc).isoformat(timespec='seconds')
        if e['s'] and e['s'][-1][2]==L:e['s'][-1][1]=ts
        else:e['s'].append([ts,ts,L])
        _dt_os.makedirs(_dt_os.path.dirname(F) or '.',exist_ok=True)
        json.dump({k:D[k] for k in sorted(D,key=int)},open(F,'w',encoding='utf-8'),separators=(',',':'))
        _C.pop('d',None)
    except Exception as ex:_w('record week',w,ex)
