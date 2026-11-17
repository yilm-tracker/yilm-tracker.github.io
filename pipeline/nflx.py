# nflx.py: reader for nfl_wk.json.gz, the NFL weekly data behind the new stats (identical in both repos; brief
# newstats-data 2026-11-17). Data only: nothing on either site reads this yet.
#
# The file is written by `node pull.mjs nfl D` (sleeper.mjs pullNfl): BBP run.py weekly and midweek runs (pipeline/,
# committed by "Save season data"); YILM season_replay.py from its capture into the .season workspace (no network).
#   {"season": "2026", "D": 10,
#    "stats": {"<w>": [[pid, team, opponent, pos, {stat: value}], ...]},  completed weeks 1..D; fantasy positions
#             QB/RB/WR/TE/K/DEF (pull_season.mjs fpos rule) with gp or gms_active; keys = every key either league scores
#             + pass_att, pass_cmp, rush_att, rec_tgt, gp, gms_active, off_snp; zero values left out (read them as 0)
#    "sched": [[week, away, home], ...],                                  every NFL regular-season game, all 18 weeks
#    "mu": {"<w>": {"<roster id>": [pid, ...]}}}                          each roster's week-w matchup list (IR / taxi too)
#
# Never raises: no file or a bad file gives empty data (ok False) and one WARNING on stderr per path.
#   load(path=None)   -> dict: ok, season, D, weeks [1..D], lines {w: {pid: Line}}, sched [(w, away, home)], mu {w: {rid: [pid]}}
#   weeks()           -> completed weeks in the file
#   lines(w)          -> {pid: Line(pid, team, opp, pos, s)} for week w ({} if none); s = stat dict
#   line(w, pid)      -> Line or None
#   stat(line, key)   -> the value, 0 when absent
#   sched()           -> [(week, away, home), ...]
#   opp(team, w)      -> (opponent, home True/False), or None (bye / unknown)
#   mu(w)             -> {roster id (int): [pid, ...]} for week w ({} if none)
#   start_qb(w, team) -> pid of the team's starting QB in week w, or None
#   start_qbs(w)      -> {team: pid} for every team with a QB line in week w
# Starting QB (phase 1 rule): the QB with the most pass attempts in that team's game; ties on offensive snaps, then
# passing yards, then the lower player id (never needed on 2026 Weeks 1-10). A team whose QBs threw no pass has none.
import gzip, json, os, sys
from collections import namedtuple

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nfl_wk.json.gz')
Line = namedtuple('Line', 'pid team opp pos s')
_C = {}


def _empty():
    return {'ok': False, 'season': None, 'D': 0, 'weeks': [], 'lines': {}, 'sched': [], 'mu': {}}


def load(path=None):
    path = path or P
    if path in _C:
        return _C[path]
    d = _empty()
    try:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            j = json.load(f)
        lines = {}
        for w, rows in (j.get('stats') or {}).items():
            L = {}
            for r in rows:
                pid, team, opp, pos, s = r
                L[str(pid)] = Line(str(pid), team, opp, pos, s or {})
            lines[int(w)] = L
        mu = {int(w): {int(r): list(p) for r, p in (m or {}).items()} for w, m in (j.get('mu') or {}).items()}
        d = {'ok': True, 'season': j.get('season'), 'D': int(j.get('D') or 0), 'weeks': sorted(lines),
             'lines': lines, 'sched': [(int(w), a, h) for w, a, h in (j.get('sched') or [])], 'mu': mu}
    except FileNotFoundError:
        print(f'WARNING nflx: {path} not found; the stats that need NFL weekly data are left out', file=sys.stderr)
        d = _empty()
    except Exception as e:  # bad / partial file
        print(f'WARNING nflx: {path} unreadable ({type(e).__name__}: {e}); the stats that need it are left out', file=sys.stderr)
        d = _empty()
    _C[path] = d
    return d


def weeks(path=None):
    return list(load(path)['weeks'])


def lines(w, path=None):
    return load(path)['lines'].get(int(w), {})


def line(w, pid, path=None):
    return lines(w, path).get(str(pid))


def stat(ln, key):
    if ln is None:
        return 0
    v = ln.s.get(key, 0)
    return v if isinstance(v, (int, float)) else 0


def sched(path=None):
    return list(load(path)['sched'])


def opp(team, w, path=None):
    for wk, a, h in load(path)['sched']:
        if wk == int(w):
            if a == team:
                return (h, False)
            if h == team:
                return (a, True)
    return None


def mu(w, path=None):
    return load(path)['mu'].get(int(w), {})


def start_qbs(w, path=None):
    best = {}
    for ln in lines(w, path).values():
        if ln.pos != 'QB' or not ln.team or stat(ln, 'pass_att') <= 0:
            continue
        k = (stat(ln, 'pass_att'), stat(ln, 'off_snp'), stat(ln, 'pass_yd'))
        b = best.get(ln.team)
        if b is None or k > b[0] or (k == b[0] and ln.pid < b[1]):
            best[ln.team] = (k, ln.pid)
    return {t: v[1] for t, v in best.items()}


def start_qb(w, team, path=None):
    return start_qbs(w, path).get(team)
