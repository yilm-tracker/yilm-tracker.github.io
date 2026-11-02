// Sleeper data pulls for the tracker. Pure functions over `get(url) -> JSON`, so the same code runs in Node
// (GitHub Actions) and in a browser for checking. Output shapes match the files the Python build reads.
const _ENV = (typeof process !== 'undefined' && process.env) || {};
export const LEAGUE = _ENV.DT_LEAGUE || '1335450123487961088', SEASON = _ENV.DT_SEASON || '2026';
const A = 'https://api.sleeper.app/v1', S = 'https://api.sleeper.com';
const FPOS = new Set(['QB', 'RB', 'WR', 'TE', 'K', 'DEF']);
const r2 = x => Math.round(x * 100) / 100;
const KST = { pre_game: 'pre', in_game: 'in', complete: 'post' };

export const leagueScore = (stats, ss) => {
  let s = 0;
  for (const [k, v] of Object.entries(stats || {})) if (ss[k] != null && typeof v === 'number') s += v * ss[k];
  return r2(s);
};

// last regular-season week whose games are all complete (0 if none)
export async function lastCompleteWeek(get) {
  const sch = await get(`${S}/schedule/nfl/regular/${SEASON}`);
  let done = 0;
  for (let w = 1; w <= 18; w++) {
    const g = sch.filter(x => x.week == w);
    if (g.length && g.every(x => x.status == 'complete')) done = w; else break;
  }
  return { done, sch };
}

async function kickoffs(get, w) {
  const sc = await get(`${S}/scores/nfl/regular/${SEASON}/${w}`);
  const k = {};
  for (const x of sc) {
    const m = x.metadata || {};
    for (const tm of [m.home_team, m.away_team]) if (tm) k[tm] = [m.date_time, KST[x.status] || x.status];
  }
  return k;
}

const projURL = w => `${S}/projections/nfl/${SEASON}/${w}?season_type=regular` + ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'].map(p => `&position[]=${p}`).join('');

// Weekly full refresh inputs: completes week D, prepares week N = D + 1.
export async function pullWeekly(get, D) {
  const N = D + 1, L = `${A}/league/${LEAGUE}`;
  const [lg, ro, us, mD, mN, tD, tN, tp, state, sch] = await Promise.all([
    get(L), get(`${L}/rosters`), get(`${L}/users`), get(`${L}/matchups/${D}`), get(`${L}/matchups/${N}`),
    get(`${L}/transactions/${D}`), get(`${L}/transactions/${N}`), get(`${L}/traded_picks`), get(`${A}/state/nfl`),
    get(`${S}/schedule/nfl/regular/${SEASON}`)]);
  const ss = lg.scoring_settings;
  const pull_m7 = {
    M7: mD.map(x => ({ rid: x.roster_id, mid: x.matchup_id, pts: x.points, st: (x.starters || []).filter(p => p && p !== '0'), pp: x.players_points })),
    RO: ro.map(r => ({ rid: r.roster_id, pl: r.players || [], res: r.reserve, taxi: r.taxi, own: r.owner_id })),
    TP: tp,
  };
  // weekly league points for every fantasy-position player who played in weeks 1..D
  const weeks = await Promise.all(Array.from({ length: D }, (_, i) => get(`${S}/stats/nfl/${SEASON}/${i + 1}?season_type=regular`)));
  const P = {};
  weeks.forEach((rows, i) => {
    for (const r of rows) {
      const pos = r.player && r.player.position;
      if (!FPOS.has(pos)) continue;
      const s = r.stats || {};
      if (!(s.gp > 0)) continue;
      const e = P[r.player_id] || (P[r.player_id] = [pos, r.team, Array(D).fill(null), '0'.repeat(D)]);
      e[1] = r.team || e[1];
      e[2][i] = leagueScore(s, ss);
      e[3] = e[3].slice(0, i) + '1' + e[3].slice(i + 1);
    }
  });
  // projections (week N), player meta for rostered players, schedule N..14, kickoffs N
  // rostered now, plus everyone in the week D and week N lineups (a player dropped since keeps his name)
  const ids = new Set([...ro.flatMap(r => r.players || []), ...mD.flatMap(x => x.players || []), ...mN.flatMap(x => x.players || [])]);
  const [pj, players, K8] = await Promise.all([get(projURL(N)), get(`${A}/players/nfl`), kickoffs(get, N)]);
  const PJ = {};
  for (const r of pj) if (ids.has(r.player_id)) PJ[r.player_id] = [leagueScore(r.stats, ss), r.opponent || null];
  for (const id of ids) if (!(id in PJ)) PJ[id] = [0, null];
  const META = {};
  for (const id of ids) {
    const p = players[id];
    META[id] = p ? [p.full_name || `${p.first_name} ${p.last_name}`, p.position, p.team || null, p.injury_status || null, p.birth_date || null] : null;
  }
  const S8 = sch.filter(x => x.week >= N && x.week <= 14).map(x => [x.week, x.away, x.home]);
  const pull8 = { PJ, META, S8, K8 };
  const tr = t => ({ ts: t.status_updated, rids: t.roster_ids, adds: t.adds, picks: t.draft_picks, faab: t.waiver_budget, st: t.status });
  const pull8a = {
    state, ss, pos: lg.roster_positions,
    ro: ro.map(r => ({ rid: r.roster_id, own: r.owner_id, n: (r.players || []).length, res: r.reserve, taxi: r.taxi })),
    us: us.map(u => [u.user_id, u.display_name, (u.metadata || {}).team_name]),
    m8: mN.map(x => [x.roster_id, x.matchup_id, (x.starters || []).filter(p => p && p !== '0')]),
    t7: tD.filter(t => t.type == 'trade').map(tr), t8: tN.filter(t => t.type == 'trade').map(tr), ntp: tp.length,
  };
  return { pull_m7, pull_pts: P, pull8, pull8a };
}

