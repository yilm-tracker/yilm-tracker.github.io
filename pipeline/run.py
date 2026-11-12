# Orchestrates the tracker build. Run from anywhere:
#   python3 pipeline/run.py weekly [--force]   after a week completes: pull, refresh season data, rebuild site
#   python3 pipeline/run.py live               in-week: pull live scores for the current week, rebuild site
#   python3 pipeline/run.py build              rebuild site from the committed data only (no network)
import json,os,re,subprocess,sys
P=os.path.dirname(os.path.abspath(__file__))+'/'
def sh(*c):
    print('>',' '.join(c),flush=True);subprocess.run(c,check=True,cwd=P)
def G():return int(re.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))
def build():
    sh('python3',P+'rebuild.py');sh('node',P+'gen.js');sh('python3',P+'build_static.py');sh('python3',P+'build_site.py')
mode=sys.argv[1] if len(sys.argv)>1 else 'build';force='--force' in sys.argv
if mode in('weekly','history') and (mode=='history' or not os.path.exists(P+'history/manifest.json')):
    subprocess.run(['node',P+'history.mjs'],cwd=P)  # never fatal; one-time import of past seasons (MFL 2021-24, Sleeper 2025)
    if mode=='history':mode='weekly'
if mode=='weekly':
    st=json.loads(subprocess.run(['node',P+'pull.mjs','state'],check=True,cwd=P,capture_output=True,text=True).stdout)
    D=st['done'];have=G()
    print('last complete week',D,'; data through week',have)
    if D>14:D=14  # regular season ends at week 14; playoffs are projected separately
    if D<=have and not force:
        print('nothing new to process; refreshing playoff projections and rebuilding')
    else:
        for w in range(have+1,D+1) if D>have else [D]:
            # final scores and stat lines for week w (what the in-week updates show), then the season refresh
            sh('node',P+'pull.mjs','live',str(w));sh('python3',P+'score.py',P+'live.json','--no-build')
            sh('node',P+'pull.mjs','weekly',str(w));sh('python3',P+'full_update.py',str(w))
    sh('node',P+'pull.mjs','playoffs');sh('python3',P+'po_write.py')
    if D<=have and not force:  # mid-week rebuild (e.g. a code push): keep the current week's live scores instead of resetting them
        if subprocess.run(['node',P+'pull.mjs','live',str(G()+1)],cwd=P).returncode==0:subprocess.run(['python3',P+'score.py',P+'live.json','--no-build'],cwd=P)
    subprocess.run(['node',P+'pull.mjs','faab'],cwd=P)  # FAAB balances (never fatal)
    subprocess.run(['node',P+'pull.mjs','wire',str(G())],cwd=P)  # THE WIRE (never fatal)
    subprocess.run(['node',P+'pull.mjs','top',str(G())],cwd=P)  # Players tab: top players by position (never fatal)
    sh('node',P+'pull.mjs','detail',f'1-{G()+1}')  # full stat lines for the Detailed view (all played weeks + current)
    # current NFL teams (trades/signings since the last completed-week pull) into the current week's files; never fatal
    if subprocess.run(['node',P+'pull.mjs','teams',str(G()+1),'full'],cwd=P).returncode==0:subprocess.run(['python3',P+'teams.py'],cwd=P)
    build()
elif mode=='live':
    W=G()+1
    # NFL team changes since the last weekly run (players map read only when week W's projections differ); never fatal
    if subprocess.run(['node',P+'pull.mjs','teams',str(W)],cwd=P).returncode==0:subprocess.run(['python3',P+'teams.py'],cwd=P)
    sh('node',P+'pull.mjs','live',str(W))
    subprocess.run(['node',P+'pull.mjs','detail',str(W)],cwd=P)  # Detailed view; never fatal
    subprocess.run(['node',P+'pull.mjs','faab'],cwd=P)  # FAAB balances; never fatal
    # THE WIRE between weekly runs (waivers, injuries): re-pull when the last pull is over 2 hours old; never fatal
    import datetime as _dtw
    try:
        _pw=json.load(open(P+'pull_wire.json'))['pulled'] if os.path.exists(P+'pull_wire.json') else None
        _old=not _pw or (_dtw.datetime.now(_dtw.timezone.utc)-_dtw.datetime.fromisoformat(_pw.replace('Z','+00:00'))).total_seconds()>7200
    except Exception:_old=True
    # live runs do not save data, so the committed pull stays old: limit re-pulls to the first 10 minutes of each hour
    if _old and _dtw.datetime.now().minute<10:subprocess.run(['node',P+'pull.mjs','wire',str(G())],cwd=P)
    sh('python3',P+'score.py',P+'live.json')  # applies scores and runs rebuild/gen/build_static
    sh('python3',P+'build_site.py')
else:
    build()
if os.path.exists(P+'history/log.json') and os.path.isdir(P+'../site'):
    import shutil;shutil.copy(P+'history/log.json',P+'../site/history_log.json')
