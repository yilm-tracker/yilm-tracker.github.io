import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Light in-week score update: python3 score.py live.json  (live.json = output of score_pull.js)
import json,sys,subprocess
P=__DTP__+''
L=json.load(open(sys.argv[1]));W=str(L['w'])
wk=json.load(open(P+f'wk{W}.json'));st=json.load(open(P+'stats.json'))
n=0
if 'starters' in L:
    # A starter may be missing from his roster's rows: added after wk{W}.json was written, possibly from another
    # roster (2026-11-08: Malik Washington, dropped by roster 1 and added by roster 7, still on roster 1's bench in
    # wk9.json, so pullLive did not send him as extra and roster 7 was 3.10 short). Take his row from the roster that
    # still lists him (and take it off there), else from extra, else a minimal row; never drop a starter.
    rows={p[0]:(r,p) for r,X in wk['out'].items() for p in X['st']+X['bn']}
    ST={r:set(i for i in ids if i and i!='0') for r,ids in L['starters'].items()}
    for rid,ids in L['starters'].items():
        X=wk['out'][rid];have={p[0]:p for p in X['st']+X['bn']}
        for i in ids:
            if not i or i=='0' or i in have:continue
            if i in L.get('extra',{}):have[i]=list(L['extra'][i])
            elif i in rows:
                r0,p0=rows[i];have[i]=list(p0)
                if i not in ST.get(r0,()):Y=wk['out'][r0];Y['bn']=[p for p in Y['bn'] if p[0]!=i]
            else:have[i]=[i,'','Player '+i,'',0,0,None,None];print('WARNING score.py: no data for starter',i,'of roster',rid,file=sys.stderr)
        X['st']=[have[i] for i in ids if i in have]
        X['bn']=[p for k,p in have.items() if k not in ids]
for rid,X in wk['out'].items():
    for p in X['st']+X['bn']:
        v=L['pp'].get(p[0])
        if v is not None and abs(v-p[5])>1e-9:p[5]=round(v,2);n+=1
    X['pts']=L['tp'].get(rid,X['pts'])  # Sleeper's team total is authoritative
    s=round(sum(p[5] for p in X['st']),2)
    if abs(s-X['pts'])>=0.02:  # warn, never stop the build (a failed live run freezes the site)
        ids=L.get('starters',{}).get(rid,[]);got={p[0] for p in X['st']}
        print('WARNING score.py: roster',rid,'starters sum',s,'!= Sleeper total',X['pts'],
              '; starter ids without a row:',[i for i in ids if i and i!='0' and i not in got],
              '; without points:',[i for i in ids if i and i!='0' and i not in L['pp']],file=sys.stderr)
wk['done']=sorted(set(L['done']));wk['live']=sorted(set(L.get('live',[])));wk['left']=L.get('left',{})
st[W]={k:('x' if v=='0' else v) for k,v in L['S'].items()}
json.dump(wk,open(P+f'wk{W}.json','w'));json.dump(st,open(P+'stats.json','w'),separators=(',',':'))
print('updated',n,'player scores; final teams',wk['done'],'; live',L['live'])
for c in ([] if '--no-build' in sys.argv else (['python3',P+'rebuild.py'],['node',P+'gen.js'],['python3',P+'build_static.py'])):
    subprocess.run(c,check=True,stdout=subprocess.DEVNULL,cwd=P)
print({r:X['pts'] for r,X in wk['out'].items()})
