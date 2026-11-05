# WebKit (WebKitGTK 2.52, same engine as Safari) memory probe for the trackers.
# A fresh MiniBrowser per measurement; memory = sum over its WebKitWebProcess children, read from /proc/<pid>/smaps_rollup.
#   USS = Private_Clean + Private_Dirty (memory only this page's process holds; closest to macOS footprint), RSS also reported.
# Usage: wkmem.py <url> <width> [tabs...]  -> one JSON line per state ("load", then each tab id opened in turn)
# Needs Xvfb on $DISPLAY.
import sys, os, json, time, glob, subprocess
from selenium import webdriver
from selenium.webdriver.webkitgtk.options import Options
from selenium.webdriver.webkitgtk.service import Service

MB = '/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/MiniBrowser'
SETTLE = float(os.environ.get('SETTLE', '6'))

def kids(pid):
    out = []
    for p in glob.glob('/proc/[0-9]*'):
        try:
            st = open(p + '/stat').read().rsplit(')', 1)[1].split()
            if int(st[1]) == pid: out.append(int(p[6:]))
        except Exception: pass
    return out

def tree(pid):
    r = [pid]
    for k in kids(pid): r += tree(k)
    return r

def mem(root):
    tot = {'uss': 0, 'rss': 0, 'pss': 0, 'n': 0}
    for p in tree(root):
        try:
            if 'WebKitWebProcess' not in open(f'/proc/{p}/cmdline').read(): continue
            d = {}
            for l in open(f'/proc/{p}/smaps_rollup'):
                k, *v = l.split()
                if v and v[-1] == 'kB': d[k.rstrip(':')] = int(v[0])
            tot['uss'] += d.get('Private_Clean', 0) + d.get('Private_Dirty', 0)
            tot['rss'] += d.get('Rss', 0); tot['pss'] += d.get('Pss', 0); tot['n'] += 1
        except Exception: pass
    return {k: (round(v / 1024, 1) if k != 'n' else v) for k, v in tot.items()}

def run(url, width, tabs):
    o = Options(); o.binary_location = MB
    o.add_argument('--automation')
    s = Service(executable_path='/usr/bin/WebKitWebDriver')
    d = webdriver.WebKitGTK(options=o, service=s)
    root = s.process.pid
    try:
        d.set_window_size(max(width + 60, 600), 1100)
        base, page = url.rsplit('/', 1)
        d.get(f'{base}/__frame.html?w={width}&u={page}')
        time.sleep(1); d.switch_to.frame('f')
        for _ in range(100):
            if d.execute_script('return document.readyState') == 'complete': break
            time.sleep(.2)
        d.execute_async_script('const cb=arguments[arguments.length-1];(document.fonts?document.fonts.ready:Promise.resolve()).then(()=>cb())')
        time.sleep(SETTLE)
        info = d.execute_script('return [innerWidth, document.getElementsByTagName("*").length, document.fonts?[...document.fonts].filter(f=>f.status==="loaded").length:-1]')
        out = [dict(state='load', w=info[0], els=info[1], fonts=info[2], **mem(root))]
        for k in range(int(os.environ.get('REFIT','0'))):
            d.execute_script('for(let i=0;i<3;i++)window.__fitAll&&window.__fitAll()'); time.sleep(SETTLE)
            out.append(dict(state=f'refit x{3*(k+1)}', **mem(root)))
        for t in tabs:
            d.execute_script('const l=document.querySelector(\'label[for="\'+arguments[0]+\'"]\');if(l)l.click()', t)
            time.sleep(SETTLE)
            els = d.execute_script('return document.getElementsByTagName("*").length')
            out.append(dict(state=t, els=els, **mem(root)))
        return out
    finally:
        d.quit()

if __name__ == '__main__':
    for r in run(sys.argv[1], int(sys.argv[2]), sys.argv[3:]): print(json.dumps(r), flush=True)
