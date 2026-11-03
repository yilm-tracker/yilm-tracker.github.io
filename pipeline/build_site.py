# Wrap standings.html (scripts kept, for the live site) as site/index.html, and copy the no-script file for download.
import os,shutil,datetime,zoneinfo
P=os.path.dirname(os.path.abspath(__file__))+'/';OUT=os.path.join(P,'..','site')
os.makedirs(OUT,exist_ok=True)
# Year switch: this build's season (DT_SEASON, default the current one) and the past seasons published under site/<year>/
import json as _j;CUR=os.environ.get('DT_CUR') or _j.load(open(P+'seasons.json'))['current'];Y=os.environ.get('DT_SEASON',CUR);PAST=Y!=CUR
RAWD=os.path.join(P,'history','raw');YEARS=os.environ['DT_YEARS'].split(',') if os.environ.get('DT_YEARS') else [CUR]+sorted([d for d in (os.listdir(RAWD) if os.path.isdir(RAWD) else []) if d.isdigit() and d!=CUR],reverse=True)
s=open(P+'standings.html',encoding='utf-8').read()
now=datetime.datetime.now(zoneinfo.ZoneInfo('America/New_York'));stamp=now.strftime('%a %b %-d, %-I:%M %p ET');ver=now.strftime('%Y%m%d%H%M%S')
UPD=('<div id="upd" role="status" hidden><span>New scores</span><button type="button" onclick="location.reload()">Refresh</button></div>'
 '<style>#upd{position:fixed;left:50%;bottom:calc(16px + env(safe-area-inset-bottom));transform:translateX(-50%);z-index:50;display:flex;align-items:center;gap:12px;'
 'padding:8px 8px 8px 16px;border-radius:999px;background:var(--chalk);color:var(--ink);font:500 14px var(--body);box-shadow:0 6px 24px rgba(0,0,0,.45)}#upd[hidden]{display:none}'
 '#upd button{border:0;border-radius:999px;padding:6px 14px;background:var(--ink);color:var(--chalk);font:600 13px var(--body);cursor:pointer}</style>'
 '<script>(function(){var V="'+ver+'",el=document.getElementById("upd");function chk(){if(document.visibilityState!=="visible"||!el.hidden)return;'
 'fetch("build.json?"+Date.now(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){if(j.v&&j.v!==V)el.hidden=false}).catch(function(){})}'
 'setInterval(chk,120000);document.addEventListener("visibilitychange",chk)})()</script>')
head=('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
      '<meta name="robots" content="noindex">\n')
s=head+s.replace('<meta charset="utf-8">\n','',1)
if PAST:UPD=''  # a finished season never changes: no update poller, no live scores
else:UPD+='<script>'+open(P+'live.js',encoding='utf-8').read()+'</script>'  # in-page live scores (Matchups)
# remember the selected tab / switches (per season; the tab itself is shared, so switching year keeps the section) across reloads (radio state), so a refresh comes back to the same view and
# Safari's restored scroll position lands where it was instead of in the middle of Standings
UPD+=('<script>(function(){var K="dt-radios'+('-'+Y if PAST else '')+'";try{var s=JSON.parse(sessionStorage.getItem(K)||"[]");'
      's.forEach(function(id){var e=document.getElementById(id);if(e&&e.type==="radio")e.checked=true});'
      'var tb=document.getElementById(sessionStorage.getItem("dt-tab")||"");if(tb&&tb.name==="tab")tb.checked=true}catch(e){}'
      'document.addEventListener("change",function(ev){var t=ev.target;if(!t||t.type!=="radio")return;'
      'try{var ids=[].map.call(document.querySelectorAll("input[type=radio]:checked"),function(x){return x.id}).filter(Boolean);'
      'sessionStorage.setItem(K,JSON.stringify(ids));if(t.name==="tab")sessionStorage.setItem("dt-tab",t.id)}catch(e){}},true)})()</script>')
# no flash of the unstyled page: the final stylesheet sits after ~10 MB of embedded data, so the page stays hidden
# (page colour only) until that last style block has arrived, then shows fully styled
import re as _reh
_pgs=_reh.findall(r'--pg:\s*(#[0-9a-fA-F]{3,8})',open(P+'readability.css',encoding='utf-8').read())
_HIDE='<style>body>*{visibility:hidden}'+(f'html,body{{background:{_pgs[-1]}}}' if _pgs else '')+'</style>';_SHOW='<style>body>*{visibility:visible}</style>'
j=s.index('</style>')+len('</style>');s=s[:j]+_HIDE+'\n</head>\n<body>'+s[j:]+_SHOW+UPD+f'\n<!-- built {stamp} -->\n</body>\n</html>\n'
s=s.replace('</style>','body{margin:0}</style>',1)
# small TeamHub link on the eyebrow line (live site only; the download file stays as is). Negative margins keep the
# line box unchanged, so nothing else on the page moves; the ::after pad gives it a 44px tap target.
_EB='<div class="eyebrow">Official</div>'
if False:  # (dynasty tracker only) TeamHub link
    s=s.replace(_EB,'<div class="eyebrow">Official<a class="thl" href="teamhub/">TeamHub<span aria-hidden="true">›</span></a></div>',1)
    s=s.replace('</style>','.thl{position:relative;display:inline-block;vertical-align:top;margin:-2px 0 -2px 10px;padding:3px 8px 2px 9px;border-radius:999px;'
      'border:1px solid rgba(255,122,26,.55);background:rgba(255,122,26,.12);color:#ff9a4d;font:700 12px/1 var(--display);letter-spacing:.1em;text-decoration:none}'
      '.thl span{margin-left:4px;letter-spacing:0}.thl::after{content:"";position:absolute;inset:-13px -8px}.thl:hover{background:rgba(255,122,26,.22);color:#ffb27a}</style>',1)
