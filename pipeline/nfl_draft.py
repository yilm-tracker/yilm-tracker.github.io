"""NFL draft slots for the Drafts tab (2026-11-03).
Source: nflverse-data release 'draft_picks' (draft_picks.csv, every NFL draft 1980-now; data CC-BY 4.0, nflverse.com).
Writes nfl_draft.json: {"<name key>|<POS>": [season, round, overall pick], ...} for fantasy positions, 1995 on.
Run after each NFL draft (network): python3 nfl_draft.py   (offline builds use the committed JSON)."""
import csv,io,json,os,re,sys,urllib.request
P=os.path.dirname(os.path.abspath(__file__))+'/'
URL='https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv'
def nk(n):
    n=re.sub(r"[.'’`,]",'',str(n or '').lower()).replace('-',' ');n=re.sub(r'\b(jr|sr|ii|iii|iv|v)\b','',n);return re.sub(r'\s+',' ',n).strip()
POSMAP={'QB':'QB','RB':'RB','FB':'RB','HB':'RB','WR':'WR','TE':'TE','K':'K','PK':'K'}
def main(src=None):
    raw=open(src,encoding='utf-8').read() if src else urllib.request.urlopen(URL,timeout=60).read().decode('utf-8')
    out={}
    for r in csv.DictReader(io.StringIO(raw)):
        pos=POSMAP.get((r.get('position') or '').upper());y=int(r['season'] or 0)
        if not pos or y<1995:continue
        k=nk(r['pfr_player_name'])+'|'+pos
        out.setdefault(k,[]).append([y,int(r['round']),int(r['pick'])])
    for k in out:out[k].sort()
    out['_meta']={'source':'nflverse draft_picks.csv (CC-BY 4.0)','through':max(v[-1][0] for k,v in out.items() if k!='_meta')}
    json.dump(out,open(P+'nfl_draft.json','w',encoding='utf-8'),separators=(',',':'))
    print('nfl_draft.json',len(out)-1,'players through',out['_meta']['through'])
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else None)
