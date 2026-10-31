import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'

import json,re
S=json.load(open(__DTP__+'stats.json'))
def _u(n,l):return f'{n}<u>{l}</u>'
# Top three scoring stats (by fantasy points, either sign), shown in natural order. Attempts, carries and targets are left
# out: they score nothing. Kickers keep FG/XP; defenses keep their top two plays plus points allowed.
SS=json.load(open(__DTP__+'pull8a.json'))['ss']
KEYS={'QB':['pass_cmp','pass_att','pass_yd','pass_td','pass_int','rush_att','rush_yd','rush_td','fum_lost'],
      'RB':['rush_att','rush_yd','rush_td','rec','rec_tgt','rec_yd','rec_td','fum_lost'],
      'WR':['rec','rec_tgt','rec_yd','rec_td','rush_att','rush_yd','rush_td','fum_lost']}
KEYS['TE']=KEYS['WR']
LAB={'pass_yd':'PA YD','pass_td':'PA TD','pass_int':'INT','rush_yd':'RU YD','rush_td':'RU TD','rec':'REC','rec_yd':'RE YD','rec_td':'RE TD','fum_lost':'FL'}
def items(pos,a):
    v=dict(zip(KEYS[pos],a))
    it=[(k,v[k],v[k]*SS.get(k,0)) for k in KEYS[pos] if k in LAB and v.get(k)]
    it=[x for x in it if abs(x[2])>=0.5] or it[:1]  # drop trivia like -1 rushing yard
    top=sorted(range(len(it)),key=lambda i:(-abs(it[i][2]),i))[:3]
    return [it[i] for i in sorted(top)]
def _grp(lab,nums):return f'<span class="sit"><u>{lab}</u> {"-".join(f"({n})".replace("(-","(−") if isinstance(n,int) and n<0 else str(n) for n in nums)}</span>'
def _arr(w,pid):
    s=S.get(str(w),{}).get(pid)
    if s is None or s.endswith('x'):return s
    return [int(x) for x in s.split('.')]+[0]*10
def fumbles(w,pid,pos):
    """fumbles lost (shown as a red FL tag beside the name, not in the stat line)"""
    a=_arr(w,pid)
    if not isinstance(a,list):return 0
    return a[{'QB':8,'RB':7,'WR':7,'TE':7}.get(pos,99)] if pos in('QB','RB','WR','TE') else 0
def statline(w,pid,pos):
    """One line, at most two categories: QB 'PA 292-4' (yds-TD[-INT]) + 'RU 2-12' (car-yds[-TD]); RB 'RU' + 'REC';
    WR/TE 'REC' (rec-yds[-TD]) + 'RU'. K 'FG 3/4 • XP 1/1'. DEF 'SK 3 • TO 2 [• TD 1] • PA 24' (TO = INT + fumble recoveries)."""
    a=_arr(w,pid)
    if a is None:return ''
    if isinstance(a,str):return '<span class="sit">Did not play</span>'
    td=lambda c,y,t:[c,y]+([t] if t else [])
    if pos=='QB':
        o=[_grp('PA',[a[2]]+([a[3],a[4]] if a[4] else [a[3]] if a[3] else []))]+([_grp('RU',td(a[5],a[6],a[7]))] if a[5] else [])
    elif pos=='RB':
        o=([_grp('RU',td(a[0],a[1],a[2]))] if a[0] else [])+([_grp('REC',td(a[3],a[5],a[6]))] if a[3] else [])
        if not o:o=[_grp('RU',[0,0])]
    elif pos in('WR','TE'):
        o=([_grp('REC',td(a[0],a[2],a[3]))] if a[0] or a[1] else [])+([_grp('RU',td(a[4],a[5],a[6]))] if a[4] else [])
        if not o:o=[_grp('REC',[0,0])]
    elif pos=='K':
        o=[_grp('FG',[f'{a[0]}/{a[1]}']),_grp('XP',[f'{a[2]}/{a[3]}'])]
    elif pos=='DEF':
        o=[_grp('SK',[a[0]]),_grp('TO',[a[1]+a[2]])]+([_grp('TD',[a[3]])] if a[3] else [])+[_grp('PA',[a[4]])]
    else:o=[]
    return '<i class="sdt">•</i>'.join(o)
def tight(h):
    """'' / ' stg1' / ' stg2': smaller type for long lines so every stat line stays on one line"""
    n=len(re.sub(r'<[^>]+>','',h))+h.count('class="sit"')
    return '' if n<=T1 else ' stg1' if n<=T2 else ' stg2' if n<=T3 else ' stg3'
T1,T2,T3=19,23,26

# ---------- Detailed view: fuller stat lines + where the points came from (from stats_detail.json)
import os as _os
DET=json.load(open(__DTP__+'stats_detail.json')) if _os.path.exists(__DTP__+'stats_detail.json') else {}
def _n(v):return f'{v:g}' if isinstance(v,float) else str(v)
def _it(v,u=''):return f'<b>{_n(v)}{f"<i>{u}</i>" if u else ""}</b>'
def _line(lab,items):
    items=[x for x in items if x]
    return f'<span class="dxl dx-{lab.lower()}"><u>{lab}</u><span>{"".join(items)}</span></span>' if items else ''
