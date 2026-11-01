import os as _dt_os;from html import escape as html_esc;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Assemble standings.html from head + data + script, inserting the timeline and position section.
import subprocess,json
P=__DTP__+''
subprocess.run(['python3',P+'pos/build_pos.py'],check=True,stdout=subprocess.DEVNULL)
h=open(P+'new_head.html',encoding='utf-8').read();t=open(P+'new_tail.js',encoding='utf-8').read()
import re as _r0
DONE=int(_r0.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))  # last completed week (from data_block)
BYES={5,6,7,8,9,10,11,13,14}  # 2026 NFL weeks with teams on bye (NFL.com schedule release)
import re as _re
_WK=json.loads(_re.search(r'const WK=(\{.*?\});\n',open(P+'data_block.js',encoding='utf-8').read()).group(1))
LTOT=[sum(_WK[t][w][2] for t in _WK) for w in range(DONE)]
_lo,_hi=800,max(LTOT)
def _seg(k):
    if k<=DONE:
        v=LTOT[k-1];hp=12+88*(v-_lo)/(_hi-_lo)
        bar=f'<i class="done" style="height:{hp:.1f}%" title="Week {k}: {v:.1f} league points"></i>'
    else:
        bar=f'<i class="{"po" if k>=15 else "fut"}"></i>'
    lab=f'<b class="wv">{LTOT[k-1]:.0f}<small>pts</small></b>' if k<=DONE else '<b class="wv"></b>'
    return f'<div class="wkc{" bye" if k in BYES else ""}">{lab}<span class="wb">{bar}</span><span>{k}</span></div>'