// Playoff weeks 15-17: league-scored projections, home teams, kickoffs (same shape as po_pull.js)
export async function pullPlayoffs(get) {
  const L = `${A}/league/${LEAGUE}`;
  const [lg, ro, sch] = await Promise.all([get(L), get(`${L}/rosters`), get(`${S}/schedule/nfl/regular/${SEASON}`)]);
  const mw = await Promise.all([15, 16, 17].map(w => get(`${L}/matchups/${w}`).catch(() => [])));
  const ss = lg.scoring_settings, ids = new Set([...ro.flatMap(r => r.players || []), ...mw.flat().flatMap(x => (x && x.players) || [])]);
  const out = { PO: {}, HOME: {}, KICK: {}, SCH: {} };
  for (const w of [15, 16, 17]) {
    const g = sch.filter(x => x.week == w);
    out.SCH[w] = g.map(x => [x.home, x.away, x.status, x.date]); out.HOME[w] = g.map(x => x.home);
    const pr = await get(projURL(w)), m = {};
    for (const r of pr) if (ids.has(r.player_id)) m[r.player_id] = [leagueScore(r.stats, ss), r.opponent || null, r.team || null];
    out.PO[w] = m;
    const sc = await get(`${S}/scores/nfl/regular/${SEASON}/${w}`), k = {};
    for (const x of sc) { const t = x.metadata && x.metadata.date_time; for (const tm of [x.metadata?.home_team, x.metadata?.away_team]) if (tm) k[tm] = [t, x.status]; }
    out.KICK[w] = k;
  }
  // projections for the rest of the regular season (current week on), for the player-level season sim
  const po0 = +(lg.settings && lg.settings.playoff_week_start) || 15;
  const now = (sch.find(x => x.week < po0 && x.status != 'complete') || { week: po0 }).week;
  out.FP = {};
  for (let w = now; w < po0; w++) {
    const pr = await get(projURL(w)).catch(() => []), m = {};
    for (const r of pr) if (ids.has(r.player_id)) m[r.player_id] = Math.round(leagueScore(r.stats, ss) * 100) / 100;
    out.FP[w] = m;
  }
  out.n = ids.size;
  return out;
}

