#!/usr/bin/env python3
"""Seed irtx.json from git history (2026-11-17, brief irtaxi; identical in both repos). One-off, for completed weeks that
were played before irtx.record() existed.
  python3 tools/irtx_seed.py <kick.json> <week> [<week> ...] [--skip <sha>]...
Observations = commits that changed the rosters' IR / taxi source (BBP pipeline/rosters.json tags IR / TX, written by the
weekly / daily runs; YILM pipeline/history/raw/<year>/core.json.gz rosters reserve / taxi, the CI capture), each at its
commit time. For week W it keeps every observation from 7 days before W's first kickoff to the first one after W's last
kickoff, merges identical neighbours into [first_seen, last_seen, lists] and marks the week seed: true (irtx.out then also
needs the snapshot after a player's game to list him). Weeks with no observation before any kickoff are left out.
Existing non-seeded weeks in the file are kept. Needs the history: git fetch --depth=1000 origin main (never --unshallow)."""
import sys,os,json,gzip,io,subprocess
from datetime import datetime,timedelta,timezone
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a=sys.argv[1:];skip=set()
while '--skip' in a:i=a.index('--skip');skip.add(a[i+1]);del a[i:i+2]
KICK=json.load(open(a[0]));WEEKS=[int(x) for x in a[1:]]
def git(*x,b=False):
    r=subprocess.run(['git','-C',REPO,*x],capture_output=True,check=True);return r.stdout if b else r.stdout.decode()
T=lambda s:datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(timezone.utc)
YILM=os.path.exists(os.path.join(REPO,'pipeline','seasons.json'))
if YILM:
    CFG=json.load(open(os.path.join(REPO,'pipeline','seasons.json')));Y=CFG['current'];LID=CFG['leagues'][Y]
    SRC=f'pipeline/history/raw/{Y}/core.json.gz';OUT=os.path.join(REPO,'pipeline','history','raw',Y,'irtx.json')
    def lists(h):
        C=json.load(gzip.open(io.BytesIO(git('show',f'{h}:{SRC}',b=True))))
        return {str(r['roster_id']):{'ir':sorted(set(r.get('reserve') or [])),'tx':sorted(set(r.get('taxi') or []))} for r in C[f'https://api.sleeper.app/v1/league/{LID}/rosters']}
else:
    SRC='pipeline/rosters.json';OUT=os.path.join(REPO,'pipeline','irtx.json')
    RID={"Convicts":1,"Homer's Heroes":2,"Team Ram Rod":3,"Team RIPMFL":4,"Reverse Apache Master":5,"Canton waitlist":6,"Nuts in the Face":7,"Bill's Block Party":8,"Mandingoes":9,"Cheating is Trying":10}
    def lists(h):
        R=json.loads(git('show',f'{h}:{SRC}'));o={}
        for k,pl in R.items():
            n=k.replace('’',"'").replace(' 👑','').strip();n={'RIPMFL':'Team RIPMFL'}.get(n,n)
            o[str(RID[n])]={'ir':sorted({p[0] for p in pl if len(p)>7 and p[7]=='IR'}),'tx':sorted({p[0] for p in pl if len(p)>7 and p[7]=='TX'})}
        return dict(sorted(o.items(),key=lambda x:int(x[0])))
OBS=[]
for ln in git('log','--format=%H %cI','HEAD','--',SRC).splitlines():
    h,t=ln.split()
    if any(h.startswith(s) for s in skip):continue
    OBS.append((T(t),h))
OBS.sort()
D=json.load(open(OUT)) if os.path.exists(OUT) else {}
for w in WEEKS:
    K=[T(v[0] if isinstance(v,list) else v) for v in KICK[str(w)].values() if v]
    f,l=min(K),max(K)
    after=[o for o in OBS if o[0]>l][:1]
    sel=[o for o in OBS if f-timedelta(days=7)<=o[0]<=l]+after
    if not any(o[0]<l for o in sel):print('week',w,': no observation before its last kickoff, left out');continue
    S=[]
    for t,h in sel:
        L=lists(h);ts=t.isoformat(timespec='seconds')
        if S and S[-1][2]==L:S[-1][1]=ts
        else:S.append([ts,ts,L])
    D[str(w)]={'seed':True,'s':S}
    print('week',w,'first kickoff',f.isoformat(),'| observations',len(sel),[(t.isoformat(timespec='minutes'),h[:7]) for t,h in sel],'| entries',len(S))
os.makedirs(os.path.dirname(OUT),exist_ok=True)
json.dump({k:D[k] for k in sorted(D,key=int)},open(OUT,'w',encoding='utf-8'),separators=(',',':'))
print('wrote',OUT)
