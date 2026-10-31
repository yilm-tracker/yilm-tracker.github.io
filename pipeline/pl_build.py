import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Builds the "Players" tab: top 50 NFL players at each position (rostered or not) by season points or points per game,
# with games played, bye, fantasy owner and a season stat line. Data: pull_top.json (node pull.mjs top D).
# CSS-only: position radios (pl-qb..pl-def) and sort radios (pl-sp / pl-sg); rows carry both ranks and are reordered with
# CSS order, rows outside the top 50 for the active sort are hidden.
import json,html,math
from datetime import date
P=__DTP__
e=html.escape
X=json.load(open(P+'pull_top.json',encoding='utf-8'))
D,MIN,PL=X['D'],X['minGp'],X['P']
import sys;sys.path.insert(0,P);from nfl_colors import badge_c as badge,NFLC,team_tiles
BYE=json.load(open(P+'ro_ranks.json',encoding='utf-8')).get('_bye',{})
RN={int(k):v for k,v in json.load(open(P+'cmp_extra.json',encoding='utf-8'))['rn'].items()}
SHORT0={"Team Ram Rod":"Ram Rod","Bill's Block Party":"Block Party","Homer's Heroes":"Homer's","Mandingoes":"Mandingoes","Team RIPMFL":"RIPMFL","Cheating is Trying":"Cheating","Convicts":"Convicts","Nuts in the Face":"Nuts","Reverse Apache Master":"Apache","Canton waitlist":"Canton"}
ORD=['QB','RB','WR','TE','K','DEF'];TOP=50
NAMES={'QB':'Quarterbacks','RB':'Running backs','WR':'Wide receivers','TE':'Tight ends','K':'Kickers','DEF':'Defenses'}
def nmh(name,pos):
    parts=name.split(' ',1)
    if pos=='DEF' and len(parts)==2 or pos=='DEF' and name.count(' ')>=1:
        city,nick=name.rsplit(' ',1);return f'<span class="nmx"><span class="dc">{e(city)} </span>{e(nick)}</span>'
    if len(parts)<2 or len(name)<14:return f'<span class="nmx">{e(name)}</span>'
    return f'<span class="nmx lg"><span class="fn">{e(parts[0])} </span><span class="fi">{e(parts[0][0])}. </span>{e(parts[1])}</span>'
def age(b):
    if not b:return None
    y,m,d=map(int,b.split('-'));return (date.today()-date(y,m,d)).days/365.25
