# Rebuild a finished Sleeper season with the real weekly pipeline, offline.
#   python3 pipeline/season_replay.py 2025 1207898992206155776
# Copies pipeline/ into .season/<year>/pipeline, seeds a "before Week 1" state from history/raw/<year> (captured by
# pull_season.mjs), then replays Weeks 1..14 exactly as the live tracker ran them (live pull -> score.py, weekly pull ->
# full_update.py) with every Sleeper request answered from the capture. Finally builds the site into .season/<year>/site.
import os,sys,json,gzip,shutil,subprocess,csv,re,datetime
Y,LID=sys.argv[1],sys.argv[2]
SRC=os.path.dirname(os.path.abspath(__file__));REPO=os.path.dirname(SRC)
ROOT=os.path.join(REPO,'.season',Y);WS=os.path.join(ROOT,'pipeline');RAW=os.path.join(SRC,'history','raw',Y)
REG=14
def log(*a):print('[season]',*a,flush=True)
# ---------- workspace
BO='--build-only' in sys.argv  # re-sync code into an existing replay and rebuild the site only
if BO:
    for f in os.listdir(SRC):
        if re.search(r'\.(py|js|mjs|html|css)$',f) and f!='data_block.js' and not re.match(r'.*_(section|css)\.|standings\.html|DynastyStandings|po_static',f):
            shutil.copy(os.path.join(SRC,f),os.path.join(WS,f))
else:
    if os.path.isdir(ROOT):shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    shutil.copytree(SRC,WS,ignore=shutil.ignore_patterns('raw','__pycache__','teamhub','.cache','node_modules','*_section.html','*_css.css','po_static.*','standings.html','DynastyStandings.html','lists.json','live.json'))
    if os.path.isdir(os.path.join(SRC,'node_modules')):os.symlink(os.path.join(SRC,'node_modules'),os.path.join(WS,'node_modules'))
YEARS=','.join(['2026']+sorted([d for d in os.listdir(os.path.join(SRC,'history','raw')) if d.isdigit() and d!='2026'],reverse=True))
# the capture's players map is today's (teams, injuries): make it that season's. NFL team = his last team in that
# season's weekly stats (else projections); no injury tags. Written to .season/<year>/raw, with the rest linked.
RAWX=os.path.join(ROOT,'raw')
if not BO:
    os.makedirs(RAWX)
    for k in ('core','stats','proj'):os.symlink(os.path.join(RAW,k+'.json.gz'),os.path.join(RAWX,k+'.json.gz'))
    _pm=json.load(gzip.open(os.path.join(RAW,'players.json.gz')));_u=next(iter(_pm));_pl=_pm[_u];last={}
    for k in ('proj','stats'):  # stats last, so a real game's team wins
        _d=json.load(gzip.open(os.path.join(RAW,k+'.json.gz')))
        for u in sorted(_d,key=lambda u:int(re.search(r'/(\d+)\?',u).group(1))):
            for r in _d[u]:
                if r.get('team') and (k=='proj' or (r.get('stats') or {}).get('gp')):last[r['player_id']]=r['team']
    for pid,p_ in _pl.items():
        if pid in last:p_['team']=last[pid]
        p_['injury_status']=None
    with gzip.open(os.path.join(RAWX,'players.json.gz'),'wt',encoding='utf-8') as f:json.dump(_pm,f)
ENV=dict(os.environ,DT_CACHE=RAWX,DT_SEASON=Y,DT_LEAGUE=LID,DT_PAST='1',DT_YEARS=YEARS)
def node(*a):subprocess.run(['node',os.path.join(WS,'pull.mjs'),*map(str,a)],cwd=WS,env=ENV,check=True,stdout=subprocess.DEVNULL)
def py(f,*a):subprocess.run(['python3',os.path.join(WS,f),*map(str,a)],cwd=WS,env=ENV,check=True,stdout=subprocess.DEVNULL)
J=lambda f:json.load(open(os.path.join(WS,f),encoding='utf-8'))
def W_(f,o):json.dump(o,open(os.path.join(WS,f),'w',encoding='utf-8'),ensure_ascii=False)
C={}
for k in ('core','players'):C.update(json.load(gzip.open(os.path.join(RAWX,k+'.json.gz'))))
A='https://api.sleeper.app/v1';S='https://api.sleeper.com';L=f'{A}/league/{LID}'
LG=C[L];PL=C[f'{A}/players/nfl'];SCH=C[f'{S}/schedule/nfl/regular/{Y}']
RN={1:'Convicts',2:"Homer's Heroes",3:'Team Ram Rod',4:'Team RIPMFL',5:'Reverse Apache Master',6:'Canton waitlist',7:'Nuts in the Face',8:"Bill's Block Party",9:'Mandingoes',10:'Cheating is Trying'}
SH={1:"Convicts",2:"Homer's",3:"Ram Rod",4:"RIPMFL",5:"Apache",6:"Canton",7:"Nuts",8:"Bill's",9:"Mandingoes",10:"Cheating"}
# ---------- remove the current season's state
for f in ([] if BO else os.listdir(WS)):
    if re.match(r'(wk\d+|pull.*|po_home|po_proj|kick|weeks|stats|stats_detail|live|eff|skill_opt|ro_pg)\.json$',f):os.remove(os.path.join(WS,f))
