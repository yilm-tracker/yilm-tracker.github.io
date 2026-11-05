# QA: full-page captures of every tab (plus Standings with Nerd on) for before/after pixel comparison.
# Usage: python3 tools/shots.py <site url> <out dir> [widths...]      e.g. shots.py http://localhost:8801/index.html /tmp/before 402 1440
#        python3 tools/shots.py --cmp <dir a> <dir b>                  -> per capture: identical / N pixels differ; exit 1 on any difference
# Serve the built site over http (chunks are fetched): python3 -m http.server in site/ (YILM .season/2026/site/). Real fonts via realfonts.
import os, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cmp(a, b):
    from PIL import Image, ImageChops
    names = sorted(set(os.listdir(a)) | set(os.listdir(b))); bad = 0
    for n in names:
        if not n.endswith('.png'): continue
        if not (os.path.exists(f'{a}/{n}') and os.path.exists(f'{b}/{n}')): print(f'{n}: missing on one side'); bad += 1; continue
        A, B = Image.open(f'{a}/{n}').convert('RGB'), Image.open(f'{b}/{n}').convert('RGB')
        if A.size != B.size: print(f'{n}: size {A.size} vs {B.size}'); bad += 1; continue
        D = ImageChops.difference(A, B); mx = max(e[1] for e in D.getextrema())
        d = D.convert('L').point(lambda v: 255 if v else 0); k = d.histogram()[255]
        print(f'{n}: ' + ('identical' if not mx else f'{k} pixels differ (max {mx}/255), box {d.getbbox()}')); bad += bool(mx)
    print(f'{len([n for n in names if n.endswith(".png")])} captures, {bad} differ'); return bad

def shoot(url, out, widths):
    import realfonts
    from playwright.sync_api import sync_playwright
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w in widths:
            pg = b.new_page(viewport={'width': w, 'height': 900}); realfonts.setup(pg)
            pg.goto(url); pg.evaluate('()=>document.fonts.ready'); pg.wait_for_timeout(1500)
            tabs = pg.evaluate("()=>[...document.querySelectorAll('input[name=tab]')].map(i=>i.id)")
            states = [(t, t) for t in tabs] + [('tab-st', 'tab-st-nerd')]
            for tab, name in states:
                pg.evaluate("(id)=>{const l=document.querySelector('label[for=\"'+id+'\"]');l.click()}", tab)
                if name.endswith('-nerd'): pg.evaluate("()=>document.querySelector('label[for=\"gl-s\"]').click()")
                pg.wait_for_timeout(1800); pg.evaluate('()=>window.scrollTo(0,0)'); pg.wait_for_timeout(200)
                pg.screenshot(path=f'{out}/{w}_{name}.png', full_page=True, animations='disabled')
                if name.endswith('-nerd'): pg.evaluate("()=>document.querySelector('label[for=\"gl-h\"]').click()")
                print(w, name, hashlib.sha256(open(f'{out}/{w}_{name}.png', 'rb').read()).hexdigest()[:12], flush=True)
            pg.close()
        b.close()

if __name__ == '__main__':
    if sys.argv[1] == '--cmp': sys.exit(1 if cmp(sys.argv[2], sys.argv[3]) else 0)
    shoot(sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]] or [402, 1440])
