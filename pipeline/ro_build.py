import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Builds the "Rosters" section from rosters.json (Sleeper current rosters; season points with league scoring, weeks 1-6)
# and ro_ranks.json (competition rank among all NFL players at the position). CSS-only team switcher.
import json,re,html
P=__DTP__+''
s=open(P+'data_block.js',encoding='utf-8').read()
H=json.loads(re.search(r'const H=(\[.*?\]);',s).group(1))
R=json.load(open(P+'rosters.json',encoding='utf-8'))
K=json.load(open(P+'ro_ranks.json',encoding='utf-8'))
def norm(n):
    n=n.replace('’',"'").replace(' 👑','').strip(); return {'RIPMFL':'Team RIPMFL'}.get(n,n)
R={norm(k):v for k,v in R.items()}
assert set(R)==set(H),set(R)^set(H)
SHORT={"Team Ram Rod":"Ram Rod","Bill's Block Party":"Block Party","Homer's Heroes":"Homer's","Mandingoes":"Mandingoes","Team RIPMFL":"RIPMFL","Cheating is Trying":"Cheating","Convicts":"Convicts","Nuts in the Face":"Nuts","Reverse Apache Master":"Apache","Canton waitlist":"Canton"}
SHORT0=dict(SHORT);SHORT={k:k for k in SHORT}  # full team names everywhere; SHORT0 keeps the data-file short names
ORD=['QB','RB','WR','TE','K','DEF']
e=html.escape
import sys;sys.path.insert(0,P);from nfl_colors import badge_c as badge,NFL_CSS,team_tiles
IRX='<svg class="irx" viewBox="0 0 12 12" role="img" aria-label="Injured reserve"><rect width="12" height="12" rx="3" fill="#ff5d73"/><path d="M6 2.6v6.8M2.6 6h6.8" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg>'
BYE=K.pop('_bye')
from datetime import date
AGE=json.load(open(P+'cmp_extra.json',encoding='utf-8'))['age']
def age(pid):
    b=AGE.get(pid)
    if not b:return None
    y,m,d=map(int,b.split('-'));return (date.today()-date(y,m,d)).days/365.25
def acl(a):return 'ay' if a<27 else 'ap' if a<31 else 'ao'
def gavg(g):
    v=[age(p[0]) for p in g if age(p[0])]
    return f'<i class="ga">Avg age <b class="{acl(sum(v)/len(v))}">{sum(v)/len(v):.1f}</b></i>' if v else ''
import re as _r1
DONE=int(_r1.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))
NAMES={'QB':'Quarterbacks','RB':'Running backs','WR':'Wide receivers','TE':'Tight ends','K':'Kickers','DEF':'Defense'}
TXC='<i class="txc">Taxi</i>'
def nmh(name,pos):
    parts=name.split(' ',1)
    if pos=='DEF' or len(parts)<2 or len(name)<14:return f'<span class="nmx">{e(name)}</span>'
    return f'<span class="nmx lg"><span class="fn">{e(parts[0])} </span><span class="fi">{e(parts[0][0])}. </span>{e(parts[1])}</span>'
PG=json.load(open(P+'ro_pg.json'))
from assess import assess_html as _AS
def prow(pid,name,pos,nfl,pts,gp,tag='',flat=False,pgm=False):
    rk,tie,pts2=K[pid] if K.get(pid) else (None,0,0.0)
    assert abs(pts2-pts)<0.006,(pid,pts,pts2)
    lab=f'{pos}{rk}' if pts>0 else pos
    by=BYE.get(nfl);bc='past' if by and by<=DONE else 'now' if by==DONE+1 else ''
    byh=f'<i class="by {bc}">(<b>{by}</b>)</i>' if by else ''
    pg=f'{pts/gp:.1f}' if gp else '–'
    if pgm: rk=PG[pid][0] if PG.get(pid) else None
    big=rk and (rk>=100 or (pos=='DEF' and rk>=10))
    sq=f'<i class="pq p-{pos.lower()}{" l3" if big and pts>0 else ""} t-{nfl or "FA"}"><span class="pqi"><span>{pos}</span>{f"<b>{rk}</b>" if pts>0 and rk else ""}</span></i>'
    a=age(pid);ag=f'<em class="pag {acl(a)}">{a:.1f}</em>' if a else ''
    return (f'<div class="rr2">{sq}'
            f'<span class="rn"><b>{nmh(name,pos)}{badge(nfl).replace('<em class="nfl','<em class="nfl tm',1) if nfl else ""}{ag}{IRX if tag=="IR" else ""}{TXC if (tag=="TX" and flat) else ""}</b><small><span class="gp">{gp} GP</span>{byh}</small></span>'
            f'<span class="rv">{pts:.1f}</span><span class="rg2">{pg}</span></div>')
