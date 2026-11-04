# Playoffs > Schedule: pick a team, see its players' NFL games for Weeks 15, 16 and 17.
# Rows are the players as on the Lineups (position tile with ranks, name, NFL team, injury, age); one column per week
# with home (vs) / road (@), the opponent and the kickoff time (ET). Starters as set in Sleeper first, then the bench.
import re,json
from zoneinfo import ZoneInfo
from datetime import datetime
import mu_build as MB
ET=ZoneInfo('America/New_York')
def _kick(w,tm):
    """kickoff (ET) in one style: '1 PM', '4:25 PM' on Sundays, 'Sat 8:20 PM' on other days, TNF / SNF / MNF at night"""
    k=MB._KJ.get(str(w),{}).get(tm)
    if not k:return 'TBD'
    d=datetime.fromisoformat(k[0]).astimezone(ET)
    if d.hour>=19 and d.weekday() in (0,3,6):return {0:'MNF',3:'TNF',6:'SNF'}[d.weekday()]
    t=f'{d.hour%12 or 12}'+(f':{d.minute:02d}' if d.minute else '')+(' PM' if d.hour>=12 else ' AM')
    return t if d.weekday()==6 else f'{d:%a} {t}'
import os
_P=os.path.dirname(os.path.abspath(__file__))+'/'
def _dvp():
    """points each NFL defence gives up per game to each position, league scoring, completed weeks; rank 1 = most allowed.
    Every player who played (pull_pts.json) is credited to the opponent his team faced that week (game pairs from kick.json)."""
    try:pts=json.load(open(_P+'pull_pts.json'));k=json.load(open(_P+'kick.json'))
    except Exception:return {},0
    if not pts:return {},0
    G=len(next(iter(pts.values()))[2]);opp={};gm={}
    for w in range(1,G+1):
        it=list(k.get(str(w),{}).items())
        for i in range(0,len(it)-1,2):
            a,b=it[i][0],it[i+1][0];opp[(w,a)]=b;opp[(w,b)]=a;gm[a]=gm.get(a,0)+1;gm[b]=gm.get(b,0)+1
    tot={}
    for pos,tm,wk,_ in pts.values():
        for i,v in enumerate(wk):
            o=opp.get((i+1,tm))
            if v is not None and o:tot[(pos,o)]=tot.get((pos,o),0.0)+v
    out={}
    for pos in ('QB','RB','WR','TE','K','DEF'):
        r=sorted(((tot.get((pos,t),0.0)/gm[t],t) for t in gm),key=lambda x:(-x[0],x[1]))
        out[pos]={t:(v,i+1) for i,(v,t) in enumerate(r)}
        AVG[pos]=sum(v for v,_ in r)/len(r) if r else 0.0
    return out,G
AVG={}   # league average allowed per game, by position
DVP,DVPG=_dvp()
def _who(p):
    """the player half of a lineup row, with the game line swapped for the player's age"""
    c=MB.lcell(p,'a');c=c[:c.index('<span class="cv ')]
    a=MB._age(p[0]);acl='ay' if a and a<27 else 'ap' if a and a<31 else 'ao'
    ag=f'<em class="pag {acl}">{a:.1f}</em>' if a else ''
    mk=re.search(r'<em class="nfl tm[^"]*">.*?</em>',c,flags=re.S)
    if mk:c=c.replace(mk.group(0),'',1)
    lg=mk.group(0).replace('nfl tm','nfl opp',1) if mk else ''   # .cnm small .nfl.opp is what carries a logo on this line
    return re.sub(r'<small>.*?</small>',f'<small class="psag">{ag}{lg}</small>',c,count=1,flags=re.S)
