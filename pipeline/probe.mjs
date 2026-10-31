// Live-game probe (diagnostic, temporary): during a live run, records what Sleeper's public endpoints say about
// players in games that are in progress, so we can tell whether projections update mid-game and what game-clock
// data the scores feed carries. Writes ../debug/probe/<UTC>.json. Never fails the build.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const P = path.dirname(fileURLToPath(import.meta.url)), OUT = path.join(P, '..', 'debug', 'probe');
const S = 'https://api.sleeper.com', SEASON = '2026';
const get = async u => { const r = await fetch(u); if (!r.ok) throw new Error(r.status + ' ' + u); return r.json(); };
try {
  const W = +process.argv[2];
  const sc = await get(`${S}/scores/nfl/regular/${SEASON}/${W}`);
  const live = sc.filter(x => x.status === 'in_game');
  if (!live.length) { console.log('probe: no game in progress'); process.exit(0); }
  const teams = new Set(live.flatMap(x => [x.metadata?.home_team, x.metadata?.away_team]));
  const pos = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'].map(p => `&position[]=${p}`).join('');
  const [pj, st] = await Promise.all([get(`${S}/projections/nfl/${SEASON}/${W}?season_type=regular${pos}`), get(`${S}/stats/nfl/${SEASON}/${W}?season_type=regular`)]);
  const keep = r => teams.has(r.team) && (r.stats?.pts_half_ppr || 0) > 2;
  const out = { at: new Date().toISOString(), week: W,
    games: live.map(x => ({ status: x.status, metadata: x.metadata, keys: Object.keys(x) })),
    proj: pj.filter(keep).slice(0, 40).map(r => ({ id: r.player_id, team: r.team, updated: r.updated_at || r.last_modified || null, ppr_half: r.stats?.pts_half_ppr, keys: Object.keys(r) })),
    stats: st.filter(r => teams.has(r.team) && (r.stats?.pts_half_ppr || 0) > 0).slice(0, 40).map(r => ({ id: r.player_id, team: r.team, pts: r.stats?.pts_half_ppr })) };
  fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(path.join(OUT, out.at.replace(/[:.]/g, '-') + '.json'), JSON.stringify(out));
  console.log('probe: saved', out.proj.length, 'projections,', live.length, 'live games');
} catch (e) { console.log('probe failed (ignored):', e.message); }
