# Playoffs > Schedule: pick a team, see its players' NFL games for Weeks 15, 16 and 17.
# Rows are the players as on the Lineups (position tile with ranks, name, NFL team, injury, age); one column per week
# with home (vs) / road (@), the opponent and the kickoff time (ET). Starters as set in Sleeper first, then the bench.
import re,json
from zoneinfo import ZoneInfo
from datetime import datetime
import mu_build as MB
ET=ZoneInfo('America/New_York')
def _kick(w,tm):
    k=MB._KJ.get(str(w),{}).get(tm)
    if not k:return 'TBD'
    d=datetime.fromisoformat(k[0]).astimezone(ET)
    t=f'{d.hour%12 or 12}'+(f':{d.minute:02d}' if d.minute else '')
    if d.hour>=19 and d.weekday() in (0,3,6):return {0:'MNF',3:'TNF',6:'SNF'}[d.weekday()]
    t+=' PM' if d.hour>=12 else ' AM'
    return t if d.weekday()==6 else f'{d:%a} {t}'.replace(' PM','p').replace(' AM','a')
def _who(p):
    """the player half of a lineup row, with the game line swapped for the player's age"""
    c=MB.lcell(p,'a');c=c[:c.index('<span class="cv ')]
    a=MB._age(p[0]);acl='ay' if a and a<27 else 'ap' if a and a<31 else 'ao'
    ag=f'<em class="pag {acl}">{a:.1f}</em>' if a else ''
    return re.sub(r'<small>.*?</small>',f'<small>{ag}</small>',c,count=1,flags=re.S)
def _game(p):
    if not p[6]:return '<span class="psg"><span class="psb">Bye</span></span>'
    # same markup as a Matchups game line (.cnm small .gp): the HOME / ROAD tile and the opponent's logo
    return (f'<span class="psg cnm"><small><span class="gp psl">{MB._gline(p[9],p[6])}</span></small>'
            f'<span class="pst">{_kick(p[10],p[3])}</span></span>')
def build(H,SHORT,e,WEEKS,mp,setlineup,pool,dd):
    """returns (radios, picker html, panels html, css); dd(k,lab) is the team drop-down used by Matchup"""
    n=len(H);w0=WEEKS[0]
    radios=''.join(f'<input type="radio" name="ps" id="ps-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(n))
    hd=('<div class="cr lu psr psh"><span>Player</span>'+''.join(f'<span>Wk {w}</span>' for w in WEEKS)+'</div>')
    pan=[]
    for i,t in enumerate(H):
        st=[q for q in setlineup(t,w0) if q]
        ids={q['pid'] for q in st}
        order=['QB','RB','WR','TE','K','DEF']
        bn=sorted([q for q in pool(t,w0) if q['pid'] not in ids],key=lambda q:(order.index(q['pos']) if q['pos'] in order else 9,-q['pj']))
        def row(q):
            ps=[mp(next((x for x in pool(t,w) if x['pid']==q['pid']),q),w) for w in WEEKS]
            return f'<div class="cr lu psr">{_who(ps[0])}'+''.join(_game(p) for p in ps)+'</div>'
        body=hd+''.join(row(q) for q in st)
        if bn:body+='<div class="msh lbh psbh">Bench</div>'+hd+''.join(row(q) for q in bn)
        pan.append(f'<div class="psp psp-{i}">{body}</div>')
    pick='<div class="cpk psk">'+dd('s','')+'</div>'
    css=(''.join(f'#ps-{i}:checked~.psk .dd-s .sv-{i}{{display:inline}}#ps-{i}:checked~.psk .dd-s label[for="ps-{i}"]{{background:var(--chalk);color:var(--ink)}}#ps-{i}:checked~.psx .psp-{i}{{display:block}}' for i in range(n))+
         '.psk{grid-template-columns:minmax(0,1fr)!important}.psp{display:none}'
         '.psr{display:grid;grid-template-columns:minmax(0,1fr) repeat(3,var(--psw,58px))!important;grid-template-areas:none!important;column-gap:4px;align-items:center}'
         '.cr.lu.psr.psh{border-color:transparent!important;background:none!important;box-shadow:none!important}.cr.lu.psr::after{display:none!important}'
         '.psr>*{grid-row:1;min-width:0}.psr>.cn{grid-column:1;grid-area:auto}.psr>:nth-child(2){grid-column:2}.psr>:nth-child(3){grid-column:3}.psr>:nth-child(4){grid-column:4}'
         '.psr.psh{padding-top:10px!important;padding-bottom:6px!important;min-height:0!important;font-family:var(--display);font-weight:700;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--label)}'
         '.psh>span:not(:first-child){text-align:center}'
         '.psg{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;min-width:0;line-height:1}'
         '.psg small{display:flex;justify-content:center}.psg .psl{display:flex;align-items:center;white-space:nowrap;margin:0}'
         '.pst{font-size:11px;font-weight:500;color:var(--steel);white-space:nowrap;font-variant-numeric:tabular-nums}'
         '.psb{font-family:var(--display);font-weight:700;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}'
         '.psbh{margin-top:18px}'
         '@media (max-width:374px){.psr{--psw:54px}}')
    return radios,pick,'<div class="psx">'+''.join(pan)+'</div>',css