segs=''.join(_seg(k) for k in range(1,18))
d=open(P+'data_block.js',encoding='utf-8').read().replace('// remaining schedule: [week, opp, projScore, oppProj, winPct] (app projections as of Oct 15)','// remaining schedule: [week, opp, ...] (only week and opponent are shown)')
import json;sp0=__import__('subprocess');sp0.run(['python3',P+'lb_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('LB_SECTION',open(P+'lb_section.html',encoding='utf-8').read()).replace('LB_CSS',open(P+'lb_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'cmp_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('CMP_SECTION',open(P+'cmp_section.html',encoding='utf-8').read()).replace('CMP_CSS',open(P+'cmp_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'mu_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('MU_SECTION',open(P+'mu_section.html',encoding='utf-8').read()).replace('MU_CSS',open(P+'mu_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'ro_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('RO_SECTION',open(P+'ro_section.html',encoding='utf-8').read()).replace('RO_CSS',open(P+'ro_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'sx_build.py'],check=True,stdout=sp0.DEVNULL)
sp0.run(['python3',P+'po_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('PO_SECTION',open(P+'po_section.html',encoding='utf-8').read()).replace('PO_CSS',open(P+'po_css.css',encoding='utf-8').read())
h=h.replace('SX_SECTION',open(P+'sx_section.html',encoding='utf-8').read()).replace('SX_CSS',open(P+'sx_css.css',encoding='utf-8').read())
# Team Hub is switched by pipeline/features.json ("teamhub": true/false). Off = not built and not on the page
# (tab, pane and glossary removed); the code stays in th_build.py / th_charts.py, ready to switch back on.
_TH_OFF=False
_FT=json.load(open(P+'features.json')) if _dt_os.path.exists(P+'features.json') else {}
if _FT.get('teamhub',True):
    sp0.run(['python3',P+'th_build.py'],check=True,stdout=sp0.DEVNULL)
    h=h.replace('TH_SECTION',open(P+'th_section.html',encoding='utf-8').read()).replace('TH_CSS',open(P+'th_css.css',encoding='utf-8').read())
else:
    _TH_OFF=True
    import re as _re_th
    h=_re_th.sub(r'  <div class="pane pane-th">.*?\n  </div>\n(?=  <div class="pane pane-po">)','',h,flags=_re_th.S)
    h=h.replace('<label for="tab-th" class="tpo">Team Hub</label>','').replace('<input type="radio" name="tab" id="tab-th" class="lr tabr">','').replace('TH_CSS','')
# Players tab: top 50 NFL players by position (pull_top.json). Inserted beside Playoffs; skipped if the pull is missing.
_PL=_dt_os.path.exists(P+'pull_top.json')
if _PL:
    sp0.run(['python3',P+'pl_build.py'],check=True,stdout=sp0.DEVNULL)
    _GL='<div class="glw"><span>Glossary</span><div class="pseg glc" role="group" aria-label="Glossary"><label for="gl-h">Hide</label><label for="gl-s">Show</label></div></div>'
    _KEY=('<div class="key"><div><b>Players</b> every NFL player, rostered or not, ranked at his position by season points (half-PPR, league scoring) '
          'or by points per game. Per game needs at least half the completed weeks played. <b>Tile</b> = position rank for the chosen sort. '
          '<b>GP</b> games played, (bye week), then the fantasy team that rosters him or Free agent.</div>'
          '<div><b>Stat line</b> season totals. PA yards-TD-INT, RU carries-yards-TD, REC catches-yards-TD; K FG made/attempted, LNG longest FG, XP made/attempted; '
          'DEF SK sacks, TO takeaways (interceptions + fumble recoveries), TD defensive and return touchdowns, PA points allowed per game.</div></div>')
    h=h.replace('<input type="radio" name="tab" id="tab-po" class="lr tabr">','<input type="radio" name="tab" id="tab-po" class="lr tabr"><input type="radio" name="tab" id="tab-pl" class="lr tabr">',1)
    h=h.replace('<label for="tab-po" class="tpo">Playoffs</label>','<label for="tab-po" class="tpo">Playoffs</label><label for="tab-pl" class="tpo">Players</label>',1)
    h=h.replace('  <div class="pane pane-po">','  <div class="pane pane-pl">\n  '+open(P+'pl_section.html',encoding='utf-8').read()+'\n  '+_GL+'\n  '+_KEY+'\n  </div>\n  <div class="pane pane-po">',1)
    _PLCSS=open(P+'pl_css.css',encoding='utf-8').read()+'#tab-pl:checked~.tabs label[for="tab-pl"]{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}#tab-pl:checked~.pane-pl{display:block}'
if _dt_os.environ.get('DT_PAST')=='1':  # a finished past season: "Final" in place of the countdown
    h=h.replace('<div class="clock"><b>__LEFT__</b><span>weeks left</span></div>','<div class="clock fin"><b>Final</b></div>',1)
    h=h.replace('</style>','.clock.fin b{font-size:34px;letter-spacing:.02em;transform:translateY(1.5px)}</style>',1)
h=h.replace('__LEFT__',str(14-DONE)).replace('__G__',str(DONE))
# ---------- league branding: name, format line, palette, manager avatars (all from league.json)
import lg as _lgb
_ss=_lgb.L.get('scoring',{})
_fmt=[f'{_lgb.N} teams',{1:'Full PPR',0.5:'Half PPR',0:'Standard'}.get(_ss.get('rec',0),f"{_ss.get('rec')} PPR")]
if 'SUPER_FLEX' in _lgb.SLOTS:_fmt.append('Superflex')
if _ss.get('pass_td') and _ss.get('pass_td')!=4:_fmt.append(f"{_ss['pass_td']:g}-pt pass TD")
elif _ss.get('pass_td')==4:_fmt.append('4-pt pass TD')
if _ss.get('bonus_rec_te'):_fmt.append(f"TE +{_ss['bonus_rec_te']:g}")
h=h.replace('<title>Official Dynasty League</title>',f'<title>{html_esc(_lgb.NAME)}</title>',1)
h=h.replace('<div class="eyebrow">Official</div>',f'<div class="eyebrow">{html_esc(_lgb.NAME)}</div>',1)
h=h.replace('<h1>The League</h1>','<h1>Standings</h1>',1)
h=h.replace('<div class="season" ',f'<div class="fmt">{" · ".join(_fmt)}</div>\n    <div class="season" ',1)
_av='';_avr={}
for _t in _lgb.TEAMS:
    _f=_lgb.AV.get(_t)
    if _f and _dt_os.path.exists(P+'avatars/'+_f):
        _r=_lgb.RID[_t];_avr[_t]=_r
        _av+=f'.av-{_r}{{background-image:url(data:image/webp;base64,'+__import__('base64').b64encode(open(P+'avatars/'+_f,'rb').read()).decode()+')}'
h=h.replace('</style>',(':root{--ink:#0f1d2e;--deck:#162a3d;--deck-2:#1b3248;--chalk:#ffffff;--label:#d3dfeb;--steel:#a5b6c8;--dim:#7189a2;--hair:#24394f;'
  '--pylon:#fb637a;--sky:#259fd6;--loss:#ff5a3c;--loss-bg:rgba(255,90,60,.15);--line-strong:#31506c;--nt:'+str(_lgb.N)+'}'
  'header .fmt{grid-column:1 / -1;font-size:12.5px;color:var(--dim);margin-top:2px}'
  '.av{flex:none;display:inline-block;width:22px;height:22px;border-radius:50%;background:var(--deck-2) center/cover no-repeat;box-shadow:0 0 0 1px var(--hair)}'
  +_av+'</style>'),1)
d_av='const AVR='+json.dumps(_avr,ensure_ascii=False)+';\n'
h=h.replace('SEGMENTS',segs).replace('POS_SECTION',open(P+'pos/pos_section.html',encoding='utf-8').read())
import json,subprocess as sp
EF={t:v[:2] for t,v in json.load(open(P+'eff.json')).items()}
d+='// lineup efficiency: [actual PF as % of Max PF (best possible lineup), points left on the bench per week]\nconst EF='+json.dumps(EF)+';\n'
_sk=json.load(open(P+'skill_opt.json'));_sk.pop('_note',None)
SK={t:[round(v['act']/v['opt']*100,2),round((v['opt']-v['act'])/DONE,2)] for t,v in _sk.items()}
d+='// skill-position efficiency: [actual RB/WR/TE/FLEX points as % of the best legal 2RB+2WR+1TE+1FLEX combo from the roster, points per week left on the bench] (Sleeper lineups)\nconst SK='+json.dumps(SK)+';\n'
import importlib,sys as _sy;_sy.path.insert(0,P);import sx_data as _D
_DP={_t:[round(v,2) for v in _D.dropped(_t).values()] for _t in _D.TEAMS}
import lg as _lg
d+='// league: teams, playoff teams, byes, positions started\nconst NT='+str(_lg.N)+',PO='+str(_lg.PO)+',BYN='+str(_lg.BYE_N)+',LPOS='+json.dumps(_lg.POS)+';\n'
d+='// dropped points per week by position [QB,RB,WR,TE,K,DEF]: bench player who should have started minus the starter he replaces, credited to the bench player\'s position\nconst DP='+json.dumps(_DP)+';\n'
d+=d_av
import os as _os,base64 as _b64
_LG='';_MIME={'svg':'image/svg+xml','png':'image/png','webp':'image/webp'}
if _os.path.isdir(P+'logos'):
    for _f in sorted(_os.listdir(P+'logos')):
        _t,_,_x=_f.rpartition('.');_x=_x.lower()
        if _x in _MIME and _t.isalpha() and _t.isupper() and 2<=len(_t)<=3:
            _u='data:'+_MIME[_x]+';base64,'+_b64.b64encode(open(P+'logos/'+_f,'rb').read()).decode()
            try:  # shown at about 23x21 CSS px: embed a 72x64 WebP (sharp on 3x screens) instead of the full upload
                from PIL import Image as _Im;import io as _io
                _im=_Im.open(P+'logos/'+_f).convert('RGBA');_im.thumbnail((72,64),_Im.LANCZOS)
                _bb=_io.BytesIO();_im.save(_bb,format='WEBP',quality=90,method=6)
                _u='data:image/webp;base64,'+_b64.b64encode(_bb.getvalue()).decode()
            except Exception:pass
            _LG+=f'.thr .nfl.tm.n-{_t},.cnm b .nfl.tm.n-{_t},.rn>b .nfl.tm.n-{_t},.cnm small .nfl.opp.n-{_t}{{background:url("{_u}") center/contain no-repeat!important;box-shadow:none!important;border-radius:0!important;width:22px!important;height:20px!important}}.nfl.tm.n-{_t} .ct,.nfl.opp.n-{_t} .ct{{visibility:hidden}}'
_i=h.rindex('</style>');h=h[:_i]+open(P+'readability.css',encoding='utf-8').read()+_LG+(_PLCSS if _PL else '')+('.tabs label.tpo{grid-column:1 / -1!important}' if _TH_OFF and not _PL else '.tabs label.tpo{grid-column:span 2!important}' if not _TH_OFF and _PL else '')+h[_i:]
open(P+'standings.html','w',encoding='utf-8').write(h+d+t)
