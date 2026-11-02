# Build one season of the tracker from a Sleeper capture, offline:
#   python3 pipeline/season_replay.py 2025          (league ids in seasons.json)
# Copies pipeline/ into .season/<year>/pipeline, seeds a "before Week 1" state from history/raw/<year> (captured by
# pull_season.mjs), then replays every completed regular-season week exactly as a live weekly tracker would (live pull ->
# score.py, weekly pull -> full_update.py) with each Sleeper request answered from the capture. For the season in
# progress it then loads the current week's live scores. Finally builds the site into .season/<year>/site.
import os,sys,json,gzip,shutil,subprocess,csv,re,datetime,base64
SRC=os.path.dirname(os.path.abspath(__file__));REPO=os.path.dirname(SRC)
CFG=json.load(open(os.path.join(SRC,'seasons.json')))
Y=sys.argv[1];LID=CFG['leagues'][Y];CUR=CFG['current'];PAST=Y!=CUR
ROOT=os.path.join(REPO,'.season',Y);WS=os.path.join(ROOT,'pipeline');RAW=os.path.join(SRC,'history','raw',Y)
YEARS=','.join(sorted(CFG['leagues'],reverse=True))
def log(*a):print('[season]',Y,*a,flush=True)
# ---------- workspace
BO='--build-only' in sys.argv  # re-sync code into an existing replay and rebuild the site only
CODE_RE=re.compile(r'\.(py|js|mjs|html|css)$')
if BO:
    for f in os.listdir(SRC):
        if (CODE_RE.search(f) or f=='champions.json') and f!='data_block.js' and not re.match(r'.*_(section|css)\.|standings\.html|DynastyStandings|po_static',f):
            shutil.copy(os.path.join(SRC,f),os.path.join(WS,f))
    shutil.copy(os.path.join(SRC,'pos','build_pos.py'),os.path.join(WS,'pos','build_pos.py'))
else:
    if os.path.isdir(ROOT):shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    shutil.copytree(SRC,WS,ignore=shutil.ignore_patterns('raw','__pycache__','teamhub','.cache','node_modules','*_section.html','*_css.css','po_static.*','standings.html','DynastyStandings.html','lists.json','live.json'))
    if os.path.isdir(os.path.join(SRC,'node_modules')):os.symlink(os.path.join(SRC,'node_modules'),os.path.join(WS,'node_modules'))
RAWX=os.path.join(ROOT,'raw')
if not BO:
    # a past season's capture has today's players map (teams, injuries): make it that season's. NFL team = his last
    # team in that season's weekly stats (else projections); no injury tags.
    os.makedirs(RAWX)
    for k in ('core','stats','proj'):os.symlink(os.path.join(RAW,k+'.json.gz'),os.path.join(RAWX,k+'.json.gz'))
    _pm=json.load(gzip.open(os.path.join(RAW,'players.json.gz')))
    if PAST:
        _pl=_pm[next(iter(_pm))];last={}
        for k in ('proj','stats'):  # stats last, so a real game's team wins
            _d=json.load(gzip.open(os.path.join(RAW,k+'.json.gz')))
            for u in sorted(_d,key=lambda u:int(re.search(r'/(\d+)\?',u).group(1))):
                for r in _d[u]:
                    if r.get('team') and (k=='proj' or (r.get('stats') or {}).get('gp')):last[r['player_id']]=r['team']
        for pid,p_ in _pl.items():
            if pid in last:p_['team']=last[pid]
            p_['injury_status']=None
    with gzip.open(os.path.join(RAWX,'players.json.gz'),'wt',encoding='utf-8') as f:json.dump(_pm,f)