def _game(p,bye=False,opt=False):
    cl=' psy' if bye else ''
    if not p[6]:return f'<span class="psg{cl}"><span class="psb">Bye</span></span>'
    d=DVP.get(p[1],{}).get(p[6])
    if d:
        v,r=d;n=len(DVP[p[1]]);tn='g' if r<=10 else 'b' if r>n-10 else ''
        dv=(f'<span class="psv"><i class="ch psk2 {tn}" title="Points allowed to {p[1]}: rank {r} of {n} (1 = most)"><span class="ct">{r}</span></i>'
            f'<b class="psa" title="{v:.1f} {p[1]} points a game allowed (all {p[1]}s combined), league average {AVG[p[1]]:.1f}">{"+" if v-AVG[p[1]]>=0.05 else "−" if v-AVG[p[1]]<=-0.05 else ""}{abs(v-AVG[p[1]]):.1f}</b></span>')
    else:dv='<span class="psv"></span>'
    # same markup as a Matchups game line (.cnm small .gp): the HOME / ROAD tile and the opponent's logo
    o='<svg class="pst8" viewBox="0 0 24 24" aria-label="In the best projected lineup"><path d="M12 2.6l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.4l-5.9 3.3 1.3-6.6-4.9-4.6 6.6-.8z"/></svg>' if opt else ''   # in the team's best projected lineup that week: small gold star
    return (f'<span class="psg cnm{cl}"{' title="In the best projected lineup this week"' if opt else ''}><small><span class="gp psl">{MB._gline(p[9],p[6])}</span></small>{dv}{o}'
            f'<span class="pst">{_kick(p[10],p[3])}</span></span>')
