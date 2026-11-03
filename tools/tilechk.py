# QA: every rank tile beside a figure must sit inside the figure's cap height (top not above cap top, bottom not below baseline).
# Usage: python3 tools/tilechk.py 402 440 360 1440   -> expects 0 violations on both trackers
# every rank tile beside text: tile top must not be above the text's cap top, bottom not below its baseline
import sys;sys.path.insert(0,'/home/claude/yilm-tracker.github.io/tools');import realfonts
from playwright.sync_api import sync_playwright
JS='''()=>{const out=[];const C=document.createElement('canvas').getContext('2d');
 document.querySelectorAll('.ch,.rkb').forEach(t=>{if(!t.offsetParent||t.closest('.gm,.sxm,.lbr,.hmx,.tqgrid,.mx,.bym'))return;
  let n=t.previousSibling;while(n&&n.nodeType===3&&!n.textContent.trim())n=n.previousSibling;if(!n)return;
  const w=n.nodeType===3?null:document.createTreeWalker(n,NodeFilter.SHOW_TEXT);let tn=n.nodeType===3?n:null,x;if(w)while(x=w.nextNode())if(x.textContent.trim()&&!x.parentElement.closest('.lku'))tn=x;
  if(!tn||!/[0-9]/.test(tn.textContent))return;const el=tn.parentElement,cs=getComputedStyle(el);
  C.font=cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;const m=C.measureText('8');const g=document.createRange();g.selectNodeContents(tn);const rr=g.getBoundingClientRect();
  const z=rr.height/(m.fontBoundingBoxAscent+m.fontBoundingBoxDescent);const base=rr.top+m.fontBoundingBoxAscent*z,top=base-m.actualBoundingBoxAscent*z;
  const tr=t.getBoundingClientRect();if(tr.bottom<rr.top||tr.top>rr.bottom)return;
  const up=top-tr.top,dn=tr.bottom-base;if(up>0.6||dn>0.6)out.push((t.closest('[class]')&&t.parentElement.className.slice(0,14))+' "'+tn.textContent.trim().slice(-8)+'" up'+up.toFixed(1)+' dn'+dn.toFixed(1))});
 return out}'''
with sync_playwright() as p:
    b=p.chromium.launch()
    for k,u in {'bbp':'file:///home/claude/dynasty-tracker/site/index.html','yilm':'file:///home/claude/yilm-tracker.github.io/.season/2026/site/index.html'}.items():
      for w in [int(a) for a in (sys.argv[1:] or ['402','440','360'])]:
        pg=b.new_page(viewport={'width':w,'height':1800});pg.route('**/api.sleeper.app/**',lambda r:r.abort());realfonts.setup(pg);pg.goto(u);pg.wait_for_timeout(1500)
        res=pg.evaluate(JS);print(k,w,len(res),'violations');[print('   ',x) for x in res[:12]]
        pg.close()
    b.close()
