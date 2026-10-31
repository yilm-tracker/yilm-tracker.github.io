// One-time (re-runnable) import of past seasons into pipeline/history/:
//   MFL league 68106, 2021-2024  -> mfl_<year>.json
//   Sleeper 2025 (previous_league_id of the current league) -> sleeper_2025.json
// Compact shapes; player lines are "id:score:s|b<shouldStart 1|0>" (MFL) or [id, pts, starter] (Sleeper).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), 'history');
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function get(u, tries = 6) {
  for (let i = 1; ; i++) {
    try { const r = await fetch(u, { headers: { 'user-agent': 'dynasty-tracker (github.com/billsblockparty/dynasty-tracker)' } });
      if (!r.ok) throw new Error(r.status + ' ' + u); const j = await r.json(); await sleep(u.includes('myfantasyleague') ? 1500 : 250); return j; }
    catch (e) { if (i >= tries) throw e; await sleep((String(e).startsWith('Error: 429') ? 30000 : 1500) * i); }
  }
}
const arr = x => x == null ? [] : [].concat(x);
const MFL = (y, q) => `https://api.myfantasyleague.com/${y}/export?L=68106&JSON=1&${q}`;
async function mfl(y) {
  const out = { year: y, weeks: {} };
  const lg = (await get(MFL(y, 'TYPE=league'))).league;
  out.fr = arr(lg.franchises.franchise).map(f => [f.id, f.name.trim()]);
  out.lastRegular = +lg.lastRegularSeasonWeek; out.starters = lg.starters;
  out.standings = arr((await get(MFL(y, 'TYPE=leagueStandings'))).leagueStandings.franchise)
    .map(f => ({ id: f.id, w: +f.h2hw, l: +f.h2hl, t: +f.h2ht, pf: +f.pf, pa: +f.pa }));
  const ids = new Set();
  for (let w = 1; w <= 17; w++) {
    const W = (await get(MFL(y, `TYPE=weeklyResults&W=${w}`))).weeklyResults;
    if (!W || !W.matchup) { out.weeks[w] = []; continue; }
    out.weeks[w] = arr(W.matchup).map(m => ({ reg: m.regularSeason === '1', f: arr(m.franchise).map(f => {
      arr(f.player).forEach(p => ids.add(p.id));
      return { id: f.id, score: +f.score, result: f.result, home: f.isHome === '1',
        pl: arr(f.player).map(p => `${p.id}:${p.score === undefined ? '' : p.score}:${p.status === 'starter' ? 's' : 'b'}${p.shouldStart === '1' ? 1 : 0}`).join(',') };
    }) }));
  }
  out.brackets = [];
  for (const b of arr((await get(MFL(y, 'TYPE=playoffBrackets'))).playoffBrackets?.playoffBracket)) {
    const r = (await get(MFL(y, `TYPE=playoffBracket&BRACKET_ID=${b.id}`))).playoffBracket;
    out.brackets.push({ id: b.id, name: b.name, title: b.bracketWinnerTitle,
      rounds: arr(r.playoffRound).map(rd => ({ week: +rd.week, games: arr(rd.playoffGame).map(g => ({
        home: { id: g.home.franchise_id, pts: +g.home.points, seed: g.home.seed || null },
        away: { id: g.away.franchise_id, pts: +g.away.points, seed: g.away.seed || null } })) })) });
  }
  out.players = {};
  const list = [...ids];
  for (let i = 0; i < list.length; i += 150) {
    const P = (await get(MFL(y, `TYPE=players&PLAYERS=${list.slice(i, i + 150).join(',')}`))).players;
    for (const p of arr(P?.player)) out.players[p.id] = [p.name, p.position, p.team];
  }
  return out;
}
async function sleeper2025() {
  const A = 'https://api.sleeper.app/v1';
  const cur = await get(`${A}/league/1335450123487961088`);
  const L = cur.previous_league_id;
  const [lg, users, rosters, wb, lb] = await Promise.all([get(`${A}/league/${L}`), get(`${A}/league/${L}/users`), get(`${A}/league/${L}/rosters`),
    get(`${A}/league/${L}/winners_bracket`), get(`${A}/league/${L}/losers_bracket`)]);
  const out = { year: +lg.season, league_id: L, playoff_week_start: lg.settings.playoff_week_start, weeks: {},
    users: users.map(u => [u.user_id, u.display_name, (u.metadata || {}).team_name || null]),
    rosters: rosters.map(r => ({ rid: r.roster_id, owner: r.owner_id, w: r.settings.wins, l: r.settings.losses, t: r.settings.ties,
      pf: r.settings.fpts + (r.settings.fpts_decimal || 0) / 100, pa: (r.settings.fpts_against || 0) + (r.settings.fpts_against_decimal || 0) / 100 })),
    winners_bracket: wb, losers_bracket: lb };
  const ids = new Set();
  for (let w = 1; w <= 17; w++) {
    const m = await get(`${A}/league/${L}/matchups/${w}`);
    out.weeks[w] = m.map(x => { Object.keys(x.players_points || {}).forEach(i => ids.add(i));
      return { rid: x.roster_id, mid: x.matchup_id, pts: x.points, st: x.starters, pp: x.players_points }; });
  }
  const P = await get(`${A}/players/nfl`);
  out.players = {};
  for (const i of ids) { const p = P[i]; out.players[i] = p ? [p.full_name || `${p.first_name} ${p.last_name}`, p.position, p.team || null] : [i, null, null]; }
  return out;
}
fs.mkdirSync(DIR, { recursive: true });
const log = { ran: new Date().toISOString(), ok: [], err: {} };
const seasons = [];
for (const y of [2021, 2022, 2023, 2024]) {
  if (fs.existsSync(path.join(DIR, `mfl_${y}.json`))) { seasons.push(y); log.ok.push(`mfl ${y} (kept)`); continue; }
  try { const d = await mfl(y); fs.writeFileSync(path.join(DIR, `mfl_${y}.json`), JSON.stringify(d)); seasons.push(y); log.ok.push(`mfl ${y}`);
    console.log('MFL', y, 'weeks', Object.keys(d.weeks).length, 'players', Object.keys(d.players).length); }
  catch (e) { log.err[`mfl ${y}`] = String(e && e.stack || e); console.log('MFL', y, 'FAILED', e); }
}
if (fs.existsSync(path.join(DIR, 'sleeper_2025.json'))) { seasons.push(2025); log.ok.push('sleeper 2025 (kept)'); }
else try { const s = await sleeper2025(); fs.writeFileSync(path.join(DIR, `sleeper_${s.year}.json`), JSON.stringify(s)); seasons.push(s.year); log.ok.push(`sleeper ${s.year}`);
  console.log('Sleeper', s.year, 'players', Object.keys(s.players).length); }
catch (e) { log.err.sleeper = String(e && e.stack || e); console.log('Sleeper FAILED', e); }
fs.writeFileSync(path.join(DIR, 'log.json'), JSON.stringify(log, null, 1));
// manifest marks the import done; only written when every season came through, so a partial import retries next run
if (!Object.keys(log.err).length) fs.writeFileSync(path.join(DIR, 'manifest.json'), JSON.stringify({ imported: log.ran, seasons }));
