import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Builds the "Points by position" section HTML from pos/pos.csv:
# two tables (points per start, season total), each with competition ranks (ties = T), switched by CSS-only radios.
import csv,re,json
P=__DTP__+''
s=open(P+'data_block.js',encoding='utf-8').read()
H=json.loads(re.search(r'const H=(\[.*?\]);',s).group(1))
rows=list(csv.DictReader(open(P+'pos/pos.csv',encoding='utf-8')))
POS=['QB','RB','WR','TE','K','DEF']
def norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip(); return {'RIPMFL':'Team RIPMFL'}.get(n,n)
TOT={norm(r['team']):{p:float(r[p]) for p in POS} for r in rows}
PS={norm(r['team']):{p:float(r[p])/max(1,int(r['starts_'+p])-int(r.get('nogame_'+p) or 0)) for p in POS} for r in rows}
G=int(re.search(r'const G=(\d+);',s).group(1))
PW={t:{p:v/G for p,v in d.items()} for t,d in TOT.items()}
SHORT={"Team Ram Rod":"Ram Rod","Bill's Block Party":"Block Party","Homer's Heroes":"Homer's","Mandingoes":"Mandingoes","Team RIPMFL":"RIPMFL","Cheating is Trying":"Cheating","Convicts":"Convicts","Nuts in the Face":"Nuts","Reverse Apache Master":"Apache","Canton waitlist":"Canton"}
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
tone=lambda r:'gold' if r==1 else 'g' if r<=3 else 'b last' if r==10 else 'b' if r>=8 else ''
def rank(D,p,t):
    v=D[t][p];return 1+sum(D[x][p]>v+1e-9 for x in D),sum(abs(D[x][p]-v)<1e-9 for x in D)>1
def table(D,cls):
    o=[f'<div class="pt {cls}" role="table"><div class="pr ph" role="row"><span role="columnheader">Team</span>'+''.join(f'<span role="columnheader"><i class="pp p-{p.lower()}"><span class="ct">{p}</span></i></span>' for p in POS)+'</div>']
    for i,t in enumerate(H):
        tc='tier-bye' if i<2 else 'tier-po' if i<6 else 'tier-out'
        cells=''.join((lambda r,tie:f'<span role="cell"><b>{D[t][p]:.1f}</b><i class="ch {tone(r)}"><span class="ct">{"T" if tie else "#"}{r}</span></i></span>')(*rank(D,p,t)) for p in POS)
        o.append(f'<div class="pr {tc}" role="row"><span role="rowheader"><em>{i+1}</em>{SHORT[t]}</span>{cells}</div>')
    o.append('</div>');return '\n'.join(o)
NG=[(norm(r['team']),p,int(r.get('nogame_'+p) or 0)) for r in rows for p in POS if int(r.get('nogame_'+p) or 0)]
NOTE=('<p class="ptnote">Per start leaves out starts with no game: '+', '.join(f'{t} {p} ({n} bye start{"s" if n>1 else ""})' for t,p,n in NG)+'.</p>') if NG else ''
html='\n'.join(['<section class="posx" aria-labelledby="posh">',
 '<input type="radio" name="posm" id="pm-start" class="lr" checked><input type="radio" name="posm" id="pm-wk" class="lr"><input type="radio" name="posm" id="pm-tot" class="lr">',
 '<div class="posh"><b id="posh">Points by position</b><div class="pseg" role="group" aria-label="Points by position view"><label for="pm-start">Per start</label><label for="pm-wk">Per week</label><label for="pm-tot">Total</label></div></div>',
 table(PS,'pt-start'),NOTE,table(PW,'pt-wk'),table(TOT,'pt-tot'),'</section>'])
if __name__=='__main__':
    for t in H: print(t,[(p,round(TOT[t][p],1),rank(TOT,p,t)) for p in POS])
open(P+'pos/pos_section.html','w',encoding='utf-8').write(html)
