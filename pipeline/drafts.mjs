// Draft history for the Drafts tab (YILM: Sleeper only) -> pipeline/history/drafts.json (re-runnable; finished drafts are kept).
//   MFL league 68106, 2021-2024: draftResults (who picked whom), draft-pick trades (to tell the original owner of a
//   traded pick), the league's draft order settings, and names for every drafted player.
//   Sleeper 2025 onward (the current league and its previous_league_id chain): drafts, picks, traded picks.
// Shape per year: { src, type, rounds, teams, slots: {slot: originalOwnerName}, picks: [[round, pick, slot, origName,
//   byName, player, pos, nfl], ...], raw: {...} }  (team names are mapped to current names when known)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), 'history');
const OUT = path.join(DIR, 'drafts.json');
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function get(u, tries = 5) {
  for (let i = 1; ; i++) {
    try { const r = await fetch(u, { headers: { 'user-agent': 'dynasty-tracker (github.com/billsblockparty/dynasty-tracker)' } });
      if (!r.ok) throw new Error(r.status + ' ' + u); const j = await r.json(); await sleep(u.includes('myfantasyleague') ? 1500 : 200); return j; }
    catch (e) { if (i >= tries) throw e; await sleep((String(e).startsWith('Error: 429') ? 30000 : 1500) * i); }
  }
}
const arr = x => x == null ? [] : [].concat(x);
const MFL = (y, q) => `https://api.myfantasyleague.com/${y}/export?L=68106&JSON=1&${q}`;
const TEAMS = fs.existsSync(path.join(DIR, 'teams.json')) ? JSON.parse(fs.readFileSync(path.join(DIR, 'teams.json'), 'utf8')) : {};
const old = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};
const out = { ...old };
const log = [];
async function mfl(y) {
  const nm = id => (TEAMS.mfl || {})[id] || id;
  const lg = (await get(MFL(y, 'TYPE=league'))).league;
  const dr = (await get(MFL(y, 'TYPE=draftResults'))).draftResults;
  const units = arr(dr && dr.draftUnit);
  const picks = units.flatMap(u => arr(u.draftPick));
  // trades of draft picks this year: "DP_r_p" (this year's draft, round r+1 pick p+1) and "FP_FFFF_YYYY_R" (future pick, original franchise FFFF)
  let trades = [];
  try { trades = arr((await get(MFL(y, 'TYPE=transactions&TRANS_TYPE=TRADE'))).transactions?.transaction); } catch (e) { log.push(`mfl ${y} trades: ${e}`); }
  let trPrev = [];
  try { trPrev = arr((await get(MFL(y - 1, 'TYPE=transactions&TRANS_TYPE=TRADE'))).transactions?.transaction); } catch (e) { }
  const ids = [...new Set(picks.map(p => p.player).filter(Boolean))];
  const PL = {};
  for (let i = 0; i < ids.length; i += 150) {
    const P = (await get(MFL(y, `TYPE=players&PLAYERS=${ids.slice(i, i + 150).join(',')}`))).players;
    for (const p of arr(P && P.player)) { const [l, f] = String(p.name).split(', '); PL[p.id] = [f ? `${f} ${l}` : p.name, p.position, p.team]; }
  }
  const rows = picks.map(p => [+p.round, +p.pick, null, null, nm(p.franchise), ...(PL[p.player] || [p.player || '', null, null]), p.comments || '']);
  return { src: 'mfl', year: y, type: y === 2021 ? 'startup' : 'rookie', rounds: Math.max(0, ...rows.map(r => r[0])), teams: (TEAMS.mfl ? Object.keys(TEAMS.mfl).length : 10),
    picks: rows, raw: { draft: { kind: lg.draft_kind, type: lg.draftType || lg.draft_type, order: lg.draftOrder || null, units: units.map(u => ({ unit: u.unit, type: u.draftType, round1: u.round1DraftOrder })) },
      trades: trades.concat(trPrev).filter(t => /(DP_|FP_)/.test((t.franchise1_gave_up || '') + (t.franchise2_gave_up || ''))).map(t => ({ ts: t.timestamp, f1: t.franchise, f2: t.franchise2, g1: t.franchise1_gave_up, g2: t.franchise2_gave_up })) } };
}
async function sleeperChain() {
  const A = 'https://api.sleeper.app/v1';
  let L = process.env.DT_LEAGUE || '1335450123487961088';
  while (L && L !== '0') {
    const lg = await get(`${A}/league/${L}`);
    const y = +lg.season;
    const [users, rosters, drafts] = await Promise.all([get(`${A}/league/${L}/users`), get(`${A}/league/${L}/rosters`), get(`${A}/league/${L}/drafts`)]);
    const rid2user = {}; for (const r of rosters) rid2user[r.roster_id] = r.owner_id;
    const uname = {}; for (const u of users) uname[u.user_id] = (u.metadata || {}).team_name || u.display_name;
    const rname = rid => (TEAMS.sleeper_roster || {})[String(rid)] || uname[rid2user[rid]] || `Team ${rid}`;
    // one draft per season: the latest completed one (the first Sleeper season also has the roster-migration drafts)
    const done = drafts.filter(x => x.status === 'complete').sort((a, b) => (b.start_time || 0) - (a.start_time || 0));
    for (const d of done.slice(0, 1)) {
      const key = String(y);
      const pk = await get(`${A}/draft/${d.draft_id}/picks`);
      let dtp = []; try { dtp = await get(`${A}/draft/${d.draft_id}/traded_picks`); } catch (e) { }
      // slot -> roster: slot_to_roster_id when Sleeper fills it, else the draft order (user -> slot) joined to roster owners
      let s2r = d.slot_to_roster_id || {};
      if (!Object.keys(s2r).length && d.draft_order) { const u2r = {}; for (const r of rosters) u2r[r.owner_id] = r.roster_id; s2r = {}; for (const [u, sl] of Object.entries(d.draft_order)) if (u2r[u]) s2r[sl] = u2r[u]; }
      out[key] = { src: 'sleeper', year: y, type: d.settings && d.settings.rounds > 8 ? 'startup' : 'rookie', rounds: d.settings ? d.settings.rounds : null, teams: d.settings ? d.settings.teams : null,
        raw: { draft_order: d.draft_order || null, slot_to_roster_id: d.slot_to_roster_id || null, traded_picks: dtp, rosters: rosters.map(r => [r.roster_id, r.owner_id]), picks: pk.map(p => [p.round, p.pick_no, p.draft_slot, p.roster_id, p.picked_by]) },
        draft_type: d.type, name: (d.metadata || {}).name || null, start: d.start_time || null, season_type: d.season_type || null, settings: d.settings || {}, slots: Object.fromEntries(Object.entries(s2r).map(([s, r]) => [s, rname(r)])),
        picks: pk.map(p => { const m = p.metadata || {}; return [p.round, p.pick_no, p.draft_slot, rname(s2r[p.draft_slot]), rname(p.roster_id), `${m.first_name || ''} ${m.last_name || ''}`.trim(), m.position || null, m.team || null, ''] }) };
      log.push(`sleeper ${key} ${pk.length} picks`);
    }
    L = lg.previous_league_id;
  }
}
for (const k of Object.keys(out)) if (/-/.test(k)) delete out[k];
for (const y of (TEAMS.mfl ? [2021, 2022, 2023, 2024] : [])) {  // MFL years only for a league that has them
  if (old[y] && old[y].src === 'mfl') { log.push(`mfl ${y} kept`); continue; }
  try { out[y] = await mfl(y); log.push(`mfl ${y} ${out[y].picks.length} picks`); } catch (e) { log.push(`mfl ${y} failed: ${e}`); }
}
try { await sleeperChain(); } catch (e) { log.push(`sleeper failed: ${e}`); }
fs.writeFileSync(OUT, JSON.stringify(out));
console.log('drafts:', log.join('; '));