def acl(a):return 'ay' if a<27 else 'ap' if a<31 else 'ao'
def n(v):v=v or 0;return str(int(v)) if float(v).is_integer() else f'{v:.1f}'
def nn(x):return f'(−{n(-x)})' if x<0 else n(x)
def grp(lab,nums):return f'<span class="sit"><u>{lab}</u> {"-".join(nn(x) for x in nums)}</span>'
def td3(a,b,c):return [a,b]+([c] if c else [])
def statline(pos,t,gp):
    """Labelled season grid, 2 rows x 5 (Sleeper-style). Rates are computed from season totals; '–' when undefined."""
    g=lambda k:t.get(k,0) or 0
    r=lambda a,b,f='{:.1f}':(f.format(a/b) if b else '–')
    pc=lambda a,b:(f'{100*a/b:.0f}%' if b else '–')
    fr=lambda m,a:f'{n(m)}/{n(a)}'
    snp=pc(g('off_snp'),g('tm_off_snp'))
    lng=lambda k:n(g(k)) if g(k) else '–'
    if pos=='QB':
        c=[('SNP%',snp),('CMP/ATT',fr(g('pass_cmp'),g('pass_att'))),('CMP%',pc(g('pass_cmp'),g('pass_att'))),('PASS YD',n(g('pass_yd'))),('PASS TD',n(g('pass_td'))),
           ('INT',n(g('pass_int'))),('YD/ATT',r(g('pass_yd'),g('pass_att'))),('SACKED',n(g('pass_sack'))),('RUSH YD',nn(g('rush_yd'))),('RUSH TD',n(g('rush_td')))]
    elif pos=='RB':
        c=[('SNP%',snp),('RUSH',n(g('rush_att'))),('RUSH YD',nn(g('rush_yd'))),('YD/CAR',r(g('rush_yd'),g('rush_att'))),('RUSH TD',n(g('rush_td'))),
           ('TGT',n(g('rec_tgt'))),('REC',n(g('rec'))),('REC YD',nn(g('rec_yd'))),('REC TD',n(g('rec_td'))),('FUM',n(g('fum_lost')))]
    elif pos in('WR','TE'):
        c=[('SNP%',snp),('TGT',n(g('rec_tgt'))),('REC',n(g('rec'))),('REC YD',nn(g('rec_yd'))),('REC TD',n(g('rec_td'))),
           ('CATCH%',pc(g('rec'),g('rec_tgt'))),('YD/REC',r(g('rec_yd'),g('rec'))),('YD/TGT',r(g('rec_yd'),g('rec_tgt'))),('LNG',lng('rec_lng')),('RUSH YD',nn(g('rush_yd')))]
    elif pos=='K':
        bk=lambda ks:fr(sum(g('fgm_'+k) for k in ks),sum(g('fgm_'+k)+g('fgmiss_'+k) for k in ks))
        c=[('FG',fr(g('fgm'),g('fga'))),('FG%',pc(g('fgm'),g('fga'))),('LNG',lng('fgm_lng')),('XP',fr(g('xpm'),g('xpa'))),('XP%',pc(g('xpm'),g('xpa'))),
           ('0–19',bk(['0_19'])),('20–29',bk(['20_29'])),('30–39',bk(['30_39'])),('40–49',bk(['40_49'])),('50+',bk(['50_59','60p']))]
    else:
        c=[('SK',n(g('sack'))),('INT',n(g('int'))),('FR',n(g('fum_rec'))),('FF',n(g('ff'))),('TD',n(g('def_td')+g('def_st_td'))),
           ('TO',n(g('int')+g('fum_rec'))),('SFTY',n(g('safe'))),('BLK',n(g('blk_kick'))),('PA/G',r(g('pts_allow'),gp)),('YDS/G',r(g('yds_allow'),gp,'{:.0f}') if g('yds_allow') else '–')]
    return ''.join(f'<span><u>{l}</u><b{" class=fr" if "/" in v else ""}>{v}</b></span>' for l,v in c)
def crank(vals):  # competition rank, higher value first
    s=sorted(vals,reverse=True);return lambda v:1+sum(1 for x in s if x>v+1e-9)
rows_by={};chk={}
for pos in ORD:
    L=[]
    for pid,(name,p,nfl,w,t,own,bd) in PL.items():
        if p!=pos:continue
        pl=[v for v in w if v is not None];pts=round(sum(pl),2);gp=len(pl)
        L.append(dict(pid=pid,name=name,nfl=nfl,w=w,t=t,own=own,bd=bd,pts=pts,gp=gp,ppg=pts/gp if gp else 0))
    ra=crank([o['pts'] for o in L]);q=[o for o in L if o['gp']>=MIN];rb=crank([o['ppg'] for o in q])
    for o in L:o['ra']=ra(o['pts']);o['rb']=rb(o['ppg']) if o['gp']>=MIN else None
    rows_by[pos]=sorted(L,key=lambda o:(o['ra'],o['name']))
    chk[pos]=(sum(o['ra']<=TOP and o['pts']>0 for o in L),sum(1 for o in L if o['rb'] and o['rb']<=TOP and o['ppg']>0))