def panel(i,t):
    pl=sorted(R[t],key=lambda p:(ORD.index(p[2]),-p[4],p[1]))
    act=[p for p in pl if not p[7]];ir=[p for p in pl if p[7]=='IR'];tx=[p for p in pl if p[7]=='TX']
    o=[f'<div class="rop rop-{i}" role="tabpanel" aria-label="{e(t)} roster">',
       f'<div class="rtop"><b>{e(t)}</b><span><b>{len(act)}</b> active<i>·</i><b>{len(ir)}</b> IR<i>·</i><b>{len(tx)}</b> taxi</span></div>',
       '<div class="rcol"><span>Player</span><span>Pts</span><span>/g</span></div>']
    pgk=lambda p:p[4]/p[6] if p[6] else -1
    for sk in ('p','g'):
        gm=sk=='g';srt=(lambda g:sorted(g,key=lambda p:(-pgk(p),-p[4],p[1]))) if gm else (lambda g:g)
        tot=(lambda g:f'{sum(pgk(p) for p in g if p[6]):.1f}<small>pts/g</small>') if gm else (lambda g:f'{sum(p[4] for p in g):.1f}<small>pts</small>')
        o.append(f'<div class="rbpos rbpos-{sk}">')
        for pos in ORD:
            g=[p for p in act if p[2]==pos]
            if not g: continue
            o.append(f'<div class="rgh p-{pos.lower()}"><span>{NAMES[pos]}<em>{len(g)}</em>{gavg(g)}</span><b>{tot(g)}</b></div>')
            o+= [prow(p[0],p[1],p[2],p[3],p[4],p[6],p[7],pgm=gm) for p in srt(g)]
        for lab,g,c in (('Injured reserve',ir,'ir'),('Taxi squad',tx,'tx')):
            if not g: continue
            o.append(f'<div class="rgh p-{c}"><span>{lab}<em>{len(g)}</em>{gavg(g)}</span><b>{tot(g)}</b></div>')
            o+= [prow(p[0],p[1],p[2],p[3],p[4],p[6],p[7],pgm=gm) for p in srt(g)]
        o.append('</div>')
    pg=lambda p:p[4]/p[6] if p[6] else -1
    for sk,key in (('p',lambda p:(-p[4],p[1])),('g',lambda p:(-pg(p),-p[4],p[1]))):
        for qk,keep in (('a',lambda p:True),('n',lambda p:p[2]!='QB')):
            o.append(f'<div class="rbl rbl-{qk}{sk}">')
            o+= [prow(p[0],p[1],p[2],p[3],p[4],p[6],p[7],True,sk=='g') for p in sorted(pl,key=key) if keep(p)]
            o.append('</div>')
    o.append(_AS(t)+'</div>');return ''.join(o)
