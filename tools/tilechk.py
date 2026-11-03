# QA: every rank tile beside a figure spans exactly the figure's cap height: tile top = the figure's digit-ink top,
# tile bottom = its baseline (tolerance TOL px, default 0.05). Both trackers, any widths, Dumb and Nerd.
# Usage: python3 tools/tilechk.py 402 440 360 1440        -> expects 0 violations everywhere
#        TOL=0.1 python3 tools/tilechk.py 402             (looser tolerance, e.g. while experimenting)
# Exact by construction: the baseline is read from a zero-size inline-block placed on it (font-metric estimates are off by
# up to ~0.9px at zoomed widths), cap height = digit ink ascent x the element's real CSS zoom. A tile in a stat line that
# is NOT level with its figure is a violation too ("off line"), not silently skipped. Tiles stacked under their number
# (flex-column cells: Dropped pts, Stats table) are not beside a figure and are not checked.
import os,sys;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import realfonts
from playwright.sync_api import sync_playwright
TOL=float(os.environ.get('TOL','0.05'))
JS='''(tol)=>{const out=[];let n=0;const C=document.createElement('canvas').getContext('2d');
 document.querySelectorAll('.ch,.rkb').forEach(t=>{if(!t.offsetParent||t.closest('.gm,.sxm,.lbr,.hmx,.tqgrid,.mx,.bym'))return;
  const ps=getComputedStyle(t.parentElement);if(ps.display.includes('flex')&&ps.flexDirection.startsWith('column'))return;
  let s=t.previousSibling;while(s&&s.nodeType===3&&!s.textContent.trim())s=s.previousSibling;
  if(!s||s.nodeType===1&&s.matches('.ch,.rkb,svg,.av,.pav,.pz,.nfl,.pba,img'))return;
  const w=s.nodeType===3?null:document.createTreeWalker(s,NodeFilter.SHOW_TEXT);let tn=s.nodeType===3?s:null,x;
  if(w)while(x=w.nextNode())if(x.textContent.trim()&&!x.parentElement.closest('.lku'))tn=x;
  if(!tn||!/[0-9]/.test(tn.textContent))return;
  const el=tn.parentElement,cs=getComputedStyle(el);C.font=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;
  const cap=C.measureText('0123456789').actualBoundingBoxAscent*(el.currentCSSZoom||1);
  const pb=document.createElement('i');pb.style.cssText='display:inline-block;width:0;height:0;padding:0;margin:0;border:0;vertical-align:baseline';
  tn.after(pb);const base=pb.getBoundingClientRect().bottom;pb.remove();const top=base-cap;
  const g=document.createRange();g.selectNodeContents(tn);const rr=g.getBoundingClientRect(),tr=t.getBoundingClientRect();
  const lab=(t.parentElement.className||t.parentElement.parentElement.className||'').slice(0,14)+' "'+tn.textContent.trim().slice(-8)+'"|'+t.textContent.trim();
  if(tr.bottom<=rr.top||tr.top>=rr.bottom){if(t.closest('.sb,.st'))out.push(lab+' off line');return}
  n++;const up=top-tr.top,dn=tr.bottom-base;  // up>0: pokes above the cap top; dn>0: below the baseline; <0: short of it
  if(Math.abs(up)>tol||Math.abs(dn)>tol)out.push(lab+' top '+(-up).toFixed(2)+' bottom '+dn.toFixed(2))});
 return {n,out}}'''
U={'bbp':'/home/claude/dynasty-tracker/site/index.html','yilm':'/home/claude/yilm-tracker.github.io/.season/2026/site/index.html'}
bad=0
with sync_playwright() as p:
    b=p.chromium.launch()
    for k,u in U.items():
      for w in [int(a) for a in (sys.argv[1:] or ['402','440','360','1440'])]:
        pg=b.new_page(viewport={'width':w,'height':1800});pg.route('**/api.sleeper.app/**',lambda r:r.abort());realfonts.setup(pg);pg.goto('file://'+u);pg.wait_for_timeout(1500)
        for st in ('Dumb','Nerd'):  # the page loads in Dumb; click the other level and check again
          pg.click('label[for="%s"]'%('dn-lean' if st=='Dumb' else 'dn-full'));pg.wait_for_timeout(800)
          res=pg.evaluate(JS,TOL);bad+=len(res['out'])
          print(k,w,st,len(res['out']),'violations of',res['n'],'tiles');[print('   ',x) for x in res['out'][:12]]
        pg.close()
    b.close()
print('TOTAL',bad,'violations (tolerance %.2fpx)'%TOL);sys.exit(1 if bad else 0)
