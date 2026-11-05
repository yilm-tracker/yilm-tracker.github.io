# Leak check: load the page, open every tab in turn, return to Standings, wait for dropped tabs to be discarded, force GC,
# take a Chromium heap snapshot and report what stays in memory.
# Usage: python3 tools/mem/leaks.py <url> <width> [--json out.json]     (serve the built site over http; real fonts)
#  - DOM counters (Memory.getDOMCounters: live nodes incl. detached, JS event listeners) and JS heap, at load and at the end
#  - heap self size by object type, at load and at the end (what grew)
#  - detached DOM trees (detachedness flag), each with its shortest retaining path to a GC root (what holds it)
import sys, os, json, time, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import realfonts
from playwright.sync_api import sync_playwright

def snapshot(cdp):
    chunks = []
    cdp.on('HeapProfiler.addHeapSnapshotChunk', lambda e: chunks.append(e['chunk']))
    cdp.send('HeapProfiler.takeHeapSnapshot', {'reportProgress': False, 'captureNumericValue': False})
    return json.loads(''.join(chunks))

DOMNAMES = ('<', 'Text', 'Comment', 'DocumentFragment', 'Detached ')

def analyse(s, trees=True):
    m = s['snapshot']['meta']; nf = m['node_fields']; ef = m['edge_fields']
    ntypes = m['node_types'][0]; etypes = m['edge_types'][0]; strings = s['strings']
    N, E = s['nodes'], s['edges']; NF, EF = len(nf), len(ef)
    iT, iN, iS, iE = nf.index('type'), nf.index('name'), nf.index('self_size'), nf.index('edge_count')
    iD = nf.index('detachedness') if 'detachedness' in nf else None
    eT, eN, eTo = ef.index('type'), ef.index('name_or_index'), ef.index('to_node')
    n = len(N) // NF
    name = lambda i: strings[N[i * NF + iN]]
    typ = lambda i: ntypes[N[i * NF + iT]]
    size = lambda i: N[i * NF + iS]
    bytype = collections.Counter()
    for i in range(n):
        t = typ(i); bytype['native DOM' if t == 'native' and name(i).startswith(DOMNAMES) else t] += size(i)
    out = {'heap_objects': n, 'by_type_mb': {k: round(v / 1e6, 2) for k, v in bytype.most_common()}}
    if not trees: return out
    isdom = lambda i: typ(i) == 'native' and name(i).startswith(DOMNAMES)
    det = [isdom(i) and ((N[i * NF + iD] == 2) if iD is not None else name(i).startswith('Detached ')) for i in range(n)]
    rev = collections.defaultdict(list); e0 = 0
    for i in range(n):
        for k in range(N[i * NF + iE]):
            j = e0 + k * EF; et = etypes[E[j + eT]]
            if et != 'weak':
                en = strings[E[j + eN]] if et in ('context', 'property', 'internal', 'shortcut') else str(E[j + eN])
                rev[E[j + eTo] // NF].append((i, et, en))
        e0 += N[i * NF + iE] * EF
    D = [i for i in range(n) if det[i]]
    par = {i: i for i in D}
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for i in D:
        for (h, _, _) in rev[i]:
            if h in par: par[f(h)] = f(i)
    comps = collections.defaultdict(list)
    for i in D: comps[f(i)].append(i)
    def path_to_root(mem):  # BFS up the retainers (no weak edges) from the tree until a GC root
        seen = set(mem); q = collections.deque((i, None) for i in mem); prev = {}
        while q:
            x, _ = q.popleft()
            for (h, et, en) in rev[x]:
                if h in seen: continue
                seen.add(h); prev[h] = (x, et, en)
                if typ(h) == 'synthetic':
                    p = []; y = h
                    while y in prev:
                        c, et2, en2 = prev[y]; p.append(f'{typ(y)}:{name(y)[:40]} --{en2}-->'); y = c
                    p.append(f'{name(y)[:40]}'); return p
                q.append((h, None))
        return ['(no path to a root: garbage not yet collected)']
    rows = []
    for _, mem in sorted(comps.items(), key=lambda kv: -len(kv[1])):
        frag = any(name(i).startswith('DocumentFragment') for i in mem)
        rows.append({'nodes': len(mem), 'parked': frag, 'sample': name(max(mem, key=lambda i: len(rev[i])))[:60],
                     'path': path_to_root(mem) if len(rows) < 25 else None})
    out.update({'detached': len(D), 'trees': rows,
                'parked_nodes': sum(r['nodes'] for r in rows if r['parked']), 'other_nodes': sum(r['nodes'] for r in rows if not r['parked'])})
    return out

def counters(cdp):
    c = cdp.send('Memory.getDOMCounters'); h = cdp.send('Runtime.getHeapUsage')
    return {'nodes': c['nodes'], 'listeners': c['jsEventListeners'], 'documents': c['documents'], 'js_heap_mb': round(h['usedSize'] / 1e6, 1)}

def gc(cdp):
    for _ in range(3): cdp.send('HeapProfiler.collectGarbage')
    time.sleep(.5)

def run(url, W, tabs=None, home='tab-st'):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': 1000}); realfonts.setup(pg)
        cdp = pg.context.new_cdp_session(pg); cdp.send('HeapProfiler.enable')
        pg.goto(url); pg.evaluate('()=>document.fonts.ready'); time.sleep(3); gc(cdp)
        r = {'load': counters(cdp), 'load_heap': analyse(snapshot(cdp), trees=False)}
        tabs = tabs or pg.evaluate("()=>[...document.querySelectorAll('input[name=tab]')].map(i=>i.id).filter(i=>i!=='tab-st')")
        for t in tabs + [home]:
            pg.evaluate("(id)=>document.querySelector('label[for=\"'+id+'\"]').click()", t); time.sleep(3)
        time.sleep(3); gc(cdp)  # dropped tabs are discarded 1.5s after leaving
        r['end'] = counters(cdp); r['end_heap'] = analyse(snapshot(cdp)); r['tabs'] = tabs
        r['on_page'] = pg.evaluate('()=>document.getElementsByTagName("*").length')
        b.close(); return r

if __name__ == '__main__':
    r = run(sys.argv[1], int(sys.argv[2]))
    if '--json' in sys.argv: json.dump(r, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    print('load:', r['load']); print('end: ', r['end'], ' elements in the document:', r['on_page'])
    print('heap by type, load:', r['load_heap']['by_type_mb']); print('heap by type, end: ', r['end_heap']['by_type_mb'])
    e = r['end_heap']; print(f"detached DOM nodes: {e['detached']}  (in parked panes: {e['parked_nodes']}, elsewhere: {e['other_nodes']})")
    for t in e['trees'][:25]:
        print(f"{t['nodes']:6} {'PARKED ' if t['parked'] else 'other  '} {t['sample']}")
        if t['path']: print('          ' + ' '.join(reversed(t['path']))[:400])
