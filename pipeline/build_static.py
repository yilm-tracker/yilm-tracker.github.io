import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
import json,re
P=__DTP__+''
L=json.load(open(P+'lists.json')); s=open(P+'standings.html').read()
head='<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
i=s.index('<style>'); s=head+s[:i]+s[i:]
j=s.index('</style>')+len('</style>'); s=s[:j]+'\n</head>\n<body>'+s[j:]+'\n</body>\n</html>\n'
a=s.index('<div class="tg"'); b=s.index('</div>',a)+6
s=s[:a]+'''<input type="radio" name="view" id="vh" class="vr" checked><input type="radio" name="view" id="vm" class="vr">
  <div class="tg" role="group" aria-label="Scoring format"><label for="vh" class="tb tbh">H2H</label><label for="vm" class="tb tbm">Median</label></div>'''+s[b:]
s=s.replace('<div class="board" id="list"></div>','<div class="board lh">'+L['h']+'</div><div class="board lm">'+L['m']+'</div>')
import os
if os.path.exists(P+'po_static.html') and '<div class="ppx"' in s:
    a=s.index('<div class="ppx"');b=s.index('</script>',s.index('id="ppz"'));b=s.index('</script>',b+9)+9
    s=s[:a]+open(P+'po_static.html',encoding='utf-8').read()+s[b:]
    s=s.replace('</style>',open(P+'po_static.css').read()+'</style>',1)
s=re.sub(r'<script>.*?</script>','',s,flags=re.S)
css='''
body{margin:0}
.vr,.xp{position:fixed;top:50%;left:0;width:1px;height:1px;margin:0;opacity:0;pointer-events:none}
.tb{flex:1;text-align:center;color:var(--muted);font:500 13px var(--body);padding:8px 0;border-radius:7px;cursor:pointer}
#vh:checked~.tg .tbh,#vm:checked~.tg .tbm{background:var(--surface);color:var(--fg);box-shadow:0 0 0 1px var(--line-strong)}
.lm{display:none}
#vm:checked~.lh{display:none}
#vm:checked~.lm{display:block}
label.r{cursor:pointer}
label.r .strip{display:none}
.xp:checked+label.r .strip{display:flex}
'''
s=s.replace('</style>',css+'</style>',1)
assert s.count('<script')==0
open(P+'DynastyStandings.html','w').write(s)
print('built')