// In-week scores for week W (same shape as score_pull.js, plus rows for newly started players)
const STATK = { QB: ['pass_cmp', 'pass_att', 'pass_yd', 'pass_td', 'pass_int', 'rush_att', 'rush_yd', 'rush_td', 'fum_lost'], RB: ['rush_att', 'rush_yd', 'rush_td', 'rec', 'rec_tgt', 'rec_yd', 'rec_td', 'fum_lost'], WR: ['rec', 'rec_tgt', 'rec_yd', 'rec_td', 'rush_att', 'rush_yd', 'rush_td', 'fum_lost'], K: ['fgm', 'fga', 'xpm', 'xpa'], DEF: ['sack', 'int', 'fum_rec', 'def_td', 'pts_allow'] };
STATK.TE = STATK.WR;
export async function pullLive(get, W, known) {
  const L = `${A}/league/${LEAGUE}`;
  const [sc, m, st, gs] = await Promise.all([get(`${S}/schedule/nfl/regular/${SEASON}`), get(`${L}/matchups/${W}`), get(`${S}/stats/nfl/${SEASON}/${W}?season_type=regular`), get(`${S}/scores/nfl/regular/${SEASON}/${W}`).catch(() => [])]);
  // share of each live game still to play (game clock), for the in-week win chance: 1 at kickoff, 0 at the end; overtime ~0
  const left = {};
  for (const x of gs || []) {
    if (x.status != 'in_game') continue; const md = x.metadata || {}, q = +md.quarter_num || 1, [mm, ss] = String(md.time_remaining || '15:00').split(':').map(Number);
    const r = q > 4 ? 0.02 : Math.max(0, Math.min(1, ((4 - q) * 900 + (mm || 0) * 60 + (ss || 0)) / 3600));
    for (const t of [md.home_team, md.away_team]) if (t) left[t] = Math.round(r * 1000) / 1000;
  }
  const done = sc.filter(g => g.week == W && g.status == 'complete').flatMap(g => [g.home, g.away]);
  const live = sc.filter(g => g.week == W && g.status == 'in_game').flatMap(g => [g.home, g.away]);
  const pp = {}, tp = {}, sts = {};
  m.forEach(x => { tp[x.roster_id] = x.points; sts[x.roster_id] = x.starters; Object.assign(pp, x.players_points); });
  const S_ = {};
  for (const r of st) {
    const pid = r.player_id; if (!(pid in pp)) continue;
    const pos = r.player?.position || ''; const k = STATK[pos]; if (!k) continue;
    const s = r.stats || {}; if (!s.gp && !s.gms_active && pos != 'DEF') continue;
    const a = k.map(x => Math.round(s[x] || 0)); while (a.length > 1 && a[a.length - 1] === 0) a.pop();
    S_[pid] = a.join('.');
  }
  const pz = {}; for (const [k, v] of Object.entries(pp)) if (v) pz[k] = v;
  // starters the build has never seen (added after the weekly refresh): give score.py a full row
  const extra = {}, need = Object.values(sts).flat().filter(id => id && id != '0' && !known.has(id));
  if (need.length) {
    const [lg, players, pj] = await Promise.all([get(L), get(`${A}/players/nfl`), get(projURL(W))]);
    const ss = lg.scoring_settings, P = Object.fromEntries(pj.map(r => [r.player_id, r]));
    const INJ = new Set(['Questionable', 'Doubtful', 'Out', 'IR', 'PUP', 'Sus']);
    for (const id of need) {
      const p = players[id] || {}, q = P[id];
      const inj = p.injury_status && INJ.has(p.injury_status) ? p.injury_status : null;
      extra[id] = [id, p.position || '', p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim() || id, p.team || '', q ? leagueScore(q.stats, ss) : 0, 0, q ? q.opponent || null : null, inj];
    }
  }
  return { w: W, done, live, left, tp, pp: pz, S: S_, starters: sts, extra };
}

