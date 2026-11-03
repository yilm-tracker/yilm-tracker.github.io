# QA: standings name blocks only (stat rows hidden), 402 and 440, both trackers -> /tmp/qa_nl_<tracker>_<w>.png
import sys;sys.path.insert(0,'/home/claude/yilm-tracker.github.io/tools');import realfonts
from playwright.sync_api import sync_playwright
out='/tmp/qa_'
with sync_playwright() as p:
    b=p.chromium.launch()
    for k,u in {'bbp':'file:///home/claude/dynasty-tracker/site/index.html','yilm':'file:///home/claude/yilm-tracker.github.io/.season/2026/site/index.html'}.items():
      for w in (402,440):
        pg=b.new_page(viewport={'width':w,'height':1800},device_scale_factor=3);pg.route('**/api.sleeper.app/**',lambda r:r.abort());realfonts.setup(pg);pg.goto(u);pg.wait_for_timeout(1200)
        # collapse to just the name lines: hide everything in rows except rank/name/side head
        pg.add_style_tag(content='.board .r>*:not(.rk):not(.nm):not(.side):not(.rav):not(.hl){display:none!important}.board .r .side>*:not(.rr){display:none!important}.tier{display:none!important}')
        pg.wait_for_timeout(300);pg.evaluate('tnFit()')
        bb=pg.evaluate("(()=>{const a=document.querySelectorAll('.board .r');return [a[0].getBoundingClientRect().top+scrollY,a[a.length-1].getBoundingClientRect().bottom+scrollY]})()")
        pg.screenshot(path=f'{out}nl_{k}_{w}.png',full_page=True,clip={'x':0,'y':bb[0],'width':w,'height':bb[1]-bb[0]})
        pg.close()
    b.close()
