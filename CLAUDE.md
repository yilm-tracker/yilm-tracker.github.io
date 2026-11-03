# Fantasy trackers: working notes (read first)

Two sister sites built by the same pipeline. This file is identical in both repos.

| | BBP (Bill's Block Party dynasty) | YILM (Your Idiot Leaguemates) |
|---|---|---|
| Repo | billsblockparty/dynasty-tracker | yilm-tracker/yilm-tracker.github.io |
| Local clone | /home/claude/dynasty-tracker | /home/claude/yilm-tracker.github.io |
| Site | billsblockparty.github.io/dynasty-tracker | yilm-tracker.github.io |
| League | 10 teams, 1QB, Sleeper 1335450123487961088 (2025+), MFL 68106 (2021-24) | 12 teams, Sleeper 1363550282381795328 (2026), 1261744566235574272 (2025) |
| FAAB budget | $200 | $200 |

## Standing rules (from Nicklaus; non-negotiable)

1. **Every UI change goes to BOTH trackers, 1 for 1.** Only exceptions: MFL history (BBP only), the Jaguars art/palette and rank-numeral art (BBP), round-logo shadows on profile pictures (BBP; YILM has faces). The Bill's Block Party team is the user's own: never highlight it.
2. **Workflow per change:** edit `pipeline/` in both repos, build locally, QA, commit (clear message), `git pull --rebase` then push, wait for the Actions deploy (`gh run list -L 1`), send a screenshot, report briefly.
3. **Test widths:** 402 first (regular iPhone Pro), then 440 (his phone), 360 (floor), 1440 desktop. No sideways scroll, nothing clipped, nothing ellipsised (`…`), no overflow.
4. **Visual precision on the FIRST iteration**, not after feedback:
   - **Rank tiles beside a figure are never taller than the figure and never poke above its cap top or below its baseline.** Check EVERY time with `python3 tools/tilechk.py 402 440 360 1440`; expect 0 violations on both trackers (exact to 0.05px, Dumb and Nerd).
   - Digits never touch a tile frame; gap ink-to-frame equal top/bottom and left/right (judged by glyph ink, not the text box).
   - Equal ink gaps; stacked tiles share one width and one left edge across rows; logos centred on what they sit beside.
   - Elements must not move between states (Dumb/Nerd, H2H/Median, re-fits on resize).
   - Use the available width; no dead space.
5. **Fonts in local QA:** the site uses Google Fonts (Barlow Condensed display, IBM Plex Sans body), which do not load in the sandbox. Always run Playwright with `tools/realfonts.py` (see its header for the one-time npm install). Measurements without it are wrong (e.g. false header overflow at 402).
6. Clinical tone; verify any arithmetic in Python; no Reddit/Wikipedia as sources.
7. **Secrets/licensing:** never enter API keys (the user adds `FP_API_KEY` in GitHub settings). FantasyPros data is personal-use: keep it out of the public repos (Actions cache only), show team totals only.
8. Commit attribution lines as the session's system reminder specifies.

## Build and deploy

- Static GitHub Pages site. `.github/workflows/site.yml` runs on push to `pipeline/**`, weekly (Tue 10:17 and 15:17 UTC) and every 10 min in game windows (`live`).
- Modes (`pipeline/run.py <mode>`): `weekly` (pull completed week + full rebuild; push events use this), `live` (scores now), `build` (no network), `history`.
- Live runs do not commit data; weekly runs commit `pipeline/*.json` ("Save season data"). Workflow rebases with `-X theirs` on data conflicts.
- **BBP local build:** `cd pipeline && python3 run.py build` → `site/index.html`.
- **YILM local build:** `cd pipeline && python3 season_replay.py 2026 --build-only` → `.season/2026/site/index.html`. YILM builds by replaying its saved Sleeper data (`history/raw/<year>/*.json.gz`, refreshed in CI by `pull_season.mjs`) in a workspace copy `.season/<year>/pipeline`. Past seasons set `DT_PAST=1`.
- The sandbox has no network to Sleeper/MFL; data for local builds comes from the committed JSON (pull from origin first).

## Page architecture

- `rebuild.py` assembles `standings.html` = `new_head.html` (base CSS) + data globals (`data_block.js`, `AVR` team→avatar id, `RNI` numeral art, `NIK` YILM nicknames, `FAAB*`) + tab sections + `new_tail.js` (all page JS). `gen.js` and `build_static.py` render, `build_site.py` wraps into `site/index.html`.
- **`pipeline/readability.css` is appended last**: all recent overrides live at its end. Do not put `!important` on font sizes that JS fits (it blocks the fitter).
- `build_site.py` hides `body>*` until a final `<style>` at the end of body (no flash on load); page background from the last `--pg` in readability.css. It also builds the season/year buttons (`yrs`).
- Tabs: Standings, Leaderboards, Stats, Rosters, Matchups, Compare, Playoffs, Players, The Wire, Drafts, Team Hub. Each tab has a `*_build.py` writing `*_section.html` and `*_css.css` (see the header comment of each file).
- Data pulls: `sleeper.mjs` (pure pull functions), `pull.mjs` CLI (`weekly`, `live`, `wire`, `top`, `detail`, `faab`, `state`), `drafts.mjs`, `history.mjs`, `fp_pull.py`.

### Fitting functions in new_tail.js (each owns one thing)

- `tabFit`: tab labels. `ddFit`: dropdown labels.
- `tnFit`: standings names. First sets every row's name padding-right to clear the widest record tile (W3 4-3) + 6px, and gives all FAAB tiles one width. Then per name: one line if ≥85% of full size (22px, 19px ≤380), else two lines at the largest fitting size, three only when two would be <15px and three fit within 52px; never a cut word.
- `mvAl`: position-change arrow (inside the name text, after the last word, `.68em`) set on the name's cap centre via vertical-align; name block nudged so the name's cap top is level with the logo/face top.
- `ravFit`: legacy logo sizing (early-returns on BBP since the Hi/Lo line is gone).
- `sbFit`: stat lines PF/PA/Tot Eff share scale `--sbs` and text column `--stw2`; `.sbm` measures all rows so dots don't move between modes. Desktop (>=1100px): only PF/PA set the scale (Tot Eff is in the right column). If the 0.68 floor still cannot fit a line, the scale resets to 1 (it used to stick at the floor, so a 1px width change flipped all stat text between full size and 68% and moved the dots; reported on Nicklaus's Mac, not reproducible in Chromium).
- `s2Fit`: Opp/All-play/Luck line scale `--s2s` down to 0.81, else `.wrp` (Luck on its own line, all rows together).
- `fit` (= `window.tileFit`) + `inkTile`: rank tiles. Tile height = the figure's digit cap height to 0.25px (frames are inset shadows, inside that height; outer height trimmed to it exactly after sizing), digit-ink-to-frame gap 1.75-3.5px so the digits fill the tile, centred on the figure's cap height using its real baseline (a zero-size marker on it, read after sizing), on every line. Old transforms are cleared before the on-line check. Font metrics cache (`FM`) is cleared each run. Transform reset before measuring (re-runs never stack). Luck tile references the luck value, not the grey xW text (`.lku` skipped).
- `rrFit`: standings right column (streak tile size, Could have alignment), then re-runs `tnFit`. `rslFit`: Rosters season-totals line (own line when it would reach the points).
- `nrdFit`: desktop only, stacks the Nerd blocks in the right-hand column of each standings row.
- `rniSnap`: snaps numeral art to whole pixels. `finFit`: sim Finish tile height = projection figures.