def _cat(k):
    if k.startswith('pass_'):return 'Pass'
    if k.startswith('rush_'):return 'Rush'
    if k.startswith('rec'):return 'Rec'
    if k.startswith('fum') and k!='fum_rec':return 'Fum'
    if k.startswith(('fg','xp')):return 'Kick'
    return 'Def'
def breakdown(d):
    """points by category in this league's scoring, e.g. {'Pass': 15.68, 'Rush': 1.2}"""
    o={}
    for k,v in d.items():
        if k in SS and SS[k]:o[_cat(k)]=o.get(_cat(k),0)+v*SS[k]
    return {k:round(v,2) for k,v in o.items() if abs(v)>=0.005}
def detail(w,pid,pos):
    d=DET.get(str(w),{}).get(pid)
    if not d:return ''
    g=lambda k:d.get(k,0);gi=lambda k:int(round(g(k)))
    L=[]
    def opt(v,u):return _it(v,u) if v else ''
    def ch(*v):  # traditional line, dash-tied, each value keeps its unit: 7CAR-73YD-1TD (zero TD/INT left off)
        v=[(n,u) for n,u in v if n or u in('yd','car')]
        seg=[f'{"(−"+_n(-n)+")" if isinstance(n,(int,float)) and n<0 else _n(n)}<i>{u}</i>' for n,u in v]  # a long line can wrap after a dash, like a hyphen
        return '<b class="dch">'+'<wbr>'.join(f'<span>{x}{"<s>-</s>" if i<len(seg)-1 else ""}</span>' for i,x in enumerate(seg))+'</b>'
    lng=lambda k:_it(gi(k),'lng') if gi(k)>0 else ''
    pas=lambda:_line('PASS',[ch((f"{gi('pass_cmp')}/{gi('pass_att')}",'cmp'),(gi('pass_yd'),'yd'),(gi('pass_td'),'td'),(gi('pass_int'),'int')),opt(gi('pass_sack'),'sk'),lng('pass_lng')]) if g('pass_att') else ''
    rus=lambda:_line('RUSH',[ch((gi('rush_att'),'car'),(gi('rush_yd'),'yd'),(gi('rush_td'),'td')),_it(f"{g('rush_yd')/g('rush_att'):.1f}",'avg') if pos=='RB' else '',lng('rush_lng')]) if g('rush_att') else ''
    rec=lambda:_line('REC',[ch((f"{gi('rec')}/{gi('rec_tgt')}",'tgt'),(gi('rec_yd'),'yd'),(gi('rec_td'),'td')),lng('rec_lng')]) if g('rec_tgt') or g('rec') else ''
    if pos=='QB':L+=[pas(),rus()]
    elif pos=='RB':L+=[rus(),rec()]
    elif pos in('WR','TE'):L+=[rec(),rus()]
    elif pos=='K':
        ma=lambda m,x:(sum(gi(k) for k in m),sum(gi(k) for k in m)+sum(gi(k) for k in x))
        L.append(_line('XP',[_it(f"{gi('xpm')}/{gi('xpa') or gi('xpm')+gi('xpmiss')}")]))
        b=[('20s',['fgm_0_19','fgm_20_29'],['fgmiss_0_19','fgmiss_20_29']),('30s',['fgm_30_39'],['fgmiss_30_39']),('40s',['fgm_40_49'],['fgmiss_40_49']),('50+',['fgm_50_59','fgm_60p'],['fgmiss_50_59','fgmiss_60p'])]
        fg=[]
        for lab,m,x in b:
            mm,aa=ma(m,x)
            if lab=='20s' and not aa:continue
            fg.append(f'<b><em>{lab}</em>{mm}/{aa}</b>')
        L.append(_line('FG',fg+[opt(gi('fgm_lng'),'lng')]))
    elif pos=='DEF':
        L.append(_line('DEF',[opt(gi('sack'),'sk'),opt(gi('int'),'int'),opt(gi('fum_rec'),'fr'),opt(gi('ff'),'ff'),opt(gi('def_td')+gi('def_st_td'),'td'),opt(gi('safe'),'saf'),opt(gi('blk_kick'),'blk')]) or _line('DEF',[_it(0,'sk')]))
        L.append(_line('ALLOW',[_it(gi('pts_allow'),'pts'),opt(gi('yds_allow'),'yds')]))
    if g('fum'):L.append(_line('FUM',[opt(gi('fum_lost'),'lost'),opt(gi('fum')-gi('fum_lost'),'kept')]))
    tp=sum(gi(k) for k in('pass_2pt','rush_2pt','rec_2pt'))
    if tp:L.append(_line('2PT',[_it(tp)]))
    bd=breakdown(d);bd={k:bd[k] for k in ('Pass','Rush','Rec','Kick','Def','Fum') if k in bd}
    if bd:L.append(_line('PTS',[f'<b><em>{k}</em>{v:.1f}</b>' if v>=0 else f'<b><em>{k}</em>−{-v:.1f}</b>' for k,v in bd.items()]))
    return ''.join(L)

_DXK=None
def fumbles_kept(w,pid):
    """fumbles recovered by the offense (fumbled, not lost): no points lost, shown as a grey FK flag"""
    global _DXK
    if _DXK is None:
        try:_DXK=json.load(open(__DTP__+'stats_detail.json'))
        except Exception:_DXK={}
    s=_DXK.get(str(w),{}).get(pid) or {}
    return max(0,int(s.get('fum',0) or 0)-int(s.get('fum_lost',0) or 0))
