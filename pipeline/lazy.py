# On-demand tabs (2026-11-04, Nicklaus): every tab pane except the one shown on load is cut out of index.html into its
# own file, site/p/<pane>.<content hash>.html, and fetched when the tab is first opened (lazy.js). Matchups is cut
# further: the shell (switches, week menu) is one file and each week's games another, so only the selected week is
# built. A changed chunk gets a new name, so a cached old chunk can never load into a new page.
# The <style> blocks found inside a cut pane are global (readability.css ends up inside the Stats pane) and stay in
# index.html, in their original order, just after the last pane. Past seasons and the download file are not cut.
# Playoffs (shown on load in Weeks 15-17) is cut one level deeper: each bracket game panel and each team panel except
# the one selected by default is its own file (data-lzs = file, data-lzr = the radio that shows it), so the page stays
# under the 20,000-element budget (DESIGN.md §7) when Playoffs is the opening tab.
import re,hashlib,os,json,shutil

_SCAN=re.compile(r'<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->|<div\b|</div>',re.S)
_STYLE=re.compile(r'<style\b.*?</style>',re.S)
HEAVY=('mu','cm','ro')   # rebuilt on each visit and discarded ~1.5s after leaving (lazy.js)
SUBS={'po':(('bkp','bk'),('psp','ps'))}  # pane: (panel class, radio prefix): <div class="bkp bkp-qf1"> shown by #bk-qf1
KEEP_BUILDS=6            # chunk files of the last N changed builds stay published (pages left open across a deploy)


def _close(s,i):
    """index of the </div> that closes the <div> whose content starts at i"""
    d=1
    for t in _SCAN.finditer(s,i):
        x=t.group(0)
        if x=='<div':d+=1
        elif x=='</div>':
            d-=1
            if d==0:return t.start()
    raise ValueError('unbalanced div after %d'%i)


def _strip_styles(h,keep):
    """move every <style> outside scripts out of h (appended to keep, in order)"""
    out=[];j=0
    for t in _SCAN.finditer(h):
        if t.group(0).startswith('<style'):out.append(h[j:t.start()]);keep.append(t.group(0));j=t.end()
    out.append(h[j:]);return ''.join(out)


def _name(pid,h):return f'p/{pid}.{hashlib.sha256(h.encode("utf-8")).hexdigest()[:10]}.html'


def _subcut(pid,h,files,styles):
    """cut the radio-selected panels of pane pid (SUBS) out of h, except the ones checked by default"""
    for cls,pfx in SUBS.get(pid,()):
        on=set(re.findall(r'<input type="radio" name="%s" id="([^"]+)"[^>]*\bchecked\b'%re.escape(pfx),h))
        parts=[];j=0
        for m in re.finditer(r'<div class="%s %s-([\w-]+)"([^>]*)>'%(cls,cls),h):
            rid=f'{pfx}-{m.group(1)}'
            if m.start()<j or rid in on:continue
            e=_close(h,m.end());sub=_strip_styles(h[m.end():e],styles);fn=_name(f'{pid}-{cls}-{m.group(1)}',sub);files[fn]=sub
            parts.append(h[j:m.start()]+f'<div class="{cls} {cls}-{m.group(1)}"{m.group(2)} data-lzs="{fn}" data-lzr="{rid}">');j=e
        parts.append(h[j:]);h=''.join(parts)
    return h


def chunk(s,out,inline=('st',)):
    """cut the panes of page s; write the chunks under out/p; return (page, manifest)"""
    panes=[]
    for m in re.finditer(r'<div class="pane pane-(\w+)">',s):
        panes.append((m.group(1),m.end(),_close(s,m.end())))
    if not panes:return s,None
    files={};man={'p':{},'w':{},'h':list(HEAVY)};styles=[];cut=[]
    for pid,a,b in panes:
        if pid in inline:
            if pid in SUBS:cut.append((a,b,_subcut(pid,s[a:b],files,styles)))
            continue
        h=_subcut(pid,_strip_styles(s[a:b],styles),files,styles)
        if pid=='mu':  # one file per week; the shell keeps each week's empty <div class="mwx mwx-N">
            parts=[];j=0
            for m in re.finditer(r'<div class="mwx mwx-(\d+)">',h):
                if m.start()<j:continue
                e=_close(h,m.end());wk=h[m.end():e];fn=_name(f'mu-w{m.group(1)}',wk)
                files[fn]=wk;man['w'][m.group(1)]=fn;parts.append(h[j:m.end()]);j=e
            parts.append(h[j:]);h=''.join(parts)
        fn=_name(pid,h);files[fn]=h;man['p'][pid]=fn;cut.append((a,b,''))
    # rebuild the page without the cut contents; the panes' styles go after the last pane, before the next script
    o=[];j=0
    for a,b,r in cut:o.append(s[j:a]+r);j=b
    o.append(s[j:]);s2=''.join(o)
    if styles:
        last=[m.end() for m in re.finditer(r'<div class="pane pane-\w+">',s2)][-1];e=_close(s2,last)+len('</div>')
        k=s2.find('<script',e);k=e if k<0 else k
        s2=s2[:k]+''.join(styles)+'\n'+s2[k:]
    pdir=os.path.join(out,'p');shutil.rmtree(pdir,ignore_errors=True);os.makedirs(pdir)
    for fn,h in files.items():open(os.path.join(out,fn),'w',encoding='utf-8').write(h)
    _retain(out,list(files))
    return s2,man


def _retain(out,names):
    """keep the previous builds' chunks published (DT_CHUNKS = a directory kept between CI runs)"""
    keep=os.environ.get('DT_CHUNKS')
    if not keep:return
    fdir=os.path.join(keep,'files');os.makedirs(fdir,exist_ok=True);lp=os.path.join(keep,'builds.json')
    try:builds=json.load(open(lp))
    except Exception:builds=[]
    for n in names:
        b=os.path.basename(n)
        if not os.path.exists(os.path.join(fdir,b)):shutil.copy(os.path.join(out,n),os.path.join(fdir,b))
    cur=sorted(os.path.basename(n) for n in names)
    if not builds or sorted(builds[-1])!=cur:builds=(builds+[cur])[-KEEP_BUILDS:]  # an unchanged rebuild is not a new build
    want=set(x for bl in builds for x in bl)
    for b in os.listdir(fdir):
        if b not in want:os.remove(os.path.join(fdir,b))
        elif not os.path.exists(os.path.join(out,'p',b)):shutil.copy(os.path.join(fdir,b),os.path.join(out,'p',b))
    json.dump(builds,open(lp,'w'))
