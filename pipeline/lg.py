# League configuration for every builder, read from league.json (written from Sleeper's league, users and rosters by
# season_replay.py). Nothing here is specific to one league: team count, names, lineup slots and playoff size all come
# from the data.
import os,json
P=os.path.dirname(os.path.abspath(__file__)).removesuffix('/pos')+'/'
L=json.load(open(P+'league.json',encoding='utf-8'))
SEASON=str(L['season']);LID=L['lid'];NAME=L['name']
N=len(L['teams'])                                   # teams
RN={int(t['rid']):t['name'] for t in L['teams']};RID={v:k for k,v in RN.items()}
TEAMS=[RN[r] for r in sorted(RN)]
MGR={t['name']:t['mgr'] for t in L['teams']}         # Sleeper display name of the manager
AV={t['name']:t.get('avatar') for t in L['teams']}   # avatar file under avatars/, or None
SHORT={t:t for t in TEAMS};SHORT0=dict(SHORT)        # data files and the page both use full team names
FULL=dict(SHORT)
def _code(n):
    w=[x for x in n.replace('-',' ').split() if x[:1].isalnum()]
    return ((w[0][0]+w[1][0]) if len(w)>1 else n[:2]).upper()
CODE={t:_code(t) for t in TEAMS}
SLOTS=[s for s in L['slots'] if s not in('BN','IR','TAXI')]   # starting lineup, in Sleeper's order
FLEXES={'FLEX':('RB','WR','TE'),'SUPER_FLEX':('QB','RB','WR','TE'),'WRRB_FLEX':('RB','WR'),'REC_FLEX':('WR','TE')}
SLAB={'FLEX':'FLEX','SUPER_FLEX':'SFLX','WRRB_FLEX':'W/R','REC_FLEX':'W/T'}
POS=[p for p in ('QB','RB','WR','TE','K','DEF') if p in SLOTS]  # positions the league starts
NEED={p:SLOTS.count(p) for p in POS}                             # dedicated starters per position
SKILL=('RB','WR','TE')
PO=int(L['po_teams']);BYE_N=int(L.get('po_byes',2));REG=int(L['po_start'])-1;PWEEKS=[REG+1,REG+2,REG+3]
SKILL_SLOTS=[s for s in SLOTS if s in SKILL or s=='FLEX']        # the RB/WR/TE + FLEX part of the lineup
def optimal(pool,pos=lambda q:q['pos'],pts=lambda q:q['pts'],slots=None):
    """best legal lineup from pool: dedicated slots first (best at each position), then the flex slots from what is
    left, narrowest first (FLEX before SUPER_FLEX). Returns the chosen items (None for an unfilled slot)."""
    left=sorted([q for q in pool if q is not None],key=lambda q:-pts(q));out=[];sl=slots or SLOTS
    for s in [s for s in sl if s in POS]+sorted([s for s in sl if s in FLEXES],key=lambda s:len(FLEXES[s])):
        ok=(s,) if s in POS else FLEXES[s]
        q=next((q for q in left if pos(q) in ok),None)
        if q is not None:left.remove(q)
        out.append(q)
    return out
def optsum(pool,pos=lambda q:q['pos'],pts=lambda q:q['pts'],slots=None):return round(sum(pts(q) for q in optimal(pool,pos,pts,slots) if q is not None),2)
def tone(r):return 'gold' if r==1 else 'g' if r<=3 else 'b last' if r==N else 'b' if r>N-3 else ''
CORE=dict(NEED)                      # core starters per position (a SUPER_FLEX spot is a second QB in practice)
if 'SUPER_FLEX' in SLOTS and 'QB' in CORE:CORE['QB']+=SLOTS.count('SUPER_FLEX')
