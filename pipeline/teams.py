import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Mid-week NFL team changes (trades, signings): python3 teams.py  (after `node pull.mjs teams W [full]`, W = G+1)
# Only the weekly pull for a completed week rewrites pull8.json, rosters.json and wk<W>.json; mid-week weekly runs and
# live runs keep the team each player had at that pull (2026-11-12: Josh Downs IND -> KC and Keenan Allen IND -> SF on
# 10 Nov stayed IND, with the Colts' Week 10 opponent). This applies pull_teams.json to the current week only:
#   wk<W>.json rows (team, opponent), pull8.json META team + PJ opponent (when it is week W's), rosters.json team,
#   pull_top.json team. Completed weeks (hist.json, wk<W-1> and earlier) are never touched, and a week-W row whose
#   player already has a stat line this week keeps the team he played for. Never fatal: any error prints and exits 0.
import json,re,sys
P=__DTP__
def main():
    T=json.load(open(P+'pull_teams.json'))
    W=int(T['w']);T=T['T']
    G=int(re.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))
    if W!=G+1:print('teams.py: pull is for week',W,'but the current week is',G+1,'; nothing applied');return
    if not T:print('teams.py: no team data; nothing applied');return
    L=lambda f:json.load(open(P+f,encoding='utf-8'))
    ch=[]
    # wk<W>.json
    f=f'wk{W}.json'
    if _dt_os.path.exists(P+f):
        wk=L(f);st=(L('stats.json') if _dt_os.path.exists(P+'stats.json') else {}).get(str(W),{});n=0
        for rid,X in wk['out'].items():
            for p in X['st']+X['bn']:
                t=T.get(p[0])
                if not t or t[0]==p[3]:continue
                if p[0] in st or p[5]:print('teams.py: kept',p[0],p[2],p[3],'(has a week',W,'stat line)');continue
                ch.append((f,rid,p[0],p[2],p[3],p[6],t[0],t[1]));p[3],p[6]=t[0],t[1];n+=1
        if n:json.dump(wk,open(P+f,'w'))
    # pull8.json: META team; PJ opponent only when its projections are week W's (S8 starts at the week it prepared)
    if _dt_os.path.exists(P+'pull8.json'):
        x=L('pull8.json');n=0;wN=min((s[0] for s in x.get('S8',[])),default=None)
        for id_,m in x['META'].items():
            t=T.get(id_)
            if not m or not t or t[0]==m[2]:continue
            o=x['PJ'].get(id_,[0,None])
            ch.append(('pull8.json','META',id_,m[0],m[2],o[1],t[0],t[1] if wN==W else o[1]));m[2]=t[0];n+=1
            if wN==W and id_ in x['PJ']:x['PJ'][id_][1]=t[1]
        if n:json.dump(x,open(P+'pull8.json','w'))
    # rosters.json
    if _dt_os.path.exists(P+'rosters.json'):
        R=L('rosters.json');n=0
        for k,pl in R.items():
            for p in pl:
                t=T.get(p[0])
                if t and t[0]!=p[3]:ch.append(('rosters.json',k,p[0],p[1],p[3],'',t[0],''));p[3]=t[0];n+=1
        if n:json.dump(R,open(P+'rosters.json','w'),ensure_ascii=False)
    # pull_top.json (Players tab)
    if _dt_os.path.exists(P+'pull_top.json'):
        x=L('pull_top.json');n=0
        for id_,p in x['P'].items():
            t=T.get(id_)
            if t and p[1]!='DEF' and t[0]!=p[2]:ch.append(('pull_top.json','P',id_,p[0],p[2],'',t[0],''));p[2]=t[0];n+=1
        if n:json.dump(x,open(P+'pull_top.json','w'),ensure_ascii=False)
    for c in ch:print('teams.py: %s %s %s %s: %s %s -> %s %s'%c)
    print('teams.py: week',W,',',len(ch),'changes')
try:main()
except Exception as e:print('WARNING teams.py (ignored):',repr(e),file=sys.stderr)