def row(o,pos):
    ina=o['ra']<=TOP and o['pts']>0;inb=o['rb'] is not None and o['rb']<=TOP and o['ppg']>0
    if not(ina or inb):return ''
    by=BYE.get(o['nfl']);bc='past' if by and by<=D else 'now' if by==D+1 else ''
    byh=f'<i class="by {bc}">(<b>{by}</b>)</i>' if by else ''
    a=age(o['bd']);ag=f'<em class="pag {acl(a)}">{a:.1f}</em>' if a and pos!='DEF' else ''
    own=f'<i class="own"><span class="of">{e(RN[o["own"]])}</span><span class="os">{e(SHORT0.get(RN[o["own"]],RN[o["own"]]))}</span></i>' if o['own'] in RN else '<i class="own fa">Free agent</i>'
    cls='rr2 plr'+('' if ina else ' xa')+('' if inb else ' xb')
    sq=f'<i class="pq p-{pos.lower()} t-{o["nfl"] or "FA"}"><span class="pqi"><span>{pos}</span><b class="ka">{o["ra"]}</b><b class="kb">{o["rb"] or ""}</b></span></i>'
    nb=badge(o['nfl']).replace('<em class="nfl','<em class="nfl tm',1) if o['nfl'] else ''
    return (f'<div class="{cls}" style="--a:{o["ra"]};--b:{o["rb"] or 999}">{sq}'
            f'<span class="rn"><b>{nmh(o["name"],pos)}{nb}{ag}</b><small><span class="gp">{o["gp"]} GP</span>{byh}{own}</small>'
            f'<span class="pst">{statline(pos,o["t"],o["gp"] or 1)}</span></span>'
            f'<span class="rv">{o["pts"]:.1f}</span><span class="rg2">{o["ppg"]:.1f}</span></div>')
radios=(''.join(f'<input type="radio" name="plp" id="pl-{p.lower()}" class="lr"{" checked" if p=="QB" else ""}>' for p in ORD)
        +'<input type="radio" name="pls" id="pl-sp" class="lr" checked><input type="radio" name="pls" id="pl-sg" class="lr">'
        +'<input type="radio" name="plcol" id="plc-p" class="lr"><input type="radio" name="plcol" id="plc-t" class="lr" checked>')
chips='<div class="lbc roc plc" role="tablist" aria-label="Position">'+''.join(f'<label for="pl-{p.lower()}">{p}</label>' for p in ORD)+'</div>'
seg=('<div class="plrow"><div class="pseg plcs" role="group" aria-label="Tile colours"><label for="plc-p">Position</label><label for="plc-t">Team</label></div>'
     '<div class="pseg plseg" role="group" aria-label="Sort"><label for="pl-sp">Pts</label><label for="pl-sg">/ Gm</label></div></div>')
blocks=''.join(f'<div class="plb plb-{p.lower()}" role="tabpanel" aria-label="{NAMES[p]}"><div class="rtop"><b>{NAMES[p]}</b><span><span class="pl-pt">Top {min(TOP,chk[p][0])} by points</span><span class="pl-pg">Top {min(TOP,chk[p][1])} by points per game</span></span></div>'
               f'<div class="rcol"><span>Player</span><span class="ca">Pts</span><span class="cb">/g</span></div><div class="pll">'+''.join(row(o,p) for o in rows_by[p])+'</div></div>' for p in ORD)
sec=(f'<section class="plx" aria-labelledby="plh">{radios}<div class="posh"><b id="plh">Players</b></div>'
     f'<div class="rsub">All NFL players · tile = position rank by <span class="pl-pt">points</span><span class="pl-pg">points per game, min. {MIN} games</span> · Wk 1–{D}</div>'
     f'{chips}{seg}{blocks}</section>')
