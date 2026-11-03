# QA: standings name block per row (font size, height, clipping) at 402/440/360/1440, plus 402/440/360 crops.
import sys;sys.path.insert(0,'/home/claude/yilm-tracker.github.io/tools');import realfonts
import sys,json
from playwright.sync_api import sync_playwright
pages={'bbp':'file:///home/claude/dynasty-tracker/site/index.html','yilm':'file:///home/claude/yilm-tracker.github.io/.season/2026/site/index.html'}
out='/tmp/qa_'
with sync_playwright() as p:
    b=p.chromium.launch()
    for k,u in pages.items():
        for w in (402,440,360,1440):
            pg=b.new_page(viewport={'width':w,'height':1800},device_scale_factor=3 if w<1000 else 1)
            pg.route('**/api.sleeper.app/**',lambda r:r.abort());realfonts.setup(pg)
            pg.goto(u);pg.wait_for_timeout(1500)
            r=pg.evaluate('''()=>{const o={sw:document.documentElement.scrollWidth,rows:[]};
              document.querySelectorAll('.board .r').forEach(r=>{const n=r.querySelector('.nm'),t=n.querySelector('.tn'),v=n.querySelector('.mv'),f=n.querySelector('.fab'),s=r.querySelector('.side');
                const R=e=>e?e.getBoundingClientRect():null,tr=R(t),vr=R(v),fr=R(f),nr=R(n),sr=R(s);
                o.rows.push([t.textContent,getComputedStyle(t).fontSize,Math.round(tr.height),t.scrollWidth>t.clientWidth+.5?'CLIP':'',vr?Math.round(vr.left-tr.right):null,fr?Math.round(fr.top-tr.bottom):null,fr?Math.round(sr.left-fr.right):null,fr?(fr.right<=nr.right+.5?'in':'OUT'):''])});return o}''')
            print(k,w,'scrollW',r['sw'])
            for x in r['rows']:print('  ',x)
            if w in(402,440,360):
                pg.locator('.board .r').nth(0).scroll_into_view_if_needed()
                el=pg.locator('#list')
                bb=pg.evaluate("(()=>{const a=document.querySelectorAll('.board .r');const r1=a[0].getBoundingClientRect(),r2=a[3].getBoundingClientRect();return [r1.top+scrollY,r2.bottom+scrollY]})()")
                pg.screenshot(path=f'{out}fab_{k}_{w}.png',full_page=True,clip={'x':0,'y':bb[0]-4,'width':w,'height':bb[1]-bb[0]+8})
            pg.close()
    b.close()
