// CLI for the Sleeper pulls. Usage:
//   node pull.mjs state            -> prints {"done":D,"now":N} (last completed week)
//   node pull.mjs weekly D         -> pull_m7.json pull_pts.json pull8.json pull8a.json
//   node pull.mjs playoffs         -> pull_po.json
//   node pull.mjs live W           -> live.json (in-week scores for week W)
//   node pull.mjs top D            -> pull_top.json (top players by position through week D, all NFL players)
//   node pull.mjs detail a-b       -> stats_detail.json (full stat lines for lineup players, weeks a..b)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { lastCompleteWeek, pullWeekly, pullPlayoffs, pullLive, pullDetail, pullTop } from './sleeper.mjs';
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
} else if (cmd === 'top') {
  const x = await pullTop(get, +arg);
  out('pull_top.json', x);
  console.log('top pull ok:', Object.keys(x.P).length, 'players through week', arg);
} else if (cmd === 'playoffs') {
  out('pull_po.json', await pullPlayoffs(get));
  console.log('playoff pull ok');
} else if (cmd === 'live') {
  const wk = JSON.parse(fs.readFileSync(path.join(DIR, `wk${arg}.json`), 'utf8'));
  const known = new Set(Object.values(wk.out).flatMap(X => [...X.st, ...X.bn].map(p => p[0])));
  const x = await pullLive(get, +arg, known);
  out('live.json', x);
  console.log('live pull ok: final', x.done.length / 2, 'games, live', x.live.length / 2, ', new starters', Object.keys(x.extra).length);
} else if (cmd === 'detail') {
  // fuller per-player stat lines for the Detailed lineup view: weeks "a-b" (or one week), lineup players only
  const [a, b] = arg.split('-').map(Number), f = path.join(DIR, 'stats_detail.json');
  const D = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : {};
  const x = await pullDetail(get, Array.from({ length: (b || a) - a + 1 }, (_, i) => a + i));
  Object.assign(D, x); out('stats_detail.json', D);
  console.log('detail pull ok:', Object.entries(x).map(([w, v]) => `wk${w} ${Object.keys(v).length}`).join(', '));
} else { console.error('usage: node pull.mjs state|weekly D|playoffs|live W|detail a-b'); process.exit(2); }
