# Chromium counterpart of wkmem.py: renderer process private memory (USS) on load, then after each tab opened in turn.
# Usage: chmem.py <url> <width> [tabs...]   GC=1: force a full garbage collection before each reading (stable figures)
import sys, os, json, time, glob
sys.path.insert(0, '/home/claude/dynasty-tracker/tools'); import realfonts
from playwright.sync_api import sync_playwright
SETTLE = float(os.environ.get('SETTLE', '5')); GC = os.environ.get('GC') == '1'
def renderers():
    out = set()
    for p in glob.glob('/proc/[0-9]*'):
        try:
            c = open(p + '/cmdline').read()
            if '--type=renderer' in c: out.add(int(p[6:]))
        except Exception: pass
    return out
def uss(pids):
    t = 0
    for p in pids:
        try:
            for l in open(f'/proc/{p}/smaps_rollup'):
                if l.startswith(('Private_Clean', 'Private_Dirty')): t += int(l.split()[1])
        except Exception: pass
    return round(t / 1024, 1)
url, W, tabs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
with sync_playwright() as p:
    before = renderers(); b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': 1000}); realfonts.setup(pg)
    cdp = pg.context.new_cdp_session(pg)
    def gc():
        if GC:
            for _ in range(2): cdp.send('HeapProfiler.collectGarbage')
            time.sleep(1)
    pg.goto(url); pg.evaluate('()=>document.fonts.ready'); time.sleep(SETTLE); gc()
    mine = renderers() - before
    print(json.dumps(dict(state='load', els=pg.evaluate('()=>document.getElementsByTagName("*").length'), uss=uss(mine))), flush=True)
    for t in tabs:
        pg.evaluate("(id)=>{const l=document.querySelector('label[for=\"'+id+'\"]');if(l)l.click()}", t); time.sleep(SETTLE); gc()
        mine = renderers() - before
        print(json.dumps(dict(state=t, els=pg.evaluate('()=>document.getElementsByTagName("*").length'), uss=uss(mine))), flush=True)
    b.close()