open(P+'pl_section.html','w',encoding='utf-8').write(sec)
ids=[p.lower() for p in ORD]
PC={'qb':'#f7739c','rb':'#3ddcc1','wr':'#5ec6f4','te':'#fca95c','k':'#c491ff','def':'#c98a72'}
css=(''.join(f'.plx .plc label[for="pl-{i}"]{{color:{PC[i]};border-color:color-mix(in srgb,{PC[i]} 45%,transparent)}}'
             f'#pl-{i}:checked~.plc label[for="pl-{i}"]{{background:color-mix(in srgb,{PC[i]} 82%,#0b0e14);color:#0b0e14;border-color:transparent}}#pl-{i}:checked~.plb-{i}{{display:block}}' for i in ids)
 +'#pl-sp:checked~.plrow label[for="pl-sp"],#pl-sg:checked~.plrow label[for="pl-sg"],#plc-p:checked~.plrow label[for="plc-p"],#plc-t:checked~.plrow label[for="plc-t"]{background:var(--chalk);color:var(--ink)}'
 +'.plx .plb{display:none}.plx .pll{display:flex;flex-direction:column}.plx .plr{order:var(--a)}#pl-sg:checked~.plb .plr{order:var(--b)}'
 +'#pl-sp:checked~.plb .xa,#pl-sg:checked~.plb .xb{display:none}'
 +'.plx .kb,.plx .pl-pg{display:none}#pl-sg:checked~.plb .kb,#pl-sg:checked~.rsub .pl-pg,#pl-sg:checked~.plb .pl-pg{display:inline}#pl-sg:checked~.plb .ka,#pl-sg:checked~.rsub .pl-pt,#pl-sg:checked~.plb .pl-pt{display:none}'
 +'.plx .plc{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px}.plx .plc label{text-align:center;padding-inline:0}'
 +'.plx .plrow{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:10px 0 12px}.plx .plrow .pseg{display:inline-flex;margin:0}'
 +team_tiles('#plc-t:checked~.plb')+'.plx .rr2>.pq{box-shadow:inset -1px 0 0 rgba(255,255,255,.08)}'
 +'.plx .rr2{grid-template-columns:minmax(0,1fr) 54px 40px!important}'
 +'@media(max-width:429px){.plx .nmx.lg .fn,.plx .dc{display:none}.plx .nmx.lg .fi{display:inline}}'
 +'@media(max-width:374px){.plx .pag{display:none}.plx .pst b{font-size:14px}.plx .pst b.fr{font-size:12.5px;letter-spacing:-.01em}.plx .pst{gap:6px 4px}.plx .pst u{font-size:9px;letter-spacing:.02em}}'
 +'.plx .rcol{display:grid;grid-template-columns:minmax(0,1fr) 54px 40px;column-gap:8px;padding:0 10px 6px calc(34px + 9px)}'
 +'#pl-sp:checked~.plb .rcol .ca,#pl-sg:checked~.plb .rcol .cb{color:var(--chalk)}'
 +'.plx .plr .rv,.plx .plr .rg2{text-align:right;white-space:nowrap;line-height:22px!important;height:22px}'
 +'#pl-sg:checked~.plb .plr .rg2{font:700 19px/22px var(--display)!important;letter-spacing:.01em;color:var(--chalk)!important}'
 +'#pl-sg:checked~.plb .plr .rv{font:400 12.5px/22px var(--body)!important;letter-spacing:normal;color:var(--steel)!important}'
 +'.plx .rn small{display:flex;align-items:baseline;gap:0 6px;min-width:0;white-space:nowrap}.plx .own{font-style:normal;color:var(--label);overflow:hidden;text-overflow:ellipsis;min-width:0}.plx .own::before{content:"·";margin-right:6px;color:var(--steel)}.plx .own.fa{color:var(--steel)}'
 +'.plx .os{display:none}@media(max-width:429px){.plx .of{display:none}.plx .os{display:inline}}'
 +'.plx .rn{overflow:visible}.plx .plr{align-items:start}.plx .plr .rv,.plx .plr .rg2{align-self:start;padding-top:10px}'
 +'.plx .pst{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px 6px;width:calc(100% + 110px);box-sizing:border-box;margin-top:8px;padding-top:8px;border-top:1px solid var(--hair)}'
 +'.plx .pst span{display:flex;flex-direction:column;gap:2px;min-width:0}'
 +'.plx .pst u{text-decoration:none;font:600 9.5px/1.1 var(--body);letter-spacing:.04em;color:var(--steel);white-space:nowrap}'
 +'.plx .pst b{font:600 15px/1.1 var(--display);color:var(--chalk);white-space:nowrap;font-variant-numeric:tabular-nums}'
 +'.plx .snp{font-style:normal;color:var(--label)}.plx .snp::before{content:"·";margin-right:6px;color:var(--steel)}')
open(P+'pl_css.css','w',encoding='utf-8').write(css)
print('players tab:',{p:chk[p] for p in ORD},'| bytes',len(sec))
