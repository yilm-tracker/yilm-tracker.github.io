# Wrap standings.html (scripts kept, for the live site) as site/index.html, and copy the no-script file for download.
import os,shutil,datetime,zoneinfo
P=os.path.dirname(os.path.abspath(__file__))+'/';OUT=os.path.join(P,'..','site')
os.makedirs(OUT,exist_ok=True)
# Year switch: this build's season (DT_SEASON, default the current one) and the past seasons published under site/<year>/
CUR='2026';Y=os.environ.get('DT_SEASON',CUR);PAST=Y!=CUR
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
j=s.index('</style>')+len('</style>');s=s[:j]+'\n</head>\n<body>'+s[j:]+UPD+f'\n<!-- built {stamp} -->\n</body>\n</html>\n'
s=s.replace('</style>','body{margin:0}</style>',1)
# small TeamHub link on the eyebrow line (live site only; the download file stays as is). Negative margins keep the
# line box unchanged, so nothing else on the page moves; the ::after pad gives it a 44px tap target.
_EB='<div class="eyebrow">Official</div>'
if _EB in s and not PAST:
    s=s.replace(_EB,'<div class="eyebrow">Official<a class="thl" href="teamhub/">TeamHub<span aria-hidden="true">›</span></a></div>',1)
    s=s.replace('</style>','.thl{position:relative;display:inline-block;vertical-align:top;margin:-2px 0 -2px 10px;padding:3px 8px 2px 9px;border-radius:999px;'
      'border:1px solid rgba(255,122,26,.55);background:rgba(255,122,26,.12);color:#ff9a4d;font:700 12px/1 var(--display);letter-spacing:.1em;text-decoration:none}'
      '.thl span{margin-left:4px;letter-spacing:0}.thl::after{content:"";position:absolute;inset:-13px -8px}.thl:hover{background:rgba(255,122,26,.22);color:#ffb27a}</style>',1)
elif not PAST:
    print('build_site: eyebrow not found; TeamHub link skipped')
# year switch in the top-right corner, above the countdown; absolutely placed, so the header grid is unchanged
if len(YEARS)>1:
    href=lambda y:('./' if not PAST else '../') if y==CUR else (('' if not PAST else '../')+y+'/')
    sw='<nav class="yrs" aria-label="Season">'+''.join(f'<a href="{href(y)}"'+(' class="on" aria-current="page"' if y==Y else '')+f'>{y}</a>' for y in YEARS)+'</nav>'
    s=s.replace('<h1>The League</h1>',sw+'<h1>The League</h1>',1)
    s=s.replace('</style>','header{position:relative}.yrs{position:absolute;top:-17px;right:0;display:inline-flex;gap:2px;padding:2px;border:1px solid var(--hair);border-radius:999px;background:var(--ink)}'
      '.yrs a{position:relative;display:block;padding:4px 8px 3px;border-radius:999px;font:700 11.5px/1 var(--display);letter-spacing:.06em;color:var(--steel);text-decoration:none;font-variant-numeric:tabular-nums}'
      '.yrs a.on{background:var(--chalk);color:var(--ink)}.yrs a:not(.on):hover{color:var(--chalk)}.yrs a::after{content:"";position:absolute;inset:-8px -2px}</style>',1)
open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(s)
shutil.copy(P+'DynastyStandings.html',os.path.join(OUT,'DynastyStandings.html'))
open(os.path.join(OUT,'.nojekyll'),'w').close()
import json;json.dump({'v':ver,'built':stamp},open(os.path.join(OUT,'build.json'),'w'))
print('site built',stamp,round(len(s)/1e6,1),'MB')