// Full stat lines for the Detailed lineup view. Keeps every stat the league scores (so a points breakdown can be
// computed) plus volume stats that score nothing (attempts, targets, longs, yards allowed). Lineup players only.
const DX = ['pass_att', 'pass_cmp', 'pass_lng', 'pass_sack', 'rush_att', 'rush_lng', 'rec_tgt', 'rec_lng', 'fga', 'fgm', 'fgm_lng', 'xpa', 'yds_allow', 'pts_allow', 'gp', 'fgmiss_0_19', 'fgmiss_20_29', 'fgmiss_30_39', 'fgmiss_40_49', 'fgmiss_50_59', 'fgmiss_60p', 'fgm_0_19'];
export async function pullDetail(get, weeks) {
  const L = `${A}/league/${LEAGUE}`, lg = await get(L), keep = new Set([...Object.keys(lg.scoring_settings), ...DX]);
  const out = {};
  for (const w of weeks) {
    const [m, st] = await Promise.all([get(`${L}/matchups/${w}`), get(`${S}/stats/nfl/${SEASON}/${w}?season_type=regular`)]);
    const ids = new Set(m.flatMap(x => [...(x.players || []), ...(x.starters || [])]));
    const W = {};
    for (const r of st) {
      if (!ids.has(r.player_id)) continue;
      const s = r.stats || {}, o = {};
      for (const [k, v] of Object.entries(s)) if (keep.has(k) && typeof v === 'number' && v !== 0) o[k] = Math.round(v * 100) / 100;
      if (Object.keys(o).length) W[r.player_id] = o;
    }
    out[w] = W;
  }
  return out;
}

// Top players by position through week D (every NFL player, rostered or not): season stat totals, weekly league points,
// names. Keeps the union of the top 60 by points and the top 60 by points per game (min. ceil(D/2) games) per position.
const TOPK = ['pass_cmp', 'pass_att', 'pass_yd', 'pass_td', 'pass_int', 'rush_att', 'rush_yd', 'rush_td', 'rec', 'rec_tgt', 'rec_yd', 'rec_td',
  'fum_lost', 'fgm', 'fga', 'fgm_lng', 'xpm', 'xpa', 'sack', 'int', 'fum_rec', 'def_td', 'pts_allow', 'yds_allow', 'safe', 'def_st_td',
  'off_snp', 'tm_off_snp', 'pass_sack', 'pass_lng', 'rush_lng', 'rec_lng', 'blk_kick', 'ff', 'fum',
  'fgm_0_19', 'fgm_20_29', 'fgm_30_39', 'fgm_40_49', 'fgm_50_59', 'fgm_60p', 'fgmiss_0_19', 'fgmiss_20_29', 'fgmiss_30_39', 'fgmiss_40_49', 'fgmiss_50_59', 'fgmiss_60p'];
export async function pullTop(get, D, keep = 60) {
  const L = `${A}/league/${LEAGUE}`;
  const [lg, ro, players] = await Promise.all([get(L), get(`${L}/rosters`), get(`${A}/players/nfl`)]);
  const ss = lg.scoring_settings, weeks = await Promise.all(Array.from({ length: D }, (_, i) => get(`${S}/stats/nfl/${SEASON}/${i + 1}?season_type=regular`)));
  const X = {};
  weeks.forEach((rows, i) => {
    for (const r of rows) {
      const pos = r.player && r.player.position, s = r.stats || {};
      if (!FPOS.has(pos) || !(s.gp > 0)) continue;
      const e = X[r.player_id] || (X[r.player_id] = { pos, team: r.team, w: Array(D).fill(null), t: {} });
      e.team = r.team || e.team; e.w[i] = leagueScore(s, ss);
      for (const k of TOPK) { const v = s[k]; if (typeof v === 'number' && v) e.t[k] = k.endsWith('_lng') ? Math.max(e.t[k] || 0, v) : r2((e.t[k] || 0) + v); }
    }
  });
  const minGp = Math.ceil(D / 2), pick = new Set();
  for (const pos of FPOS) {
    const L_ = Object.entries(X).filter(([, e]) => e.pos === pos).map(([id, e]) => {
      const pl = e.w.filter(v => v != null); const pts = r2(pl.reduce((a, b) => a + b, 0)); return { id, pts, gp: pl.length, ppg: pl.length ? pts / pl.length : 0 };
    });
    L_.slice().sort((a, b) => b.pts - a.pts).slice(0, keep).forEach(o => pick.add(o.id));
    L_.filter(o => o.gp >= minGp).sort((a, b) => b.ppg - a.ppg).slice(0, keep).forEach(o => pick.add(o.id));
  }
  const own = {}; for (const r of ro) for (const id of r.players || []) own[id] = r.roster_id;
  const P = {};
  for (const id of pick) {
    const e = X[id], p = players[id] || {};
    const name = e.pos === 'DEF' ? `${p.first_name || id} ${p.last_name || ''}`.trim() : (p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim() || id);
    P[id] = [name, e.pos, e.team || p.team || null, e.w, e.t, own[id] || null, p.birth_date || null];
  }
  return { D, minGp, P };
}

