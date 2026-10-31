# writes po_proj.json, po_home.json and kick.json weeks 15-17 from pull_po.json
import json
d=json.load(open('pull_po.json'));R=json.load(open('rosters.json',encoding='utf-8'))
opp={w:{} for w in d['SCH']}
for w,g in d['SCH'].items():
    for h,a,_,_ in g:opp[w][h]=a;opp[w][a]=h
allp={p[0]:p for t in R.values() for p in t}
P={w:{pid:([d['PO'][w][pid][0],d['PO'][w][pid][1] or opp[w].get(p[3])] if pid in d['PO'][w] else [0.0,opp[w].get(p[3])]) for pid,p in allp.items()} for w in ['15','16','17']}
json.dump(P,open('po_proj.json','w'));json.dump(d['HOME'],open('po_home.json','w'))
k=json.load(open('kick.json'))
for w in ['15','16','17']:k[w]={t:[v[0],'pre'] for t,v in d['KICK'][w].items()}
json.dump(k,open('kick.json','w'));print('ok',len(allp))