# ---------- season constants that were hard-coded for 2026
teams_nfl=sorted({g['home'] for g in SCH}|{g['away'] for g in SCH})
bye={t:[w for w in range(1,19) if not any(g['week']==w and t in (g['home'],g['away']) for g in SCH)] for t in teams_nfl}
BYE={t:v[0] for t,v in bye.items() if v}
byeweeks=sorted(set(BYE.values()))
k1=min(g['date'] for g in SCH if g['week']==1)  # season opener date; Sunday 1 PM ET of week 1 = first Sunday on/after it
d=datetime.date.fromisoformat(k1);d+=datetime.timedelta(days=(6-d.weekday())%7)
def patch(f,a,b):
    p=os.path.join(WS,f);s=open(p,encoding='utf-8').read();assert a in s,(f,a[:60]);open(p,'w',encoding='utf-8').write(s.replace(a,b))
patch('rebuild.py','BYES={5,6,7,8,9,10,11,13,14}',f'BYES={set(w for w in byeweeks if w<=REG)}')
patch('sx_data.py','K1=datetime(2026,9,13,17,0,tzinfo=timezone.utc)',f'K1=datetime({d.year},{d.month},{d.day},17,0,tzinfo=timezone.utc)')
# ages as of the end of that season (New Year's Day after it), not today
for f in ('assess.py','cmp_build.py','mu_build.py','pl_build.py','po_build.py','ro_build.py','sx_data.py'):
    p_=os.path.join(WS,f);t_=open(p_,encoding='utf-8').read()
    t_=t_.replace('date.today()',f'date({int(Y)+1},1,1)').replace('_d.today()',f'_d({int(Y)+1},1,1)')
    open(p_,'w',encoding='utf-8').write(t_)
# ---------- seed files
if BO:
    subprocess.run(['python3',os.path.join(WS,'run.py'),'build'],cwd=WS,env=ENV,check=True);sys.exit()
fut={RN[r]:[] for r in RN}
for w in range(1,REG+1):
    by={}
    for m in C[f'{L}/matchups/{w}']:by.setdefault(m['matchup_id'],[]).append(m['roster_id'])
    for a,b in by.values():fut[RN[a]].append([w,SH[b],0,0,50]);fut[RN[b]].append([w,SH[a],0,0,50])
open(os.path.join(WS,'data_block.js'),'w',encoding='utf-8').write('const G=0;\nconst FUT='+json.dumps(fut,ensure_ascii=False,separators=(',',':'))+';\n')
W_('hist.json',{'m':{},'w':{}});W_('kick.json',{});W_('stats.json',{});W_('stats_detail.json',{})
X=J('cmp_extra.json')
X['rounds']=LG['settings'].get('draft_rounds',X['rounds'])
X['tp']=[[p['season'],p['round'],p['roster_id'],p['owner_id']] for p in C[f'{L}/traded_picks']]
tx=[];txp={}
for w in range(1,19):
    for t in C.get(f'{L}/transactions/{w}',[]):
        if t.get('type')!='trade' or t.get('status')!='complete':continue
        tx.append({'w':w,'ts':t['status_updated'],'rids':t['roster_ids'],'adds':t.get('adds') or {},
                   'picks':[[p['season'],p['round'],p['roster_id'],p['owner_id'],p['previous_owner_id']] for p in t.get('draft_picks') or []],
                   'faab':[{'amount':x['amount'],'sender':x['sender'],'receiver':x['receiver']} for x in t.get('waiver_budget') or []]})
        for pid in (t.get('adds') or {}):
            p=PL.get(pid) or {};nm=p.get('full_name') or f"{p.get('first_name','')} {p.get('last_name','')}".strip() or pid
            txp[pid]=[nm,p.get('position'),p.get('team')]
