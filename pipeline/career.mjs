// Career fantasy points for every drafted player (Drafts tab) -> pipeline/career.json. Never fatal to the build.
// Every regular season a player has stats for (Sleeper season totals, 2009 on), scored with THIS league's current
// scoring settings, so the numbers compare across players and eras. Players are matched to Sleeper ids by name +
// position (MFL-era picks only have names). Output: { "<name key>|<POS>": [points, games, seasons with a game,
// first season counted, last season counted, partial (career started before 2009)], _meta: {...} }
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { leagueScore } from './sleeper.mjs';
const P = path.dirname(fileURLToPath(import.meta.url));
const A = 'https://api.sleeper.app/v1', S = 'https://api.sleeper.com';
const LEAGUE = process.env.DT_LEAGUE || '1335450123487961088', FIRST = 2009;
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function get(u, tries = 4) {
  for (let i = 1; ; i++) {
    try { const r = await fetch(u, { headers: { 'user-agent': 'fantasy-tracker career points' } }); if (!r.ok) throw new Error(r.status + ' ' + u); return await r.json(); }
    catch (e) { if (i >= tries) throw e; await sleep(1500 * i); }
  }
}
export const nameKey = s => String(s || '').toLowerCase().replace(/[.'’`,]/g, '').replace(/-/g, ' ')
  .replace(/\b(jr|sr|ii|iii|iv|v)\b/g, '').replace(/\s+/g, ' ').trim();
const POSFIX = { PK: 'K', Def: 'DEF', DST: 'DEF' };
try {
  const D = JSON.parse(fs.readFileSync(path.join(P, 'history', 'drafts.json'), 'utf8'));
  const want = new Map();  // key -> [name, pos]
  for (const d of Object.values(D)) for (const r of d.picks || []) { const pos = POSFIX[r[6]] || r[6]; if (r[5]) want.set(nameKey(r[5]) + '|' + pos, [r[5], pos]); }
  const lg = await get(`${A}/league/${LEAGUE}`), ss = lg.scoring_settings, season = +lg.season;
  const PL = await get(`${A}/players/nfl`);
  const byKey = new Map();
  for (const [pid, p] of Object.entries(PL)) {
    const nm = p.full_name || `${p.first_name || ''} ${p.last_name || ''}`;
    for (const pos of new Set([p.position, ...(p.fantasy_positions || [])])) { const k = nameKey(nm) + '|' + pos; (byKey.get(k) || byKey.set(k, []).get(k)).push(pid); }
  }
  const pick = {};  // key -> pid (several players can share a name: the one with the most NFL seasons wins, then the active one)
  let miss = [];
  for (const [k] of want) {
    const c = byKey.get(k) || [];
    if (!c.length) { miss.push(k); continue; }
    c.sort((a, b) => (PL[b].years_exp || 0) - (PL[a].years_exp || 0) || (PL[b].active ? 1 : 0) - (PL[a].active ? 1 : 0));
    pick[k] = c[0];
  }
  const ids = new Set(Object.values(pick));
  const start = Math.max(FIRST, Math.min(season, ...[...ids].map(id => season - (PL[id].years_exp || 0))));
  const tot = {};  // pid -> [pts, gp, seasons, first, last]
  for (let y = start; y <= season; y++) {
    let rows;
    try { rows = await get(`${S}/stats/nfl/${y}?season_type=regular`); } catch (e) { console.log('career: season', y, 'skipped:', String(e)); continue; }
    const list = Array.isArray(rows) ? rows : Object.entries(rows).map(([player_id, stats]) => ({ player_id, stats }));
    for (const r of list) {
      if (!ids.has(String(r.player_id))) continue;
      const s = r.stats || {}, gp = +s.gp || 0, pts = leagueScore(s, ss);
      if (!gp && !pts) continue;
      const t = tot[r.player_id] || (tot[r.player_id] = [0, 0, 0, y, y]);
      t[0] += pts; t[1] += gp; if (gp) t[2]++; t[3] = Math.min(t[3], y); t[4] = Math.max(t[4], y);
    }
    await sleep(250);
  }
  const out = { _meta: { league: LEAGUE, through: season, first: start, updated: new Date().toISOString(), unmatched: miss } };
  for (const [k] of want) {
    const id = pick[k]; if (!id) continue;
    const t = tot[id] || [0, 0, 0, null, null], rookie = season - (PL[id].years_exp || 0);
    out[k] = [Math.round(t[0] * 10) / 10, t[1], t[2], t[3], t[4], rookie < FIRST];
  }
  fs.writeFileSync(path.join(P, 'career.json'), JSON.stringify(out));
  console.log(`career: ${Object.keys(out).length - 1} players, seasons ${start}-${season}, ${miss.length} unmatched${miss.length ? ' (' + miss.slice(0, 8).join(', ') + ')' : ''}`);
} catch (e) { console.log('career: skipped:', String(e)); }