// THE WIRE: every unrostered player with season points or a projection this week. Week N = D + 1.
// Row: [id, name, pos, team, injury, seasonPts, gp, posRank (season points among all players at the position),
//       projN (league scoring), opp, home (1/0), kickoff ISO, adds48h (Sleeper-wide trending adds)]
export async function pullWire(get, D) {
  const N = D + 1, L = `${A}/league/${LEAGUE}`;
  const [lg, ro, players, pj, sch, K] = await Promise.all([get(L), get(`${L}/rosters`), get(`${A}/players/nfl`), get(projURL(N)),
    get(`${S}/schedule/nfl/regular/${SEASON}`), kickoffs(get, N).catch(() => ({}))]);
  let tr = [];
  try { tr = await get(`${A}/players/nfl/trending/add?lookback_hours=48&limit=300`); } catch (e) { }
  const ss = lg.scoring_settings;
  const weeks = await Promise.all(Array.from({ length: D }, (_, i) => get(`${S}/stats/nfl/${SEASON}/${i + 1}?season_type=regular`)));
  const X = {};
  weeks.forEach(rows => { for (const r of rows) { const pos = r.player && r.player.position, s = r.stats || {};
    if (!FPOS.has(pos) || !(s.gp > 0)) continue; const e = X[r.player_id] || (X[r.player_id] = { pos, pts: 0, gp: 0 }); e.pts = r2(e.pts + leagueScore(s, ss)); e.gp++; } });
  const rk = {};
  for (const pos of FPOS) Object.entries(X).filter(([, e]) => e.pos === pos).sort((a, b) => b[1].pts - a[1].pts).forEach(([id], i) => rk[id] = i + 1);
  const own = new Set(ro.flatMap(r => r.players || []));
  const PJ = {}; for (const r of pj) PJ[r.player_id] = r2(leagueScore(r.stats || {}, ss));
  const OPP = {}; for (const g of sch.filter(x => x.week == N)) { OPP[g.home] = [g.away, 1]; OPP[g.away] = [g.home, 0]; }
  const AD = {}; for (const t of tr) AD[t.player_id] = t.count;
  const out = [];
  for (const id of new Set([...Object.keys(X), ...Object.keys(PJ)])) {
    if (own.has(id)) continue;
    const p = players[id] || {}, pos = (X[id] && X[id].pos) || p.position;
    if (!FPOS.has(pos)) continue;
    const pts = X[id] ? X[id].pts : 0, pr = PJ[id] || 0;
    if (pts <= 0 && pr < 1) continue;
    const team = pos === 'DEF' ? id : (p.team || null); if (!team) continue;
    const name = pos === 'DEF' ? `${p.first_name || id} ${p.last_name || ''}`.trim() : (p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim());
    const o = OPP[team] || [null, 0];
    out.push([id, name, pos, team, p.injury_status || null, pts, X[id] ? X[id].gp : 0, rk[id] || null, pr, o[0], o[1], (K[team] || [null])[0], AD[id] || 0]);
  }
  return { D, N, pulled: new Date().toISOString(), W: out };
}
