# writes po_proj.json, po_home.json and kick.json weeks 15-17 from pull_po.json
import json
d=json.load(open('pull_po.json'));R=json.load(open('rosters.json',encoding='utf-8'))
opp={w:{} for w in d['SCH']}
for w,g in d['SCH'].items():
    for h,a,_,_ in g:opp[w][h]=a;opp[w][a]=h
allp={p[0]:p for t in R.values() for p in t}
P={w:{pid:([d['PO'][w][pid][0],d['PO'][w][pid][1] or opp[w].get(p[3])] if pid in d['PO'][w] else [0.0,opp[w].get(p[3])]) for pid,p in allp.items()} for w in ['15','16','17']}
# Matchups' future weeks (2026-11-13): the rest of the regular season in the same shape (projection, NFL opponent from
# the projection, else from the week's games); kickoffs only for weeks after Sleeper's current week (that week's are
# full_update.py's / midweek.py's), or when kick.json has none for it yet
FPO=d.get('FPO',{});NOW=min((int(w) for w in d.get('FP',{})),default=99)
for w,m in d.get('FP',{}).items():
    if int(w)>=15:continue
    P[w]={pid:[m[pid] if pid in m else 0.0,FPO.get(w,{}).get(pid) or opp.get(w,{}).get(p[3])] for pid,p in allp.items()}
json.dump(P,open('po_proj.json','w'));json.dump(d['HOME'],open('po_home.json','w'))
k=json.load(open('kick.json'))
for w in ['15','16','17']:k[w]={t:[v[0],'pre'] for t,v in d['KICK'][w].items()}
for w,v in d['KICK'].items():
    if int(w)<15 and (int(w)>NOW or w not in k):k[w]={t:[x[0],'pre'] for t,x in v.items()}
json.dump(k,open('kick.json','w'));print('ok',len(allp))
# every remaining week's projections (league scoring) for the player-level season sim: {week: {player: points}}
FP={w:m for w,m in d.get('FP',{}).items()}
for w in ['15','16','17']:FP[w]={pid:v[0] for pid,v in d['PO'][w].items()}
json.dump(FP,open('fut_proj.json','w'))
