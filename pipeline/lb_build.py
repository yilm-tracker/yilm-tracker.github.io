import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Builds the "Leaderboard" section: pick a stat, see all 10 teams ranked by it (CSS-only radios, works without JS).
import json,re,csv
P=__DTP__+''
s=open(P+'data_block.js',encoding='utf-8').read()
T=json.loads(re.search(r'const T=(\{.*?\});',s).group(1))
G=int(re.search(r'const G=(\d+);',s).group(1))
EF=json.load(open(P+'eff.json'));SKr=json.load(open(P+'skill_opt.json'));SKr.pop('_note',None)
rows=list(csv.DictReader(open(P+'pos/pos.csv',encoding='utf-8')))
nm=lambda n:{'RIPMFL':'Team RIPMFL'}.get(n.replace('’',"'").replace(' \U0001F451','').strip(),n.replace('’',"'").replace(' \U0001F451','').strip())
PS={nm(r['team']):{p:float(r[p])/max(1,int(r['starts_'+p])-int(r.get('nogame_'+p) or 0)) for p in ['QB','RB','WR','TE','K','DEF']} for r in rows}
sg=lambda v:('+' if v>0 else '−' if v<0 else '')+f"{abs(v):.2f}"
# key, label, value fn, display fn, low_is_rank1
STATS=[
 ('pf','PF',lambda t:T[t][3],lambda t:f"{T[t][3]:.2f}",False),
 ('pa','PA',lambda t:T[t][6],lambda t:f"{T[t][6]:.2f}",False),
 ('max','Max PF',lambda t:EF[t][3],lambda t:f"{EF[t][3]:.2f}",False),
 ('ap','All-play',lambda t:T[t][10],lambda t:f"{T[t][10]}-{T[t][11]}",False),
 ('xw','xW',lambda t:T[t][10]/(T[t][10]+T[t][11])*G,lambda t:f"{T[t][10]/(T[t][10]+T[t][11])*G:.2f}",False),
 ('luck','Luck',lambda t:T[t][12],lambda t:sg(T[t][12]),False),
 ('opp','Opp rk',lambda t:T[t][9],lambda t:f"{T[t][9]:.1f}",True),
 ('eff','Eff',lambda t:EF[t][0],lambda t:f"{EF[t][0]:.1f}%",False),
 ('skill','Skill',lambda t:SKr[t]['act']/SKr[t]['opt']*100,lambda t:f"{SKr[t]['act']/SKr[t]['opt']*100:.1f}%",False),
]+[(p.lower(),p,(lambda p:lambda t:PS[t][p])(p),(lambda p:lambda t:f"{PS[t][p]:.1f}")(p),False) for p in ['QB','RB','WR','TE','K','DEF']]
DESC={'pf':'Points for, season total','pa':'Points against, season total','max':'Best possible lineup points, season total','ap':'Record if you played every team every week','xw':'Expected wins from all-play win %','luck':'Actual wins minus expected wins','opp':'Average weekly rank of opponent score (#1 = hardest schedule)','eff':'Actual PF as a share of Max PF','skill':'RB/WR/TE/FLEX points as a share of the best combo on the roster','qb':'QB points per start','rb':'RB points per start','wr':'WR points per start','te':'TE points per start','k':'K points per start','def':'DEF points per start'}
tone=lambda r:'gold' if r==1 else 'g' if r<=3 else 'b last' if r==10 else 'b' if r>=8 else ''
teams=list(T)
out=['<section class="lbx" aria-labelledby="lbh">',''.join(f'<input type="radio" name="lbm" id="lb-{k}" class="lr"{" checked" if i==0 else ""}>' for i,(k,*_) in enumerate(STATS)),
 '<div class="posh"><b id="lbh">Leaderboard</b></div>',
 '<div class="lbc" role="group" aria-label="Stat">'+''.join(f'<label for="lb-{k}">{lab}</label>' for k,lab,*_ in STATS)+'</div>']
css=[]
for k,lab,f,disp,low in STATS:
    vals={t:f(t) for t in teams}
    order=sorted(teams,key=lambda t:(vals[t] if low else -vals[t],-T[t][3]))
    rk=lambda t:1+sum((vals[x]<vals[t]-1e-9) if low else (vals[x]>vals[t]+1e-9) for x in teams)
    tie=lambda t:sum(abs(vals[x]-vals[t])<1e-9 for x in teams)>1
    rws=''.join(f'<div class="lbr"><i class="ch {tone(rk(t))}"><span class="ct">{"T" if tie(t) else "#"}{rk(t)}</span></i><span class="lbn">{t}</span><span class="lbv">{disp(t)}</span></div>' for t in order)
    out.append(f'<div class="lbt lbt-{k}"><div class="lbd">{DESC[k]}</div>{rws}</div>')
    css.append(f'#lb-{k}:checked~.lbc label[for="lb-{k}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#lb-{k}:checked~.lbt-{k}{{display:block}}')
out.append('</section>')
open(P+'lb_section.html','w',encoding='utf-8').write('\n'.join(out))
open(P+'lb_css.css','w',encoding='utf-8').write('\n'.join(css))
if __name__=='__main__':
    print(len(STATS),'stats')