X['tx']=tx;X['txp']=txp;X['txw']={pid:[] for pid in txp};X['bench']={RN[r]:[] for r in RN};X['age']={}
W_('cmp_extra.json',X)
rows=list(csv.DictReader(open(os.path.join(WS,'pos','pos.csv'),encoding='utf-8')))
for r in rows:
    for k in r:
        if k not in('roster_id','team'):r[k]=0
with open(os.path.join(WS,'pos','pos.csv'),'w',encoding='utf-8',newline='') as f:
    w_=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w_.writeheader();w_.writerows(rows)
R0=J('rosters.json');W_('rosters.json',{k:[] for k in R0})
W_('ro_ranks.json',{'_bye':BYE})
# ---------- week 0 pull -> wk1.json (same as full_update step 6 with NOW = 1)
node('weekly',0)
X8=J('pull8.json');X8a=J('pull8a.json');M7=J('pull_m7.json')
PJ,META,S8,K8=X8['PJ'],X8['META'],X8['S8'],X8['K8'];RO={r['rid']:r for r in M7['RO']}
INJ=set()  # past season: no injury tags
home={h for w_,a_,h in S8 if w_==1};out={}
for rid,mid,st in X8a['m8']:
    r=RO[rid]
    def row(pid):
        m=META.get(pid) or [pid,'?',None,None,None];return [pid,m[1],m[0],m[2] or '',PJ.get(pid,[0,None])[0],0,PJ.get(pid,[0,None])[1],None]
    out[str(rid)]={'mid':mid,'pts':0,'st':[row(p) for p in st],'bn':[row(p) for p in r['pl'] if p not in st]}
W_('wk1.json',{'done':[],'out':out,'home':sorted(home),'done_note':'season replay'})
W_('kick.json',{'1':K8})
# ---------- replay weeks 1..14
for w in range(1,REG+1):
    node('live',w);py('score.py','live.json','--no-build')
    node('weekly',w);py('full_update.py',w)
    log('week',w,'ok')
node('detail',f'1-{REG}');node('top',REG);node('playoffs');py('po_write.py')
# ---------- playoff results (Weeks 15-17) in hist.json's week format: {week: {rid: [mid, pts, starters, bench], ...}}
PO=J('pull_po.json');HM=J('hist.json')['m'];A8=J('pull_pts.json');M8=J('pull8.json')['META']
POA={'bracket':C[f'{L}/winners_bracket'],'losers':C[f'{L}/losers_bracket'],'w':{},'m':{}}
for w in (15,16,17):
    home=set(PO['HOME'][str(w)]);pw=PO['PO'][str(w)];POA['w'][str(w)]={}
    def ent(pid,pp):
        pj,opp,tm=(pw.get(pid) or [0,None,None])
        tm=tm or (M8.get(pid) or [None,None,None])[2] or (A8.get(pid) or [None,''])[1] or ''
        o='' if not opp else (opp if tm in home else '@'+opp)
        return f"{pid}|{tm}|{pj}|{pp}|{o}"
    for m in C[f'{L}/matchups/{w}']:
        if m['matchup_id'] is None:continue
        pp=m.get('players_points') or {};st=[x for x in m['starters'] if x and x!='0']
        assert abs(sum(pp.get(x,0) for x in st)-m['points'])<0.02,(w,m['roster_id'])
        POA['w'][str(w)][str(m['roster_id'])]=[m['matchup_id'],m['points'],','.join(ent(x,pp.get(x,0)) for x in st),','.join(ent(x,v) for x,v in pp.items() if x not in st)]
        for x in pp:
            if x not in HM and x not in POA['m']:
                mm=M8.get(x) or PL.get(x) and [PL[x].get('full_name') or x,PL[x].get('position')]
                POA['m'][x]=[(mm or [x,'?'])[1],(mm or [x])[0]]
W_('po_actual.json',POA)
log('replay done')
# ---------- build the site (.season/<year>/site)
if '--no-build' not in sys.argv:
    subprocess.run(['python3',os.path.join(WS,'run.py'),'build'],cwd=WS,env=ENV,check=True)
    log('site built')