def build(H,SHORT,e,WEEKS,mp,setlineup,pool,dd,byes=2,opt=lambda t,w:set()):
    """returns (radios, picker html, panels html, css); dd(k,lab) is the team drop-down used by Matchup"""
    n=len(H);w0=WEEKS[0]
    radios=''.join(f'<input type="radio" name="ps" id="ps-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(n))
    pan=[]
    for i,t in enumerate(H):
        by=i<byes   # seeds 1-2: no Week 15 game
        hd=('<div class="cr lu psr psh"><span>Player</span>'+''.join(f'<span{" class=psy" if by and w==w0 else ""}>Wk {w}</span>' for w in WEEKS)+'</div>')
        st=[q for q in setlineup(t,w0) if q]
        ids={q['pid'] for q in st}
        order=['QB','RB','WR','TE','K','DEF']
        bn=sorted([q for q in pool(t,w0) if q['pid'] not in ids],key=lambda q:(order.index(q['pos']) if q['pos'] in order else 9,-q['pj']))
        OP={w:opt(t,w) for w in WEEKS}
        def row(q):
            ps=[mp(next((x for x in pool(t,w) if x['pid']==q['pid']),q),w) for w in WEEKS]
            return f'<div class="cr lu psr">{_who(ps[0])}'+''.join(_game(p,by and p[10]==w0,(not (by and p[10]==w0)) and p[0] in OP[p[10]]) for p in ps)+'</div>'
        body=hd+''.join(row(q) for q in st)
        if bn:body+='<div class="msh lbh psbh">Bench</div>'+hd+''.join(row(q) for q in bn)
        pan.append(f'<div class="psp psp-{i}">{body}</div>')
    pick=('<div class="cpk psk">'+dd('s','')+'</div>'
          f'<div class="pskey"><span><i class="ch g"><span class="ct">1</span></i>most allowed to position<i class="ch b"><span class="ct">32</span></i>fewest</span><span><svg class="pst8 k" viewBox="0 0 24 24" aria-label="In the best projected lineup"><path d="M12 2.6l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.4l-5.9 3.3 1.3-6.6-4.9-4.6 6.6-.8z"/></svg>in the best projected lineup</span>'
          f'<span class="pskw"><b>+4.2</b>pts/game allowed to the position vs league avg · Wks 1–{DVPG}</span></div>' if DVP else '')
    css=(''.join(f'#ps-{i}:checked~.psk .dd-s .sv-{i}{{display:inline}}#ps-{i}:checked~.psk .dd-s label[for="ps-{i}"]{{background:var(--chalk);color:var(--ink)}}#ps-{i}:checked~.psx .psp-{i}{{display:block}}' for i in range(n))+
         '.psk{grid-template-columns:minmax(0,1fr)!important}.psp{display:none}'
         '.psr{display:grid;grid-template-columns:minmax(0,1.3fr) repeat(3,minmax(0,1fr))!important;grid-template-areas:none!important;column-gap:0;align-items:center;padding-right:0!important}'
         '.cr.lu.psr.psh{border-color:transparent!important;background:none!important;box-shadow:none!important}.cr.lu.psr::after{display:none!important}'
         '.psr>*{grid-row:1;min-width:0}.psr>.cn{grid-column:1;grid-area:auto;padding-right:6px}.psr>:nth-child(2){grid-column:2}.psr>:nth-child(3){grid-column:3}.psr>:nth-child(4){grid-column:4}'
         '.psr.psh{padding-top:10px!important;padding-bottom:6px!important;min-height:0!important;font-family:var(--display);font-weight:700;font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--label)}'
         '.psh>span:not(:first-child){text-align:center}.psh>span.psy{color:var(--text-dim)}'
         # each week a pillar: full row height, its own shade, a cut on its left
         '.psg{align-self:stretch;margin:-8px 0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;min-width:0;line-height:1;'
         'background:rgba(255,255,255,.035);box-shadow:inset 2px 0 0 var(--ink)}'
         '.psg small{display:flex;justify-content:center}.psg .psl{display:flex;align-items:center;white-space:nowrap;margin:0}.psg>small{margin:0!important;height:16px;align-items:center}.psg.cnm{padding-top:2px;box-sizing:border-box}'
         '.cr.lu.psr{padding-right:0!important}.cnm small.psag{gap:6px!important;height:14px}.psag .nfl{height:15px!important;margin:-1px 0!important;transform:none!important}.psv{display:flex;align-items:center;gap:5px;line-height:1}'
         '.psv .psk2{margin:0;min-width:21px;height:15px;padding:0 4px;font-size:11px;font-weight:700;font-style:normal;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box}'
         '.psa{font-family:var(--display);font-weight:700;font-size:13.5px;font-variant-numeric:tabular-nums;color:var(--chalk)}'
         '.pst{font-size:10.5px;font-weight:500;color:var(--steel);white-space:nowrap;font-variant-numeric:tabular-nums}'
         '.psb{font-family:var(--display);font-weight:700;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim)}'
         '.psg.psy{background:rgba(0,0,0,.18)}.psg.psy>*{opacity:.28}'
         '.psbh{margin-top:18px}'
         # sizes follow the week cell's width (container units), never smaller than the phone sizes above: wider
         # screens (or a zoomed-out page) get bigger tiles, logo, figure and star instead of empty space
         '.psg.cnm{container-type:inline-size}'
         '.cr.lu .psg.cnm .gp .gha.ht,.psg .psv .psk2{width:clamp(20px,27cqw,30px)!important;height:clamp(17px,23cqw,25px)!important;font-size:clamp(11.5px,14.5cqw,16px)!important;border-radius:clamp(4px,5cqw,6px)!important}'
         '.cr.lu .psg.cnm b.psa{font-size:clamp(17px,24cqw,27px)!important;height:clamp(17px,23cqw,25px);line-height:1}'
         '.cr.lu .psg.cnm .gp .nfl.opp{width:clamp(18px,30cqw,33px)!important;height:clamp(17px,27cqw,29px)!important}'
         '.cr.lu .psg.cnm .pst8{width:clamp(12px,19cqw,18px)!important;height:clamp(12px,19cqw,18px)!important}'
         '.cr.lu .psg.cnm .pst{font-size:clamp(10.5px,12.5cqw,13px)}'
         # one 2-column grid per week: tiles in the left column (home/road over the matchup rank, same size, same left
         # edge), the opponent's logo and the points-allowed figure beside them, the kickoff under both
         '.psg.cnm{display:grid!important;grid-template-columns:auto auto minmax(0,1fr);align-content:center;column-gap:7px;row-gap:6px;padding:8px 4px 8px 9px!important;box-sizing:border-box}@media(max-width:380px){.cr.lu .psg.cnm b.psa{font-size:16px!important}.cr.lu .psg.cnm .gp .nfl.opp{width:18px!important;height:17px!important}.psg .psa{font-size:16.5px!important}.psg.cnm{column-gap:5px!important;padding-left:7px!important;padding-right:2px!important}}'
         '.psg.cnm>small,.psg.cnm .gp.psl,.psg.cnm .psv{display:contents!important}'
         '.psg .gp .gha.ht{grid-column:1;grid-row:2;top:0!important;margin:0!important}.psg .gp .nfl.opp{grid-column:2;grid-row:2;justify-self:start;margin:0!important;top:0!important}'
         '.psg .gp .gsep,.psg .gp .gwhen{display:none}'
         '.psg .psv .psk2{grid-column:1;grid-row:1;width:20px;min-width:0;height:17px;padding:0;border-radius:4px;font-size:11.5px}.psg .psv .psk2:not(.g):not(.b){background:rgba(238,240,244,.11);color:var(--label);box-shadow:inset 0 0 0 1px rgba(238,240,244,.32)}'
         '.psg .psv .psk2.g{background:rgba(63,214,155,.16);color:#7fdcb6;box-shadow:inset 0 0 0 1px rgba(63,214,155,.55)}.psg .psv .psk2.b{background:rgba(255,93,115,.18);color:#ff9aa8;box-shadow:inset 0 0 0 1px rgba(255,93,115,.6)}'
         '.pst8{width:11px;height:11px;fill:#f4c451;flex:none}.psg .pst8{grid-column:3;grid-row:2;justify-self:start;align-self:center;width:10px;height:10px;margin-left:-1px}.pskey .pst8{width:12px;height:12px}'
         '.psg .psa{grid-column:2 / -1;grid-row:1;justify-self:start;font-size:18px;line-height:17px;height:17px;display:flex;align-items:center;white-space:nowrap}'
         '.psg .pst{grid-column:1 / -1;grid-row:3;justify-self:start;margin-top:1px}.cr.lu.psr{min-height:84px}'
         '.pskey{display:flex;align-items:center;flex-wrap:wrap;gap:6px 14px;margin:2px 0 4px;font-size:11.5px;color:var(--steel)}.pskey .ch{margin:0 0 0 0;min-width:21px;height:15px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-style:normal;font-weight:700}.pskey .ch.b{margin-left:6px}.pskey>span{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}.pskey>span.pskw{white-space:normal;display:inline}.pskw b{margin-right:6px}.pskey b{font-family:var(--display);font-weight:700;color:var(--chalk)}.pskey .ch.g{background:rgba(63,214,155,.16);color:#7fdcb6;box-shadow:inset 0 0 0 1px rgba(63,214,155,.55)}.pskey .ch.b{background:rgba(255,93,115,.18);color:#ff9aa8;box-shadow:inset 0 0 0 1px rgba(255,93,115,.6)}'
         '')
    # player names: the largest size (down to 10px) that fits the narrower player column, refitted when a team is picked
    fit=('<script>(function(){function fit(){document.querySelectorAll(".psr .cnm b>span").forEach(function(el){if(!el.clientWidth||el.dataset.fw==el.clientWidth)return;'
         'el.dataset.fw=el.clientWidth;el.style.fontSize="";var f=parseFloat(getComputedStyle(el).fontSize);'
         'while(el.scrollWidth>el.clientWidth+0.5&&f>10){f-=0.5;el.style.fontSize=f+"px"}})}'
         'document.addEventListener("change",function(){requestAnimationFrame(fit)});window.addEventListener("resize",function(){requestAnimationFrame(fit)});'
         'if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit)})()</script>')
    return radios,pick,'<div class="psx">'+''.join(pan)+'</div>'+fit,css
