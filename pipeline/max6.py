exec(open("w6.py").read().split("teams=list(season)\ndef")[0])
mx[5]={R:221.06,H:186.30,A:140.16,N:119.24,M:129.20,B:114.48,P:110.44,T:105.12,W:88.60,C:96.24}
mx[6]={B:133.90,N:147.44,R:129.20,T:114.02,M:123.86,P:105.88,C:126.72,H:97.30,A:92.20,W:94.84}
teams=list(season); W=range(1,7)
for w in W:
    for t in teams: assert mx[w][t]>=act[w][t]-1e-9,(w,t)
pf={t:sum(act[w][t] for w in W) for t in teams}; mp={t:sum(mx[w][t] for w in W) for t in teams}
rec={t:[0,0] for t in teams}; opt={t:[0,0] for t in teams}; cw={t:[] for t in teams}; cl={t:[] for t in teams}
for w in W:
    for a,b in sched[w]:
        for x,y in((a,b),(b,a)):
            if act[w][x]>act[w][y]:
                rec[x][0]+=1
                if act[w][x]<mx[w][y]: cl[x].append((w,y,act[w][x],mx[w][y]))
            else:
                rec[x][1]+=1
                if mx[w][x]>act[w][y]: cw[x].append((w,y,mx[w][x],act[w][y]))
            if mx[w][x]>mx[w][y]: opt[x][0]+=1
            else: opt[x][1]+=1
print("EFF")
for t in sorted(teams,key=lambda t:-pf[t]/mp[t]):
    print(f"{t:22} PF {pf[t]:.2f} MAX {mp[t]:.2f} gap {mp[t]-pf[t]:.2f} gap/wk {(mp[t]-pf[t])/6:.2f} eff {pf[t]/mp[t]*100:.1f}%")
print("OPT")
for t in sorted(teams,key=lambda t:(-opt[t][0],-mp[t])): print(t,opt[t],rec[t])
print("CW/CL")
for t in sorted(teams,key=lambda t:(-rec[t][0],-pf[t])): print(t,rec[t],len(cw[t]),len(cl[t]),cw[t],cl[t])
print("wk eff",[(w,{t:round(act[w][t]/mx[w][t]*100,1) for t in teams}) for w in (5,6)])
