import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Light in-week score update: python3 score.py live.json  (live.json = output of score_pull.js)
import json,sys,subprocess
P=__DTP__+''
L=json.load(open(sys.argv[1]));W=str(L['w'])
wk=json.load(open(P+f'wk{W}.json'));st=json.load(open(P+'stats.json'))
n=0
if 'starters' in L:
    for rid,ids in L['starters'].items():
        X=wk['out'][rid];have={p[0]:p for p in X['st']+X['bn']}
        for i in ids:
            if i not in have and i in L.get('extra',{}):have[i]=list(L['extra'][i])
        X['st']=[have[i] for i in ids if i in have]
        X['bn']=[p for k,p in have.items() if k not in ids]
for rid,X in wk['out'].items():
    for p in X['st']+X['bn']:
        v=L['pp'].get(p[0])
        if v is not None and abs(v-p[5])>1e-9:p[5]=round(v,2);n+=1
    X['pts']=L['tp'].get(rid,X['pts'])
    s=sum(p[5] for p in X['st'])
    assert abs(s-X['pts'])<0.02,(rid,s,X['pts'])
wk['done']=sorted(set(L['done']));wk['live']=sorted(set(L.get('live',[])))
st[W]={k:('x' if v=='0' else v) for k,v in L['S'].items()}
json.dump(wk,open(P+f'wk{W}.json','w'));json.dump(st,open(P+'stats.json','w'),separators=(',',':'))
print('updated',n,'player scores; final teams',wk['done'],'; live',L['live'])
for c in ([] if '--no-build' in sys.argv else (['python3',P+'rebuild.py'],['node',P+'gen.js'],['python3',P+'build_static.py'])):
    subprocess.run(c,check=True,stdout=subprocess.DEVNULL,cwd=P)
print({r:X['pts'] for r,X in wk['out'].items()})