radios='<input type="radio" name="rcol" id="rc-p" class="lr" checked><input type="radio" name="rcol" id="rc-t" class="lr"><input type="radio" name="rview" id="rv-pos" class="lr" checked><input type="radio" name="rview" id="rv-pts" class="lr"><input type="radio" name="rq" id="rq-all" class="lr" checked><input type="radio" name="rq" id="rq-noqb" class="lr"><input type="radio" name="rsort" id="rs-p" class="lr" checked><input type="radio" name="rsort" id="rs-g" class="lr">'+''.join(f'<input type="radio" name="ros" id="ro-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(10))
chips='<div class="roc rogd" role="tablist" aria-label="Team">'+''.join(f'<label for="ro-{i}"><em class="rrk">{i+1}</em><span>{e(SHORT[t])}</span></label>' for i,t in enumerate(H))+'</div>'
CTRL=('<div class="rctl lctl lgrid">'
      '<div class="pseg rcseg" role="group" aria-label="Tile colors"><label for="rc-p">Position</label><label for="rc-t">Team</label></div><i class="lt">Colors</i>'
      '<i class="lt ltr">Order</i><div class="pseg rseg" role="group" aria-label="Roster view"><label for="rv-pos">Position</label><label for="rv-pts">Points</label></div>'
      '<div class="pseg rqseg rqf" role="group" aria-label="Filter"><label for="rq-all">All</label><label for="rq-noqb">No QBs</label></div><i class="lt rqt">Filter</i>'
      '<i class="lt ltr">Sort</i><div class="pseg rqseg rsseg" role="group" aria-label="Sort"><label for="rs-p">Pts</label><label for="rs-g">/ Gm</label></div></div>')
sec=('<section class="rox" aria-labelledby="roh">'+radios+
     '<div class="posh"><b id="roh">Rosters</b></div><div class="rsub">Tile = position rank by <span class="rs-pt">points</span><span class="rs-pg">points per game</span> · Wk 1–'+str(DONE)+'</div>'+chips+CTRL+
     ''.join(panel(i,t) for i,t in enumerate(H))+'</section>')
css=''.join(f'#ro-{i}:checked~.roc label[for="ro-{i}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#ro-{i}:checked~.rop-{i}{{display:block}}' for i in range(10))
sel=lambda pairs:','.join(f'#{i}:checked~.rctl label[for="{i}"]' for i in pairs)
css+=(sel(['rv-pos','rv-pts','rs-p','rs-g','rc-p','rc-t','rq-all','rq-noqb'])+'{background:var(--chalk);color:var(--ink)}'
      '.rox .rctl .pseg{display:grid!important;margin:0!important}'
      '.rox .rctl .rqf,.rox .rctl .rqt{visibility:hidden}#rv-pts:checked~.rctl .rqf,#rv-pts:checked~.rctl .rqt{visibility:visible}'
      '.rox .rogd{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;margin:2px 0 12px}'
      
      '.rox .rogd label{display:flex;align-items:center;gap:7px;min-height:36px;padding:6px 10px;box-sizing:border-box;border-radius:6px;border:1px solid var(--hair);background:var(--ink);cursor:pointer;'
      'font-family:var(--display);font-weight:700;font-size:13.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--label);white-space:nowrap;min-width:0}'
      '.rox .rogd label span{overflow:hidden;text-overflow:ellipsis;min-width:0}'
      '@media(max-width:429px){.rox .rogd label{font-size:12.5px;letter-spacing:.02em;padding:6px 8px;gap:6px}}@media(max-width:374px){.rox .rogd label{font-size:11.5px;letter-spacing:.01em;padding:6px 6px;gap:5px}}'
      '.rox .rogd .rrk{font-style:normal;flex:none;min-width:1.2em;text-align:right;color:var(--steel);font-variant-numeric:tabular-nums}'
      +''.join(f'#ro-{i}:checked~.roc label[for="ro-{i}"] .rrk{{color:var(--ink);opacity:.55}}' for i in range(10))
      +team_tiles('#rc-t:checked~.rop'))
open(P+'ro_section.html','w',encoding='utf-8').write(sec)
open(P+'ro_css.css','w',encoding='utf-8').write(css)
if __name__=='__main__':
    for t in H: print(SHORT[t],len(R[t]),round(sum(p[4] for p in R[t]),2))