# year switch in the top-right corner, above the countdown; absolutely placed, so the header grid is unchanged
if len(YEARS)>1:
    href=lambda y:('./' if not PAST else '../') if y==CUR else (('' if not PAST else '../')+y+'/')
    # one button per season; a finished season shows its champion underneath (pipeline/champions.json: {"year": "team"})
    import json as _jc,html as _hc
    CH=_jc.load(open(P+'champions.json',encoding='utf-8')) if os.path.exists(P+'champions.json') else {}
    # seasons without a page here (e.g. MFL years) still get a button and their champion, not clickable
    _ALL=sorted(set(YEARS)|set(CH))
    # owner first names for the champion line on phones, where six buttons share a row (owners.json: {"team": "owner"})
    OWN=_jc.load(open(P+'owners.json',encoding='utf-8')) if os.path.exists(P+'owners.json') else {}
    def _yb(y):
        _t=CH.get(y);_o=OWN.get(_t) if _t else None
        cap=(f'<small><span class="cf">{_hc.escape(_t)}</span><span class="cs">{_hc.escape(_o or _t)}</span></small>' if _t else (f'<small><span class="cf">In progress</span><span class="cs">Now</span></small>' if y==CUR else '<small></small>'))
        if y in YEARS:return f'<a class="yb{" on" if y==Y else ""}" href="{href(y)}"'+(' aria-current="page"' if y==Y else '')+f'><b>{y}</b>{cap}</a>'
        return f'<span class="yb na" title="{y}: before this site (MyFantasyLeague)"><b>{y}</b>{cap}</span>'
    sw=f'<nav class="yrs n{len(_ALL)}" aria-label="Season">'+''.join(_yb(y) for y in _ALL)+'</nav>'
    s=s.replace('<header>',sw+'<header>',1)  # its own row above the header, so it never sits on the title or the countdown
    s=s.replace('</style>',
      # every button the same width (the widest caption sets it), right-aligned; phones: one row across the full width
      '.yrs{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:10px 12px;width:max-content;max-width:100%;margin:0 0 8px auto;align-items:start}'
      '.yrs .yb{position:relative;display:flex;flex-direction:column;align-items:stretch;gap:6px;min-width:0;text-decoration:none}'
      # raised button, BDGE-style: a solid dark under-edge offset down-right plus a soft drop, pressed in on tap
      '.yrs .yb b{display:block;box-sizing:border-box;padding:7px 0;text-indent:.06em;text-align:center;border-radius:9px;border:1px solid rgba(0,0,0,.55);background:var(--deck-2);'
      'box-shadow:3px 4px 0 rgba(0,0,0,.6),0 8px 14px -4px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.06);'
      'font:700 13px/1 var(--display);letter-spacing:.06em;color:var(--label);font-variant-numeric:tabular-nums;text-box:trim-both cap alphabetic;transition:transform .08s,box-shadow .08s}'
      '.yrs a.yb:active b{transform:translate(2px,3px);box-shadow:1px 1px 0 rgba(0,0,0,.6),0 3px 6px -2px rgba(0,0,0,.5)}'
      '.yrs .yb.on b{background:var(--chalk);color:var(--ink)}.yrs a.yb:not(.on):hover b{color:var(--chalk)}'
      '.yrs .yb.na{cursor:default}.yrs .yb.na b{color:var(--steel)}'
      '.yrs .yb small{display:block;padding:0 4px;white-space:nowrap;font:600 10.5px/1.15 var(--body);color:#c9a15a;text-align:center}'
      '.yrs .yb.on small{color:var(--steel)}.yrs .yb small:empty{display:none}.yrs .cs{display:none}'
      '@supports not (text-box:trim-both cap alphabetic){.yrs .yb b{padding:6px 0 5px}}'
      '@media(max-width:640px){.yrs.n4,.yrs.n5,.yrs.n6,.yrs.n7,.yrs.n8{width:100%;gap:8px 7px}.yrs.n4 .cf,.yrs.n5 .cf,.yrs.n6 .cf,.yrs.n7 .cf,.yrs.n8 .cf{display:none}'
      '.yrs.n4 .cs,.yrs.n5 .cs,.yrs.n6 .cs,.yrs.n7 .cs,.yrs.n8 .cs{display:inline}.yrs .yb small{padding:0;font-size:10px}.yrs .yb b{font-size:12.5px;letter-spacing:.04em;text-indent:.04em;padding:6.83px 0 7.17px}}</style>',1)
open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(s)
shutil.copy(P+'DynastyStandings.html',os.path.join(OUT,'DynastyStandings.html'))
open(os.path.join(OUT,'.nojekyll'),'w').close()
import json;json.dump({'v':ver,'built':stamp},open(os.path.join(OUT,'build.json'),'w'))
print('site built',stamp,round(len(s)/1e6,1),'MB')
