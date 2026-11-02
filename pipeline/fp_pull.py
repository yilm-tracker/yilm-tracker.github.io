# FantasyPros weekly projections: the second opinion beside Sleeper's in the pre-game sim (psim.pregame blends the two).
# Needs an API key in FP_API_KEY (fantasypros.com/api-data; a personal production key comes with FantasyPros HOF).
# Without a key this does nothing and the sim uses Sleeper alone.
# FantasyPros data is licensed for personal use, so pipeline/fp/ is kept out of git (Actions cache only) and the page
# shows only the sim's team totals, never FantasyPros' player numbers.
# Writes pipeline/fp/<season>_w<week>.json = {"week", "pulled", "scoring", "pts": {sleeper_id: league points}, "unmatched": [...]}.
# A player's projection stops updating once his NFL game has kicked off, so the pre-game sim stays fixed through the week.
import os,sys,json,re,urllib.request,urllib.parse
from datetime import datetime,timezone
P=os.path.dirname(os.path.abspath(__file__))+'/'
KEY=os.environ.get('FP_API_KEY','').strip()
LEAGUE=os.environ.get('DT_LEAGUE','1335450123487961088');SEASON=os.environ.get('DT_SEASON','2026')
BASE='https://api.fantasypros.com/public/v2/json'
def get(url,hdr=None):
    r=urllib.request.Request(url,headers={'User-Agent':'league-tracker',**(hdr or {})})
    with urllib.request.urlopen(r,timeout=30) as f:return json.load(f)
if not KEY:print('fp_pull: no FP_API_KEY, skipped');sys.exit(0)
week=int(os.environ.get('FP_WEEK') or get('https://api.sleeper.app/v1/state/nfl')['week'])
ss=get(f'https://api.sleeper.app/v1/league/{LEAGUE}').get('scoring_settings',{})
rec=ss.get('rec',0);SC='PPR' if rec>=1 else 'HALF' if rec>=0.5 else 'STD'
# kickoff per NFL team this week (ESPN's public scoreboard); unknown = treat as not started
TM={'WSH':'WAS','JAC':'JAX','LA':'LAR'}
kick={}
try:
    sb=get(f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&week={week}&dates={SEASON}')
    for ev in sb.get('events',[]):
        for c in ev['competitions'][0]['competitors']:
            a=c['team']['abbreviation'];kick[TM.get(a,a)]=ev['date']
except Exception as ex:print('fp_pull: no kickoff times',ex)
now=datetime.now(timezone.utc)
started=lambda tm:tm in kick and datetime.fromisoformat(kick[tm].replace('Z','+00:00'))<=now
# every Sleeper player (name, position, team) to match FantasyPros names to Sleeper ids; refreshed once a day
os.makedirs(P+'fp',exist_ok=True);PF=P+'fp/players.json'
if not os.path.exists(PF) or (now.timestamp()-os.path.getmtime(PF))>20*3600:
    pl=get('https://api.sleeper.app/v1/players/nfl')
    json.dump({k:[v.get('full_name') or f"{v.get('first_name','')} {v.get('last_name','')}".strip(),v.get('position'),v.get('team')] for k,v in pl.items() if v.get('position') in ('QB','RB','WR','TE','K','DEF')},open(PF,'w'))
META=json.load(open(PF))
def norm(s):
    s=re.sub(r"[.'’\-]",'',s.lower());s=re.sub(r'\b(jr|sr|ii|iii|iv|v)\b','',s);return re.sub(r'\s+',' ',s).strip()
IDX={}
for pid,m in META.items():
    if not m or not m[0]:continue
    IDX.setdefault((norm(m[0]),m[1]),[]).append((pid,m[2]))
# FantasyPros stat names -> Sleeper scoring keys (used when the response carries stat lines; else its points for SC)
SMAP={'pass_yds':'pass_yd','pass_tds':'pass_td','pass_ints':'pass_int','rush_yds':'rush_yd','rush_tds':'rush_td','rec':'rec',
      'rec_rec':'rec','rec_yds':'rec_yd','rec_tds':'rec_td','fumbles':'fum_lost','fum_lost':'fum_lost','fg':'fgm','fga':'fga','xpt':'xpm',
      'def_sack':'sack','def_int':'int','def_fr':'fum_rec','def_td':'def_td','def_safety':'safe'}
def pts(row):
    st=row.get('stats') if isinstance(row.get('stats'),dict) else row
    calc=[(ss[SMAP[k]],float(v)) for k,v in st.items() if k in SMAP and SMAP[k] in ss and isinstance(v,(int,float,str)) and re.match(r'^-?[\d.]+$',str(v))]
    for k in ('points','fpts','proj_pts','fantasy_points','pts'):
        for src in (row,st):
            if k in src:
                try:fp=float(src[k])
                except Exception:continue
                return (sum(a*b for a,b in calc) if len(calc)>=2 else fp)
    return sum(a*b for a,b in calc) if calc else None
def rows(d):
    if isinstance(d,list):return d
    for k in ('players','data','projections','results'):
        if isinstance(d.get(k),list):return d[k]
    return []
f=f'{P}fp/{SEASON}_w{week}.json'
old=json.load(open(f)) if os.path.exists(f) else {'pts':{}}
out={'week':week,'pulled':now.isoformat(timespec='minutes'),'scoring':SC,'pts':dict(old.get('pts',{})),'unmatched':[]}
raw={}
for pos in ('QB','RB','WR','TE','K','DST'):
    q=urllib.parse.urlencode({'week':week,'position':pos,'scoring':SC,'type':'weekly'})
    try:d=get(f'{BASE}/nfl/{SEASON}/projections?{q}',{'x-api-key':KEY})
    except Exception as ex:print('fp_pull:',pos,ex);continue
    raw[pos]=d
    r0=(rows(d) or [{}])[0];print('fp_pull:',pos,'fields',sorted(r0)[:40],'stats',sorted(r0.get('stats',{}) if isinstance(r0.get('stats'),dict) else [])[:40])   # names only, no data
    for r in rows(d):
        nm=r.get('player_name') or r.get('name') or r.get('full_name') or '';tm=r.get('player_team_id') or r.get('team') or r.get('team_id') or ''
        tm=TM.get(tm,tm);sp='DEF' if pos=='DST' else pos;v=pts(r)
        if v is None:continue
        if sp=='DEF':pid=tm if tm in META else None
        else:
            c=IDX.get((norm(nm),sp),[]);c=[x for x in c if not tm or x[1]==tm] or c;pid=c[0][0] if len(c)==1 else None
        if not pid:out['unmatched'].append(f'{nm} {sp} {tm}');continue
        if started(META.get(pid,[None,None,tm])[2] or tm) and pid in old.get('pts',{}):continue   # frozen at kickoff
        out['pts'][pid]=round(v,2)
json.dump(out,open(f,'w'),indent=0)
print(f'fp_pull: week {week} {SC}: {len(out["pts"])} players, {len(out["unmatched"])} unmatched')
