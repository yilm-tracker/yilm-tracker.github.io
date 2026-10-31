// One-time capture of a finished Sleeper season for the year switch: every API response the weekly pipeline would read,
// trimmed to the fields it uses, saved as gzip JSON maps {url: response} under history/raw/<year>/.
// The season pipeline then replays them offline (DT_CACHE), so a past season rebuilds without the network.
//   node pull_season.mjs 2025 1207898992206155776
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import { fileURLToPath } from 'node:url';
const DIR = path.dirname(fileURLToPath(import.meta.url));
const [Y, LID] = process.argv.slice(2);
const A = 'https://api.sleeper.app/v1', S = 'https://api.sleeper.com';
const FPOS = new Set(['QB', 'RB', 'WR', 'TE', 'K', 'DEF']);
async function get(u, tries = 5) {
  for (let i = 1; ; i++) {
    try { const r = await fetch(u, { headers: { 'user-agent': 'dynasty-tracker season capture' } }); if (!r.ok) throw new Error(r.status + ' ' + u); return await r.json(); }
    catch (e) { if (i >= tries) throw e; await new Promise(s => setTimeout(s, 1500 * i)); }
  }
}
const projURL = w => `${S}/projections/nfl/${Y}/${w}?season_type=regular` + ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'].map(p => `&position[]=${p}`).join('');
// two-way players (Sleeper lists Travis Hunter as DB) keep their fantasy position: the first of fantasy_positions the league scores
const fpos = p => p && (FPOS.has(p.position) ? p.position : (p.fantasy_positions || []).find(x => FPOS.has(x))) || null;
const pl = await get(`${A}/players/nfl`), POSOF = {};
for (const [id, p] of Object.entries(pl)) { const f = fpos(p); if (f) POSOF[id] = f; }
const slimRow = r => ({ player_id: r.player_id, team: r.team, opponent: r.opponent, player: r.player ? { position: POSOF[r.player_id] || r.player.position, first_name: r.player.first_name, last_name: r.player.last_name } : null, stats: r.stats });
const out = { core: {}, stats: {}, proj: {}, players: {} };
const L = `${A}/league/${LID}`;
for (const u of [L, `${L}/users`, `${L}/rosters`, `${L}/traded_picks`, `${L}/winners_bracket`, `${L}/losers_bracket`, `${S}/schedule/nfl/regular/${Y}`]) out.core[u] = await get(u);
for (let w = 1; w <= 18; w++) {
  if (w <= 17) out.core[`${L}/matchups/${w}`] = await get(`${L}/matchups/${w}`);
  out.core[`${L}/transactions/${w}`] = await get(`${L}/transactions/${w}`);
  out.core[`${S}/scores/nfl/regular/${Y}/${w}`] = (await get(`${S}/scores/nfl/regular/${Y}/${w}`)).map(x => ({ status: x.status, metadata: x.metadata ? { home_team: x.metadata.home_team, away_team: x.metadata.away_team, date_time: x.metadata.date_time } : null }));
  const su = `${S}/stats/nfl/${Y}/${w}?season_type=regular`;
  out.stats[su] = (await get(su)).filter(r => r.player && FPOS.has(POSOF[r.player_id] || r.player.position)).map(slimRow);
  out.proj[projURL(w)] = (await get(projURL(w))).map(slimRow);
  console.log('week', w, out.stats[su].length, 'stat rows');
}
const keep = {};
const F = ['full_name', 'first_name', 'last_name', 'position', 'fantasy_positions', 'team', 'injury_status', 'birth_date', 'years_exp'];
for (const [id, p] of Object.entries(pl)) if (p && (POSOF[id] || !/^\d+$/.test(id))) keep[id] = { ...Object.fromEntries(F.map(k => [k, p[k] ?? null])), position: POSOF[id] || p.position };
out.players[`${A}/players/nfl`] = keep;
const dst = path.join(DIR, 'history', 'raw', Y); fs.mkdirSync(dst, { recursive: true });
for (const [k, v] of Object.entries(out)) fs.writeFileSync(path.join(dst, k + '.json.gz'), zlib.gzipSync(JSON.stringify(v), { level: 9 }));
console.log('saved', Object.fromEntries(Object.keys(out).map(k => [k, fs.statSync(path.join(dst, k + '.json.gz')).size])));