ENV=dict(os.environ,DT_CACHE=RAWX,DT_SEASON=Y,DT_LEAGUE=LID,DT_YEARS=YEARS,DT_CUR=CUR)
if PAST:ENV['DT_PAST']='1'
def node(*a):subprocess.run(['node',os.path.join(WS,'pull.mjs'),*map(str,a)],cwd=WS,env=ENV,check=True,stdout=subprocess.DEVNULL)
def py(f,*a):subprocess.run(['python3',os.path.join(WS,f),*map(str,a)],cwd=WS,env=ENV,check=True,stdout=subprocess.DEVNULL)
J=lambda f:json.load(open(os.path.join(WS,f),encoding='utf-8'))
def W_(f,o):json.dump(o,open(os.path.join(WS,f),'w',encoding='utf-8'),ensure_ascii=False)
C={}
for k in ('core','players'):C.update(json.load(gzip.open(os.path.join(RAWX,k+'.json.gz'))))
A='https://api.sleeper.app/v1';S='https://api.sleeper.com';L=f'{A}/league/{LID}'
LG=C[L];PL=C[f'{A}/players/nfl'];SCH=C[f'{S}/schedule/nfl/regular/{Y}']
REG=int(LG['settings'].get('playoff_week_start') or 15)-1
# ---------- league.json: teams (names as they were that season), managers, avatars, lineup, playoff format
US={u['user_id']:u for u in C[f'{L}/users']};ROS=C[f'{L}/rosters']
AVS=json.load(gzip.open(os.path.join(RAW,'avatars.json.gz'))) if os.path.exists(os.path.join(RAW,'avatars.json.gz')) else {}
if not BO and AVS:os.makedirs(os.path.join(WS,'avatars'),exist_ok=True)
teams=[]
for r in sorted(ROS,key=lambda r:r['roster_id']):
    u=US.get(r['owner_id']) or {};md=u.get('metadata') or {}
    nm=(md.get('team_name') or u.get('display_name') or f"Team {r['roster_id']}").strip()
    av=None;FD=os.path.join(SRC,'faces');FJ=json.load(open(os.path.join(FD,'faces.json'))) if os.path.exists(os.path.join(FD,'faces.json')) else {}
    if os.path.exists(os.path.join(FD,f"{r['owner_id']}.webp")):  # the league's own cartoon face for this manager
        av=f"{r['roster_id']}.webp"
        if not BO:os.makedirs(os.path.join(WS,'avatars'),exist_ok=True);shutil.copy(os.path.join(FD,f"{r['owner_id']}.webp"),os.path.join(WS,'avatars',av))
    elif str(r['roster_id']) in AVS:
        av=f"{r['roster_id']}.webp"
        if not BO:  # whatever Sleeper served (types are often mislabelled): centre-crop to a 128px square webp
            from PIL import Image;import io
            im=Image.open(io.BytesIO(base64.b64decode(AVS[str(r['roster_id'])].split(',',1)[1]))).convert('RGB');w_,h_=im.size;m_=min(w_,h_)
            im.crop(((w_-m_)//2,(h_-m_)//2,(w_-m_)//2+m_,(h_-m_)//2+m_)).resize((128,128),Image.LANCZOS).save(os.path.join(WS,'avatars',av),'WEBP',quality=82)
    teams.append({'rid':r['roster_id'],'name':nm,'mgr':u.get('display_name') or '','nick':(FJ.get(r['owner_id']) or {}).get('nick') or u.get('display_name') or '','avatar':av})
assert len({t['name'] for t in teams})==len(teams),'duplicate team names'
pot=int(LG['settings'].get('playoff_teams') or 6)
W_('league.json',{'season':Y,'lid':LID,'name':LG['name'],'teams':teams,'slots':LG['roster_positions'],'po_teams':pot,
                  'po_byes':{6:2,12:4}.get(pot,0),'po_start':REG+1,'past':PAST,'scoring':LG['scoring_settings'],'dynasty':LG['settings'].get('type')==2})
sys.path.insert(0,WS)
RN={t['rid']:t['name'] for t in teams}
# ---------- season constants
teams_nfl=sorted({g['home'] for g in SCH}|{g['away'] for g in SCH})
bye={t:[w for w in range(1,19) if not any(g['week']==w and t in (g['home'],g['away']) for g in SCH)] for t in teams_nfl}
BYE={t:v[0] for t,v in bye.items() if v}
byeweeks=sorted(set(BYE.values()))
k1=min(g['date'] for g in SCH if g['week']==1)  # Sunday 1 PM ET of week 1 = first Sunday on/after the opener
d=datetime.date.fromisoformat(k1);d+=datetime.timedelta(days=(6-d.weekday())%7)
def patch(f,a,b):
    p=os.path.join(WS,f);s=open(p,encoding='utf-8').read();assert a in s,(f,a[:60]);open(p,'w',encoding='utf-8').write(s.replace(a,b))
patch('rebuild.py','BYES={5,6,7,8,9,10,11,13,14}',f'BYES={set(w for w in byeweeks if w<=REG)}')
patch('sx_data.py','K1=datetime(2026,9,13,17,0,tzinfo=timezone.utc)',f'K1=datetime({d.year},{d.month},{d.day},17,0,tzinfo=timezone.utc)')
patch('live.js',"L='1335450123487961088',Y='2026'",f"L='{LID}',Y='{Y}'")
if PAST:  # ages as of the end of that season (New Year's Day after it), not today
    for f in ('assess.py','cmp_build.py','mu_build.py','pl_build.py','po_build.py','ro_build.py','sx_data.py'):
        p_=os.path.join(WS,f);t_=open(p_,encoding='utf-8').read()
        t_=t_.replace('date.today()',f'date({int(Y)+1},1,1)').replace('_d.today()',f'_d({int(Y)+1},1,1)')
        open(p_,'w',encoding='utf-8').write(t_)
# completed weeks: every NFL game of the week final
def wk_done(w):
    g=[x for x in SCH if x['week']==w];return bool(g) and all(x.get('status')=='complete' for x in g)
DONE=0
while DONE<REG and wk_done(DONE+1):DONE+=1
log('completed regular-season weeks:',DONE)
# ---------- seed files
if BO:
    subprocess.run(['python3',os.path.join(WS,'run.py'),'build'],cwd=WS,env=ENV,check=True);sys.exit()
fut={RN[r]:[] for r in RN}
for w in range(1,REG+1):
    by={}
    for m in C.get(f'{L}/matchups/{w}',[]):
        if m.get('matchup_id') is not None:by.setdefault(m['matchup_id'],[]).append(m['roster_id'])
    for a,b in [v for v in by.values() if len(v)==2]:fut[RN[a]].append([w,RN[b],0,0,50]);fut[RN[b]].append([w,RN[a],0,0,50])
open(os.path.join(WS,'data_block.js'),'w',encoding='utf-8').write('const G=0;\nconst FUT='+json.dumps(fut,ensure_ascii=False,separators=(',',':'))+';\n')
W_('hist.json',{'m':{},'w':{}});W_('kick.json',{});W_('stats.json',{});W_('stats_detail.json',{});W_('age_extra.json',{})
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
W_('cmp_extra.json',{'rounds':LG['settings'].get('draft_rounds',4),'rn':{str(k):v for k,v in RN.items()},
   'tp':[[p['season'],p['round'],p['roster_id'],p['owner_id']] for p in C[f'{L}/traded_picks']],
   'tx':tx,'txp':txp,'txw':{pid:[] for pid in txp},'bench':{RN[r]:[] for r in RN},'age':{}})
POSL=[p for p in ('QB','RB','WR','TE','K','DEF') if p in LG['roster_positions']]
cols=['roster_id','team','wins','empty_slots','total','total_rank']+[c for p in POSL for c in (p,p+'_rank')]+[c for p in POSL for c in ('avg_'+p,'avg_'+p+'_rank')]+['starts_'+p for p in POSL]+['nogame_'+p for p in POSL]
os.makedirs(os.path.join(WS,'pos'),exist_ok=True)
with open(os.path.join(WS,'pos','pos.csv'),'w',encoding='utf-8',newline='') as f:
    w_=csv.DictWriter(f,fieldnames=cols);w_.writeheader();w_.writerows([{**{c:0 for c in cols},'roster_id':r,'team':RN[r]} for r in sorted(RN)])
W_('rosters.json',{RN[r]:[] for r in sorted(RN)})
W_('ro_ranks.json',{'_bye':BYE})
# ---------- week 0 pull -> wk1.json (same as full_update step 6 with NOW = 1)
node('weekly',0)
X8=J('pull8.json');X8a=J('pull8a.json');M7=J('pull_m7.json')
PJ,META,S8,K8=X8['PJ'],X8['META'],X8['S8'],X8['K8'];RO={r['rid']:r for r in M7['RO']}
home={h for w_,a_,h in S8 if w_==1};out={}
for rid,mid,st in X8a['m8']:
    r=RO[rid]
    def row(pid):
        m=META.get(pid) or [pid,'?',None,None,None];return [pid,m[1],m[0],m[2] or '',PJ.get(pid,[0,None])[0],0,PJ.get(pid,[0,None])[1],None]
    out[str(rid)]={'mid':mid,'pts':0,'st':[row(p) for p in st if p and p!='0'],'bn':[row(p) for p in r['pl'] if p not in st]}
W_('wk1.json',{'done':[],'out':out,'home':sorted(home),'done_note':'season replay'})
W_('kick.json',{'1':K8})
# ---------- replay the completed weeks, then (season in progress) the current week's live scores
for w in range(1,DONE+1):
    node('live',w);py('score.py','live.json','--no-build')
    node('weekly',w);py('full_update.py',w)
    log('week',w,'ok')
if DONE<REG:
    W=DONE+1;node('live',W);py('score.py','live.json','--no-build');log('week',W,'live')
node('detail',f'1-{min(DONE+1,REG)}');node('top',max(DONE,1));
try:
    if Y==CUR:node('wire',max(DONE,1))  # THE WIRE, current season only; never fatal (needs this week's projections in the capture)
except Exception as ex:print('wire pull skipped:',ex)
node('playoffs');py('po_write.py')
# ---------- playoff results in hist.json's week format: {week: {rid: [mid, pts, starters, bench], ...}} (completed weeks only)
PO=J('pull_po.json');HM=J('hist.json')['m'];A8=J('pull_pts.json');M8=J('pull8.json')['META']
POA={'bracket':C[f'{L}/winners_bracket'],'losers':C[f'{L}/losers_bracket'],'w':{},'m':{}}
for w in [x for x in (REG+1,REG+2,REG+3) if DONE==REG and wk_done(x)]:
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
if POA['w']:W_('po_actual.json',POA)
log('replay done')
# ---------- build the site (.season/<year>/site)
if '--no-build' not in sys.argv:
    subprocess.run(['python3',os.path.join(WS,'run.py'),'build'],cwd=WS,env=ENV,check=True)
    log('site built')
