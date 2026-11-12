// CLI for the Sleeper pulls. Usage:
//   node pull.mjs state            -> prints {"done":D,"now":N} (last completed week)
//   node pull.mjs weekly D         -> pull_m7.json pull_pts.json pull8.json pull8a.json
//   node pull.mjs playoffs         -> pull_po.json
//   node pull.mjs live W           -> live.json (in-week scores for week W)
//   node pull.mjs faab           -> pull_faab.json (FAAB budget and each roster's balance)
//   node pull.mjs wire D           -> pull_wire.json (THE WIRE: unrostered players, week D+1 projections)
//   node pull.mjs top D            -> pull_top.json (top players by position through week D, all NFL players)
//   node pull.mjs detail a-b       -> stats_detail.json (full stat lines for lineup players, weeks a..b)
//   node pull.mjs teams W [full]   -> pull_teams.json (current NFL team + week-W opponent of the players in the files;
//                                     applied by teams.py; without full the players map is read only on a difference)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { lastCompleteWeek, pullWeekly, pullPlayoffs, pullLive, pullDetail, pullTop, pullWire, pullTeams } from './sleeper.mjs';
const DIR = path.dirname(fileURLToPath(import.meta.url));
const out = (f, o) => fs.writeFileSync(path.join(DIR, f), JSON.stringify(o));
// Offline replay of a captured season (pull_season.mjs): DT_CACHE=history/raw/2025 answers every request from the capture
import zlib from 'node:zlib';
let CACHE = null;
if (process.env.DT_CACHE) {
  CACHE = {};
  for (const k of ['core', 'stats', 'proj', 'players']) Object.assign(CACHE, JSON.parse(zlib.gunzipSync(fs.readFileSync(path.resolve(DIR, process.env.DT_CACHE, k + '.json.gz')))));
}
async function get(u, tries = 4) {
  if (CACHE) {
    if (u in CACHE) return JSON.parse(JSON.stringify(CACHE[u]));
    if (/\/state\/nfl$/.test(u)) return { season: process.env.DT_SEASON, season_type: 'regular', week: 18 };
    if (/\/(matchups|transactions)\/\d+$/.test(u)) return [];  // weeks outside the season (e.g. week 0 before Week 1)
    throw new Error('not in season capture: ' + u);
  }
  for (let i = 1; ; i++) {
    try {
      const r = await fetch(u, { headers: { 'user-agent': 'dynasty-tracker (github.com/billsblockparty/dynasty-tracker)' } });
      if (!r.ok) throw new Error(`${r.status} ${u}`);
      return await r.json();
    } catch (e) { if (i >= tries) throw e; await new Promise(s => setTimeout(s, 1500 * i)); }
  }
}
const [cmd, arg] = process.argv.slice(2);
if (cmd === 'state') {
  const { done } = await lastCompleteWeek(get);
  console.log(JSON.stringify({ done, now: done + 1 }));
} else if (cmd === 'weekly') {
  const x = await pullWeekly(get, +arg);
  for (const k of ['pull_m7', 'pull_pts', 'pull8', 'pull8a']) out(k + '.json', x[k]);
  console.log('weekly pull ok for week', arg);
} else if (cmd === 'faab') {
  // FAAB balances (standings card): league budget and each roster's amount left
  const { LEAGUE } = await import('./sleeper.mjs');
  const L = `https://api.sleeper.app/v1/league/${LEAGUE}`, [lg, ro] = await Promise.all([get(L), get(`${L}/rosters`)]);
  const B = +((lg.settings || {}).waiver_budget) || 0;
  out('pull_faab.json', { league: LEAGUE, budget: B, pulled: new Date().toISOString(), left: Object.fromEntries(ro.map(r => [r.roster_id, B - (+((r.settings || {}).waiver_budget_used) || 0)])) });
  console.log('faab pull ok, budget', B);
} else if (cmd === 'wire') {
  out('pull_wire.json', await pullWire(get, +process.argv[3]));
} else if (cmd === 'top') {
  const x = await pullTop(get, +arg);
  out('pull_top.json', x);
  console.log('top pull ok:', Object.keys(x.P).length, 'players through week', arg);
} else if (cmd === 'playoffs') {
  out('pull_po.json', await pullPlayoffs(get));
  console.log('playoff pull ok');
} else if (cmd === 'live') {
  const wk = JSON.parse(fs.readFileSync(path.join(DIR, `wk${arg}.json`), 'utf8'));
  // per roster: a player listed on another roster in wk W (moved since it was written) still needs a row (2026-11-08)
  const known = Object.fromEntries(Object.entries(wk.out).map(([r, X]) => [r, new Set([...X.st, ...X.bn].map(p => p[0]))]));
  const x = await pullLive(get, +arg, known);
  out('live.json', x);
  console.log('live pull ok: final', x.done.length / 2, 'games, live', x.live.length / 2, ', new starters', Object.keys(x.extra).length);
} else if (cmd === 'teams') {
  // every player in wk<W>.json, rosters.json, pull8.json and pull_top.json, with the NFL teams those files give him
  const rd = f => { try { return JSON.parse(fs.readFileSync(path.join(DIR, f), 'utf8')); } catch (e) { return null; } };
  const cur = {}, add = (id, t) => { (cur[id] = cur[id] || []); if (t && !cur[id].includes(t)) cur[id].push(t); };
  const wk = rd(`wk${arg}.json`); if (wk) for (const X of Object.values(wk.out)) for (const p of [...X.st, ...X.bn]) add(p[0], p[3]);
  const ro = rd('rosters.json'); if (ro) for (const L_ of Object.values(ro)) for (const p of L_) add(p[0], p[3]);
  const p8 = rd('pull8.json'); if (p8) for (const [id, m] of Object.entries(p8.META || {})) if (m) add(id, m[2]);
  const tp = rd('pull_top.json'); if (tp) for (const [id, p] of Object.entries(tp.P || {})) add(id, p[2]);
  const x = await pullTeams(get, +arg, cur, process.argv[4] === 'full');
  out('pull_teams.json', x);
  console.log('teams pull ok for week', arg, '(' + x.src + '):', Object.keys(x.T).length, 'players');
} else if (cmd === 'detail') {
  // fuller per-player stat lines for the Detailed lineup view: weeks "a-b" (or one week), lineup players only
  const [a, b] = arg.split('-').map(Number), f = path.join(DIR, 'stats_detail.json');
  const D = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : {};
  const x = await pullDetail(get, Array.from({ length: (b || a) - a + 1 }, (_, i) => a + i));
  Object.assign(D, x); out('stats_detail.json', D);
  console.log('detail pull ok:', Object.entries(x).map(([w, v]) => `wk${w} ${Object.keys(v).length}`).join(', '));
} else { console.error('usage: node pull.mjs state|weekly D|playoffs|live W|detail a-b|teams W [full]'); process.exit(2); }