## Standings card (current design)

- **Board and tiers**: one card (`#list.board`); each tier is a plain `section.tcard` (built in `draw()`). Rows run edge to edge in alternating shades (first row of each tier lighter, `rgba(238,240,244,.055)`). Each tier header is a band tinted in the tier colour (19%), from the tear line (dotted perforation with a semicircle notch bitten out of each edge; none above Bye) down to just under the tier name, closed by a 2px rule in the tier colour; name / seeds / Line in lighter tints of it. Panel shadow is firm down both sides and along the bottom. Dots (rank dots and last-5) have a dark outer ring (reference: Sleeper-style ringed dots); whole-pixel sizes, `space-between`, ring sized so neighbours never touch. Nicklaus rejected a coloured bar along the card top (looks generic). The class `.tg` is taken (toggle groups).
- **Desktop (>=1100px)**: one team per row. Left: rank, logo, name, Opp/All-play/Luck, PF, PA, record column (`102px 270px 84px 78px`); right column (after a thin divider): Tot Eff, Dropped pts + Season sim, season chart, stacked by `nrdFit` (all three share one grid cell spanning to a final `1fr` row, so the right stack never stretches the left rows). The left side is identical in Dumb and Nerd.
- Row: rank numeral art (BBP: `rank_tiles_gold_alabaster_teal.zip`, with_buffer/squared, served byte-for-byte from `ranknum/r1-12.webp` (do not crop or re-encode): brushed gold 1-2, alabaster 3-6, teal 7-12, shadow baked in; one rule `.rni{height:var(--rt)}` with `--rt:44px`, no per-tier size/filter/opacity; fixed 52px rank column (`--rks`), tile centred; `alt="N"` + `aria-label="Rank N"`; Team Hub uses the same tiles at 44px) + logo 50px (44 ≤380; BBP shadow: 1px ring + identical circle offset 2px/2px + blur at same offset) + name block + right column: W-L record (35.1px; 29.7px for 4-digit records), then one row under it (`.l5r`, pulled up into the record's descender space, 3px below its baseline): streak tile (height = the record's cap at 26px, 22px at <=380) left of the last-5 dots; then Could have / Breakdown (Dumb and Nerd), label cap top level with the OPP RK line (`rrFit`: first stat line starting 4px clear of the streak row). Dots: the dark ring is the dot's own border (box-sizing border-box), never a box-shadow ring (snapped separately, drifts off-centre). Games back and the Leader label were removed 2026-11-03.
- Name block: name (cap top level with logo top) + ▲/▼ change; under it the **FAAB tile** (raised, same shadow depth as the logo; "FAAB" label to its right; tap opens The Wire). YILM: manager nickname under the FAAB line.
- FAAB data: `pull.mjs faab` → `pull_faab.json` (BBP; run in weekly and live), `season_replay.py` writes it for YILM from the capture; `rebuild.py` emits `FAABB, FAABL, FAABR, FAAB` (current season only); the page re-reads Sleeper rosters on load (`waiver_budget − waiver_budget_used`).
- Stat lines: Opp rk / All-play / Luck (+ grey `n.nn xW` = all-play win rate × games; luck = wins − xW). PF and PA alabaster with grey `/wk`; dots green only (no gold for #1; the tile shows 1 in gold).
- Hi/Lo/Avg seed was removed from the card; Team Hub shows "Highest / lowest seed" and "Average seed" (standings positions, `SER[t]['stand']`, not weekly score ranks).
- Season sim: 1.0 shown gold, no tile; title right-aligned.

## BBP kit palette (Standings Redesign Spec, 2026-11-03; BBP only)

- Tokens at the end of BBP `readability.css`: `--pg #101b1f` (page), `--deck #1a2c33` (panel: board, every second row, header bands, nav buttons, year tabs, toggle tracks), `--row-alt #203841` (other rows, FAAB pills), tiers `--tier-bye #e2cf93` / `--tier-po #19b5c4` / `--tier-ch #cda74b` (label, sub-labels and header rule at full colour; band = tier 10% over panel), season chart `--chart-po-line #0097a7`, `--chart-po-fill #023442`, `--chart-po-val #19b5c4`, `--chart-nfl-bye #5a6870`.
- `--pylon`/`--sky` are NOT redefined (used across other tabs); standings/chart uses are overridden one by one (sim BYE/PLAYOFFS labels, desktop table tier rows, seeds and odds columns, focus outline).
- Spec contrast checks pass (verified in Python). Left unchanged by design: status colours (form dots, streaks, arrows, rank chips), cream text, the position colours (TE stays orange).

## Drafts tab

- Each pick row: pick tile (position colour) | player name + NFL logo, career points chip (on its own line under the name below 760px, inline above) | team column of one fixed width (`--dfbw` 140/124/112px) behind a 3px page-colour divider, so every avatar starts on the same left edge; owner name over a gold "VIA <orig owner>" box when the pick was traded.
- Career points: `career.mjs` (CI only; BBP `run.py` weekly/history, YILM `season_replay.py` after `drafts.mjs`) matches each drafted player to a Sleeper id by name + position, sums Sleeper season totals 2009-now scored with the league's current scoring settings -> `career.json` (`"<name key>|POS": [pts, games, seasons, first, last, partial]`). Offline builds have no career.json: chips are simply absent. BBP commits it with the weekly data; YILM rebuilds it every run.
- Name fit: shrink to 13px, else wrap to two lines at full size (never clipped). A long team name in the team column is zoomed down (`--dfz`, to 0.7).

## Gotchas learned the hard way

- `!important` font-size in CSS silently defeats JS fitting.
- Measure chips only after resetting transform; skip nothing in `fit` now (stat lines included).
- Measuring only visible rows changes widths between modes: measure all (`.sbm`).
- Canvas font metrics read before web fonts load are wrong: never cache across runs.
- Digit ink can rise above the H cap: size tiles on digit ink.
- Baselines estimated from canvas font metrics are off by up to ~0.9px at zoomed widths (1440 has `zoom` 1.1; layout rounds ascent/descent differently): measure with a zero-size inline-block on the baseline. `tilechk.py` now measures this way (it used to allow 0.6px, which hid it).
- A tile's stale `translateY` once made `fit` think it was off its line, so it was skipped forever (360: PF/PA tiles missing, 3.75px digits). Fixed by clearing transforms before the check.
- `new_tail.js` ends with `</script>`: append new JS before it.
- `const _cv` canvas already exists in new_tail.js: reuse, don't redeclare.
- YILM `live.js` is copied from BBP; `build_site.py` substitutes the YILM league id and season (was polling BBP's league before 2026-11-02).
- Sleeper draft slot owners: derive from `draft_order` when `slot_to_roster_id` is empty; keep only the latest completed draft per season.
- Playoff orange bars (Week 15): total of both wild-card games, averaged across seasons.

### Local sandbox setup (no network to Sleeper)

- **BBP Team Hub** (`teamhub/build.py`) calls Sleeper even in `build` mode; offline it fails with a 403 tunnel error. It is non-fatal by design: the main site still builds. Ignore it locally.
- **YILM first build:** `season_replay.py 2026 --build-only` fails (`.season/2026/pipeline/... not found`) until one full offline replay has run: `python3 season_replay.py 2026` (uses the committed capture, no network). After that, `--build-only` works.
- **YILM Playwright:** do not `npm i` in `pipeline/`. `package.json` pins Playwright 1.47.2, which wants browser build chromium-1134; the sandbox has chromium-1243 only, so `gen.js` fails with "Executable doesn't exist". Without a local `node_modules`, `gen.js` resolves the global Playwright (as BBP does). If one was installed, `rm -rf pipeline/node_modules .season/2026/pipeline/node_modules` and rebuild.

## Open items / ideas offered, not decided

- At 360 BBP, "Mandingoes" fits only at 16px (with FAAB below the name it is better than before; recheck).
- Page weight: 11.3 MB raw / 2.1 MB gzip (Matchups 4.7 MB, Playoffs and Compare 1.8 MB each). Lazy-loading tabs, Matchups first, was proposed.
- Converting the MFL seasons (2021-24) into full tracker pages like 2025 was offered.
- `anthropic-skills:dynasty-tracker-design` skill describes an older version; this file supersedes it.

## QA tools (tools/)

- `realfonts.py`: real fonts in Playwright (required).
- `tilechk.py`: every tile beside a figure spans exactly its cap height (real baseline via a zero-size marker, real CSS zoom, tolerance 0.05px, `TOL=` to loosen); stat-line tiles off their line count as violations; Dumb and Nerd; both trackers, any widths; exit code 1 on any violation. Against the pre-2026-11-02 fitter it fails 80-98% of tiles; the old version passed them all.
- `fab.py`: per-row name size/height/clip report + crops. `shot.py`: name-block-only screenshots at 402/440.
