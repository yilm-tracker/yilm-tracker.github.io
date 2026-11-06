# DESIGN.md: BBP + YILM tracker design system

Single source of truth for how both trackers look and behave. Identical in both repos; site-specific items are labelled **BBP** or **YILM**.
**Builder:** read this before any UI change; update it in the same commit as the change (status tag + Decision log line).
**Translator chat:** reads this at the start of every session; never edits code.
Implementation notes (file names, fitting functions, data pipelines) stay in `CLAUDE.md`; where the two disagree about design, this file wins.

Status tags: `LIVE` = verified on the built page · `BRIEFED` = sent, not yet confirmed · `PENDING` = agreed, not yet sent.
When a brief is applied and verified, change its tag to `LIVE` and add a line to the Decision log.
Last reconciled against the built pages: 2026-11-04, after the data bar / opacity / rank pack changes (BBP `site/index.html`, YILM `.season/2026/site/index.html`, values read with real fonts at 402px).

---

## 1. Roles and workflow

- **Translator chat:** reads code and screenshots, measures real values, writes briefs. Never changes code.
- **Builder (Claude Code):** applies briefs to `billsblockparty/dynasty-tracker` (BBP) and `yilm-tracker/yilm-tracker.github.io` (YILM), verifies the BUILT page, updates this file.
- Every UI change goes to both trackers unless a section says otherwise. Only exceptions: MFL history (BBP), the Jaguars art/palette and rank-numeral art (BBP), logo ring + shadow (BBP; YILM has bare faces), draft-pick features (BBP; YILM is redraft).
- One brief at a time. To change course mid-task: "Stop. Discard X. Do this instead."
- Verify the built page, not the source (a build step once changed colours after the source).
- Reverts restore exact values from a named commit; never recreate by eye.
- **Brief-first step:** before any UI change, restate the request, name the exact elements, list ambiguous words and the choice made, give current values from the built page, then old → new, and flag risks. Small clear changes proceed; ambiguous changes, reverts or multi-page changes wait for approval.
- **Every UI brief ends with updating this file** in the same commit: status tag + one Decision log line. Both repos' copies stay identical.

## 2. Standing design rules

1. **Tokens only.** No new colour, shadow, radius or font size inline; a new value = a new token, and say so. `LIVE`
2. **Surface order:** frame (darkest) < page < panel < alternate row. Nothing nested is lighter than its container (except the alternate row's one step; text, chips and data excepted). `LIVE`
3. **One job per colour.** Tier colours = tiers; green/red = results only; YILM league red = #1 seed and the playoff line. Gold = top seeds (bye) only, never playoff text. **Alabaster is a surface colour (BBP FAAB tile), not a text colour; tier identity in text comes from position and labels, not colour.** `LIVE`
4. **Flat.** No gradients, glows, blurred shadows, top-edge highlights, accent rails/bars, edge fades, or cards inside cards. Depth only via hard offset shadow (no blur) in the frame colour: `--sh-hard` = `1px 3px 0 0 var(--frame)`. `LIVE`
5. **Dividers recede:** always darker than what they separate. `LIVE`
6. **Reuse** the nearest existing component before styling anything new.
7. **List every value** (colour, border, shadow, radius, spacing) before building.
8. **Contrast:** ≥ 4.5:1 small text, ≥ 3:1 large text and graphics (computed, not eyeballed).
9. **Report** what changed and any rule not followed.
10. **When unsure,** choose the plainer option and mention the alternative.
11. **Avoid AI-generated UI patterns;** prefer distinctive choices (e.g. a coloured bar along a card's top edge was rejected as generic).
12. **Shadow depth scales with the element:** ~5% of its height, whole pixels, min 1px. Dark elements on dark rows (value tiles) use 1px (`--sh-1` = `0 1px 0 0 var(--frame)`); light elements (FAAB tile, active pills) keep `--sh-hard`. Same direction and colour everywhere. Reference: standings logos and FAAB tile. `LIVE` for the rule, Drafts RPTS tiles and Drafts original-order logos; eight elements audited 2026-11-03 still break it (inactive nav / year / Wire buttons, Wire search, Players pill strip, Trades swap badge, BBP Playoffs bracket logos 28px, Compare logos 18px): not changed, decision pending (incl. whether panels and cards over 60px keep 3px).
13. Never highlight the Bill's Block Party team specially. `LIVE`
14. **Corners:** outer panels `--r-panel` (6px); inside a panel only chips/pills and avatars are rounded. `LIVE`
15. **Borders** only where they separate content, in the frame colour (chips and position pills keep their coded outlines). Enforced by the 2026-11-03 cleanup block at the end of both `readability.css` files (a `body *` border rule with chip exclusions). `LIVE`
16. **Minimum text 11 CSS px = 9.35pt on phones** (scale 0.85), every tab, both sites `LIVE` (2026-11-05). Labels and units 11px; a value keeps its step above its label (raise the value if the label would catch up: Rosters stat lines 13 / 11, The Wire header row 12.5px: Player, Matchup and the sort words over 11px sub-labels; Matchup's caps spacing .05em at 760-1099px to fit its 46px column). Every fitter's floor is 11px (`pfit`, `pcnFit`, `tnFit`, `ddFit`, Team Hub `.tro2`, Drafts list name and board banner, `--dfz`, Playoffs schedule/columns, BBP history pages); text that cannot fit at 11px is abbreviated (BBP Stats: "Rev. Apache Master" on phones) or the unit moves to the header (YILM Per start: "GP" once in each column header, numbers 11px; the header holds the same 20px tile group as the rows, so header GP and numbers align to 0px at every width), never shrunk. Uppercase letter-spaced labels may lose letter-spacing to fit ("PROJ": .1em → .06em). **Exception:** digits inside tiles beside figures follow the tile rule (cap height, ≥ 1.75px gap, equal on all sides) and are never scaled down: the Standings stat-line tiles (10.25px digits in 10.97px tiles beside 15px figures, cards and desktop table alike; the desktop table's figures are 15px from 1120px, and 1100-1119px keeps 13.5px figures with 8.75px digits because BBP's one-line team names need 196px and 15px would push the table up to 17.7px past the content edge) — and the stat lines themselves are never scaled below 1: Opp rk / All-play / Luck puts Luck on its own line where it does not fit (360P and 402P), PF / PA / Tot Eff wrap the per-week part under the figure (360P). Check: the under-11px scan is empty apart from that exception.

**Deliberate exceptions (do not undo):**
- Team rows use alternating shades AND a divider (see §3).
- **BBP** logo ring keeps its soft blurred shadow part (restored from the pre-cleanup commit; halved in Stats and Paper Trail).

## 3. Depth system (rows)

Four steps in one hue; only lightness changes. Reference: bdge.co standings. Applies to the standings cards, desktop table, Stats tables, Trades, Drafts lists and Paper Trail; cutoff lines unchanged. `LIVE`

| Step | Role | Reference contrast with step above | BBP live | YILM live |
|---|---|---|---|---|
| 1 | Lighter row (alternate) `--row-lt` | n/a | `#243F49` | `#2F4B66` |
| 2 | Darker row (panel) `--deck` | 1.29:1 | `#1A2C33` · 1.30:1 | `#203A55` · 1.29:1 |
| 3 | Divider between rows `--row-divider` | 1.16:1 | `#121F24` · 1.16:1 | `#172A3E` · 1.25:1 |
| 4 | Outer frame (darkest) `--frame` | 1.20:1 | `#04080A` · 1.19:1 | `#08111A` · 1.30:1 |

- Divider is full width, 1px (half the 2px frame), meets the side frames cleanly, never lighter than either row or as dark as the frame.
- Rows: no radius, border or shadow. Panels: 6px corners, 2px frame, `--sh-hard`.
- Panel vs page ≈ 1.3:1 (Sleeper reference 1.27:1). Live: **BBP** 1.30:1, **YILM** 1.46:1.
- First data row is the lighter one.

## 4. Colour tokens

| Token | BBP | YILM | Status |
|---|---|---|---|
| Outer frame `--frame` | `#04080A` (was `#070C0E`) | `#08111A` | `LIVE` |
| Page `--pg` | `#0C1215` (was `#101B1F`) | `#101D2B` | `LIVE` |
| Panel / darker row `--deck` | `#1A2C33` | `#203A55` | `LIVE` |
| Lighter row `--row-lt` | `#243F49` (was `#203841`) | `#2F4B66` (was `#2B445D`) | `LIVE` |
| `--row-divider` | `#121F24` | `#172A3E` | `LIVE` |
| Body text `--chalk` | `#ECE6DA` cream | `#FFFFFF` white | `LIVE` |
| `--text-dim` (labels, units) | `#A0A8B8` | `#AEBECC` | `LIVE` |
| `--steel` | `#ABA497` | `#A9B9CA` | `LIVE` |
| FAAB tile `--faab` / `--faab-ink` | `#D9D0BC` alabaster, `#101B1F` figures (11.4:1) | `#4F9FE8`, navy `#101D2B` figures (6.05:1) | `LIVE` |

- `--text-dim` and `--steel` meet 4.5:1 on the lighter row (lifted 2026-11-03). Coloured data on the lighter row (position QB pink, tier teal/red, result red) is still under 4.5:1: open item.
- **Tier text (2026-11-04)** `LIVE`: the playoff tier's text uses the normal text levels. All season sim labels (Finish, #1, Bye, Playoffs) are `--text-dim` on both sites (YILM has no Bye). Desktop table playoff % values: body text (cream / white), header unchanged (same as other headers). Stats › Points by position seed numbers 3-6: body text (**BBP** 1-2 stay gold, 7-12 `--text-dim`; **YILM** seed 1 league red, 2-6 white, 7-12 `--text-dim`, as on the standings). Contrast on the lighter row: `--text-dim` 4.67:1 BBP / 4.52:1 YILM; body text 8.98:1 / 9.06:1. Gold stays only where it marks a top seed (tiles 1-2, Bye line, seed numbers 1-2, the gold projected-finish value 1.0).
- Two text levels on the standings cards, **both sites** (BBP 2026-11-03, YILM 2026-11-04) `LIVE`: values `--chalk` (BBP cream, YILM white); labels/units `--text-dim` (OPP, ALL-PLAY, LUCK, PF, PA, TOT EFF, /wk, xW, COULD HAVE, Won/Lost, FAAB, DROPPED PTS, SEASON SIM, FINISH, #1, BYE, PLAYOFFS, the "no change" dash). `--text-dim` on the panel / lighter row: BBP 6.05:1 / 4.67:1, YILM 6.14:1 / 4.76:1 (`#AEBECC` since 2026-11-04; `#AAB9C7` gave 5.83:1 / 4.52:1, too close to the limit). Season chart labels unchanged. YILM manager nickname under the face stays `--label`.
- **BBP** kit palette (Standings Redesign Spec, 2026-11-03), at the end of BBP `readability.css`: tiers match the live rank pack (2026-11-05): `--tier-bye #E2CF93` (gold), `--tier-po #19B5C4` (teal; Playoff line label 7.59:1 on `--pg`, its 75% rule 4.71:1; was alabaster `#E4DDCD` 2026-11-04), `--tier-ch #2A2E33` (charcoal; was teal `#006778`; nothing visible uses it, checked 2026-11-05) (labels, sub-labels and rules at full colour); season chart `--chart-po-line #0097A7`, `--chart-po-fill #023442`, `--chart-po-val #19B5C4`, `--chart-nfl-bye #5A6870`; `--row-alt #203841` (FAAB pills). `--accent` (was `--pylon`) and `--sky` are NOT redefined (used across other tabs); standings/chart uses are overridden one by one. Unchanged by design: status colours (form dots, streaks, arrows, rank chips), the position colours (TE stays orange). `LIVE`
- **YILM** palette: logo blue `#4F9FE8`, logo red `#EC5F70`, league red `--accent #FB637A`.

**Token names: one name per role on both sites** (2026-11-04) `LIVE`. Every token below is defined on both sites under the same name and does the same job; values differ per site. No aliases.

| Role | Token | BBP | YILM |
|---|---|---|---|
| Page | `--pg` | `#0C1215` | `#101D2B` |
| Panel / darker row | `--deck` | `#1A2C33` | `#203A55` |
| Lighter row | `--row-lt` | `#243F49` | `#2F4B66` |
| Row divider | `--row-divider` | `#121F24` | `#172A3E` |
| Frame (plate, panel frames, hard shadows) | `--frame` | `#04080A` | `#08111A` |
| Hairline | `--line` | `#24444D` | `#30506F` |
| Stronger line, logo rings | `--line-strong` | `#2F5761` | `#3F6385` |
| Body text, values | `--chalk` | `#ECE6DA` | `#FFFFFF` |
| Secondary labels, table headers | `--label` | `#CFC6B6` | `#D3DFEB` |
| Muted figures | `--steel` | `#ABA497` | `#A9B9CA` |
| Dim text: labels, units | `--text-dim` | `#A0A8B8` | `#AEBECC` |
| Dark text on light tiles | `--ink` | `#0F1C20` | `#15263A` |
| Site accent | `--accent` | `#FF7A1A` orange (The Wire sort arrow, chart playoff weeks) | `#FB637A` league red (also seed 1 and, via `--tier-po`, the playoff line) |
| Second accent | `--sky` | `#7FA6FF` | `#259FD6` |
| Playoff tier | `--tier-po` | `#19B5C4` teal | `var(--accent)` |
| Results | `--win` / `--loss` (+ `-bg`) | | |
| Hard shadows | `--sh-hard`, `--sh-1` | | |
| Panel corners | `--r-panel` | 6px | 6px |
| Rank column width | `--rks` | 52px | 52px |
| FAAB tile / figures | `--faab` / `--faab-ink` | | |
| Projection cell fill (lineups) | `--proj-fill` | `rgba(255,255,255,.035)` | `rgba(255,255,255,.035)` |
| Playoffs schedule game cell fill (`.psg`) | `--sched-cell` | `rgba(255,255,255,.035)` | `rgba(255,255,255,.035)` |

- Site-specific by design: **BBP** `--tier-bye`, `--tier-ch`, `--chart-*`, `--rt` (rank tile height), `--ravh` / `--rd` (logo sizes), `--row-alt` (FAAB pills); **YILM** `--nt` / `--np` (layout counts).
- Removed 2026-11-04 (do not reintroduce): `--hair` (now `--line`), `--dim` (now `--text-dim`), `--plate` (now `--frame`), `--dsh` / `--dsh2` (now `--sh-hard`), `--pylon` (now `--accent`), and the unused `--bg`, `--surface`, `--fg`, `--muted`, `--faint`.

**Rejected; do not reintroduce:** **BBP** surfaces at hue 178° (too green; tried and reverted 2026-11-03); green-tinted frame `#060E0E`; Sleeper's navy for BBP (borrow its dark page and quiet labels, not its hue); FAAB alabaster `#ECE8DD` (read as white).

## 5. Navigation

**Groups and tabs** `LIVE` (group order GAME DAY, FRONT OFFICE, THE LAB since 2026-11-05)
- GAME DAY: Standings, Matchups, Playoffs
- FRONT OFFICE: Rosters, Players, The Wire, Drafts, Paper Trail (**YILM**: Drafts appears when the season's draft data is built)
- THE LAB: Stats, Leaderboards, Compare, Team Hub
- Default on load: Game Day › Standings; once Week 14 is done (weeks 15-17, current season only): Game Day › Playoffs.
- Switching group opens its first tab (Game Day opens Playoffs in weeks 15-17). No remembering last tab.
- Deep links always win over defaults (`#standings`, `#the-wire`, `#paper-trail`, `#paper-trail/pick/…`, `#paper-trail/player/…`).
- One-line fit rule for the level 2 row (applied only when a row would not fit): segment padding down to 6px, then the gap down to 5px (the toggle's gap is 2px, so this step does nothing), then padding to 4px. Letter-spacing is not reduced (the toggle has none). It engages only for the five Front Office tabs: padding 8 → 6px at 360, 10 → 9px at 402, 15 → 11px at 440; nowhere else.

**Three levels, three forms**
- Level 1, groups: big buttons, full width. `LIVE`
- **Level 2, tabs: the H2H/Median segmented toggle across the content width** (same left and right edges as the group buttons) `LIVE` (2026-11-05). Same track, active segment, text size, weight and height as `.pane-st .tg`, no new tokens: track = the toggle's background on each site (**BBP** `--deck`, **YILM** `--ink`), 1px `--frame` border, 10px radius, 3px padding, 2px gap, no shadow; segments 8px radius, IBM Plex Sans 600, no capitals, active `--chalk` fill with `--ink` text (14.0:1 BBP, 15.3:1 YILM), inactive `--steel` text, no fill; text size steps as the toggle: 15px; ≤430px 14px; ≤380px 13px (side padding 15 / 10 / 8px). **Track geometry** (polish 2026-11-05) `LIVE`: outer left and right edges = the group row's outer edges (box delta 0px at every width; the group buttons' 1px-right hard shadow is the only painted overhang); track height = group button height, never taller (`subFit()` sets the segment top/bottom padding `--tsv` from the measured group button; CSS fallback 6.78 / 7.35 / 7.22px); 4px inset (3px padding + 1px border) equal on all four sides of every segment; 8px from the group row at every width (was 6px below 1100px). No spacing token exists (spacing values are literal px, §7); 8px is literal. Selected segments are not aligned with the group buttons (3, 4 or 5 tabs under 3 groups). Measured (Chromium; WebKitGTK same to its whole-pixel rounding), group / track height: 360 37.39 / 37.38; 402, 440, 874, 956, 1100, 1440, 1920 38.80 / 38.78. **Width rule** (`subFit()`): equal segments when the widest label plus its padding fits an equal share; otherwise each segment's width follows its label and the row is still filled (extra space shared equally); never wraps, clips or ellipsises. Checked on both sites at 360, 402, 440, 874, 956 (landscape), 1100, 1440 and 1920: every group fills the row, one line, no sideways scroll, same row height in every group.
- Level 3, sections `PENDING` (e.g. 14 Stats sections), grouped under headings (Team / Moves / Results / Roster):
  - content ≥ 1100px: sticky sidebar list (~200px) left of the section panel;
  - content < 1100px: one section-picker button ("POSITIONS ▾") opening an inline grid (2 cols < 520px, 3 cols 520-1099px).
  - Switch by content width, not device; no scroll jump or lost selection when resizing.

## 6. Components

### Rank tiles and numerals (BBP) `LIVE`
- **Live pack: `scoreboard_rank_tiles_final.zip`, `square/`** (flip-scoreboard cards, lossless WebP 240×320 for 1-9, 280×320 for 10-12; `RNI_snippet.js` sha256 `524af2caec1cdc95…`): 1-2 white face `#FCFCFA` with gold frame `#CDA74B` (`1_bye_white`), 3-6 teal face `#006778` (`2_playoff_teal`), 7-12 charcoal face `#2A2E33` (`3_chasing_dark`). Each image carries a 4px transparent margin (the tile is 72 of 80px at 1x), so the CSS height is 49/44.1 of the visible tile. Served byte-for-byte from `ranknum/r1-12.webp` (identical to the snippet, and to the files live until 2026-11-04, `9f05cc4^`); the build inlines them from those files; never cropped, re-encoded, filtered or transformed. Replaced `rank_tiles_gold_alabaster_teal.zip` on 2026-11-05 (that pack had replaced this one on 2026-11-04).
- **1 and 11 are centred on their stems by design** (approved by Nicklaus 2026-11-05); exception to the visible-ink centring rule. Do not re-centre.
- CSS: `.rni{display:block;height:var(--rt);width:auto;max-width:none;margin:0}`; one rule, no per-tier size/filter/opacity. `--rt` **49px** (visible tile 44.1px; 10-12 are 42.9px wide, inside the 52px rank column `--rks`), **48px at ≤380px** (visible 43.2px: the logo is 44px there and the tile is never taller than the logo). Team Hub 49px. Desktop standings table **27px** (visible 24.3px; margin −3.5px so it takes the same 20px in the row as before). Tile centre level with the logo centre: ≤0.16px at 360/402/440 (3x), 0.24px at 1440 (2x); `rniSnap` snaps the art to device pixels, so a 1x screen shows up to 0.5px. `alt="N"` + `aria-label="Rank N"` per seed.
- Other packs offered (not live): `rank_numerals_keyline.zip` (free-standing; `--rt` 32px desktop / 44px mobile, 40px column); `rank_tiles_gold_alabaster_teal.zip` (live 2026-11-04 to 2026-11-05).
- Section label colours match the live pack's tiers: Bye line gold `--tier-bye`; Playoff line label and rule teal `--tier-po` (`#19B5C4`, 2026-11-05; was alabaster). Gold stays on the Bye line and Stats seeds 1-2 only.

### Rank numerals (YILM) `LIVE`
- Own fixed 52px column + 9px gap before the face; faces at the same x on every row.
- Seed 1 league red `#FB637A`; 2-6 white; 7-12 muted (`--text-dim #AEBECC`). Desktop table seeds unchanged.

### FAAB tile `LIVE`
- Light tile, dark figures, raised by `--sh-hard` (the shadow is its frame; no border). Values in §4.

### Avatars and logos `LIVE`
- Default: flat circle, no shadow.
- **BBP**: ring + shadow restored from the pre-cleanup commit: 1px `--line-strong` ring + 2px/2px hard and 6px soft shadow on standings; halved (1px, 3px soft) in Stats and Paper Trail. **YILM** faces: no ring, no disc, no shadow anywhere.
- Drafts › Original order: logos 40px (36px ≤ 380px), same treatment as standings scaled by size (40px = offsets 2, blur 5; 36px = offsets 1, blur 4).

### Data bars `LIVE`
- Every bar (Stats: luck `.dvb`, totals `.hbr`, odds `.obar`, stacked `.sbar` / `.ybar`, home/road `.hx-bar`; Team Hub: `.tqbar`, `.tqhb`, `.sbar`, `.ybar`; Matchups: win probability `.g4b`) is one framed track: 8px, fully rounded, `--frame` background, 1px `--line` border, 1px padding; fills inside, fully rounded and flat (no inset frames). Stacked bars keep their 2px gaps; the empty remainder is the track itself. One rule block at the end of both `readability.css` files (selectors carry `:not(#z)` to beat the `body *` border rule).
- Diverging: one track, 1px zero mark (`--label`) centred and drawn on top; fills grow left (red) / right (green) from it, square at the mark, rounded at the outer end, never past the padding. Empty values still show the track.

### Text levels
- Values full cream/white; labels and units `--text-dim`. Hierarchy from size/weight, never reduced opacity. `LIVE` on the standings cards, the season chart and the Drafts pick tiles; other reduced-opacity uses remain (§8).
- Season chart OPP row numbers: `--text-dim` (≥ 5.2:1 BBP, ≥ 4.9:1 YILM on their tiles), no opacity.
- Drafts pick tile position label (RB, WR…): full ink `#0B0E14`, no opacity; smaller size carries the hierarchy. `--text-dim` was not used there: on the pastel position colours it is 1.0-1.4:1.

### Cutoff lines `LIVE`
- No tier banners. Cutoff line under the last seed of a tier: dark strip (`--pg`), label in the tier colour, 2px rule in that colour, count at the right. **BBP**: bye line under 2 ("Top 2 bye"), playoff line under 6 ("Top 6 in"); **YILM**: playoff line only, league red. Same lines in the desktop table.

### Panels `LIVE`
- Panels (board, Stats/Leaderboards/Rosters/Matchups/Compare/Drafts/Paper Trail/Team Hub cards, desktop table) have a 2px frame in `--frame`, 6px corners and `--sh-hard`.

### List patterns (Stats, Team Hub and any list page) `BRIEFED`
All: one panel per section; rows edge to edge, alternating shades + `--row-divider`; 16px inset; 12px min from column edges; no nested cards; nothing past the panel edges.
- **A. Table rows:** one line per item; header row in `--text-dim` small caps; numbers right-aligned, tabular.
- **B. Item rows with header strip:** strip (`--row-divider` bg, ~28px) with context left + headline figure right; body below; status chips at the end. (Lineups, Trades, Consistency.)
- **C. Matchup + players rows:** week + team; "vs" + seed chip + opponent; players below as unbreakable units (pill + name) that wrap; never overlap. (Bye exposure, Two or more starters out.)
- Audit sent 2026-11-03 with four open questions (split multi-list sub-tabs into one panel each; Team Hub tiles to pattern A; keep matrices with a dim "Tap a cell" note; neutral margin chips). Only Trades (below) is applied.

### Matchups and Playoffs lineup `LIVE`
- Applies to the Matchups lineups and the Playoffs lineups (Matchup view and bracket game panels; 2026-11-05). The Playoffs schedule grid (`.psr`, its own Bench label) is a different component and keeps its rows.
- (2026-11-05) Player rows run flush: no frame, no hard shadow, no gap (was a 1px `--frame` border, `--sh-hard` and 5px between rows). The removed 1px border became 1px of padding, so row height (63.55px) and every element inside stay where they were.
- Slot groups from the league's own Sleeper `roster_positions` (BBP `pull8a.json`, YILM `league.json`): a 1px `--row-divider` only above the first row of a new group, none between players of the same group. **BBP**: QB | RB RB | WR WR | TE | FLEX | K | DEF (6 dividers). **YILM**: QB | RB RB | WR WR WR | TE | FLEX | SUPER_FLEX (shown SFLX) (5 dividers; the league starts no K/DEF). Same groups in the Optimal lineup; bench rows have none.
- Centre: projection cells have no side lines; their `--proj-fill` fill (§4) runs the full row height (figures unmoved, 1px inner padding). One 1px `--line` line, full row height, centred between the two projection columns: delta 0px at 360P/402P/440P/956L/1440, both sites. Final-score boxes keep their green/red side lines (results colour; "boxed = final" note), Nicklaus 2026-11-05.
- Bench: `--pg` strip as wide as the rows (cutoff-line geometry: 11px 16px padding, Barlow 700 11.5px, .2em caps), BENCH in `--text-dim` (7.9:1 BBP, 8.95:1 YILM), a 1px `--line` rule, note right-aligned in `--steel`, flush to the rows above and below.
- **Lineup fit, never "…"** (2026-11-06) `LIVE`: per lineup (one matchup view: both teams, starters + bench; Actual and Optimal fitted separately) one shared name size (largest that fits every name, ≤ 15.95px, floor 12px) and one shared game-line size (≤ 13.125px, floor 11px), set by `luFit()` as `--lnf` / `--lgf` on `.lus-a` / `.lus-o`. A name that does not fit at 12px: 11px on its own row → letter-spacing down to −0.02em → its injury tag, then its team logo, move to the end of the game line (kept only if the game line still fits) → a fixed approved abbreviation, the same at every width: Croskey-M., McCaff., Rodrig., Monang., Henders. Any other name that would need one stays at 11px / −0.02em and is reported with a proposed form (syllable break, ≥ 5 letters, not another surname) for approval. A game line that does not fit at 11px writes its time short ("9:30a", "Sat 8:20p", "1p"). Full player name in the name's `title` and `aria-label`; `text-overflow: clip`, and the check asserts no overflow. 2026-11-06 check, 276 states (every week, Actual/Optimal, Playoffs bracket + Matchup, 360P/402P/440P/874L/956L/1440, both sites): 0 overflow; shared names 15.75px at 440P/874L/1440, 12–15.75px at 360P/402P/956L; abbreviations in use: McCaff. (both sites, 360P/956L), Henders. (BBP, 360P/956L); St. Brown fits by letter-spacing, Croskey-Merritt and Rodriguez by moving the injury tag.
- **BN** (Optimal lineup, a bench player moved in): the third line of the position tile, under the rank (RB / 13 / BN), on every such row; never on the name or game line. Barlow Condensed 700 11px, .04em, cap-trimmed, the tile's own ink at full opacity; the three lines keep the tile's 3px gap and equal space above and below (≤ 0.02px off). Contrast on the position colours: QB 5.01, RB 7.53, WR 6.76, TE 6.81, K 5.59, DEF 4.73 (:1). In team-colour mode the tile ink is the team's: LAC 3.93 and KC 4.41 are under 4.5:1 (open item, shared by the existing tile lines).
- Bench strip width = row width in both tabs (desktop Matchups rows sit at 0, Playoffs rows at -10.5px; the strip follows). Checks 2026-11-05: centre delta 0, row gaps 0, content unmoved, bench edges 0 at 360P/402P/440P/956L/1440, both sites, both tabs.

### Trades `LIVE`
Pattern B plus: header strip (28px, `--row-divider`; date left, "WEEK n ON" right), centre swap badge (vs/@ tile style) with vertical divider, per-side "RECEIVED" rule, footer with totals (winner green + WON chip, other `--text-dim`). Team names in the side headers ellipsise (Nicklaus's choice: clean truncation here). **YILM** 3-team trades stack below 760px.

### Drafts round table `LIVE`
- Columns: pick tile | player name + NFL logo | NFL slot | RPTS tile | GM.
- NFL slot: stacked "RD 1 / PK 8" (overall pick), `--text-dim` Barlow 600 11px caps, header "NFL", 34px; "UDFA" or "–" when absent; all years incl. 2021 startup.
- RPTS tile: one width per round, `--row-divider` bg, cream tabular figures (Barlow 700 15px), 4px radius, `--sh-1`; "–" when no points; header "RPTS" (startup "PTS").
- Phones (< 760px): GM column is the logo/face only (44px). Desktop (≥ 1100px): draft board.

### The Wire `LIVE`
- Filters: ALL · QB · RB · WR · TE · FLX · K · DEF (**YILM**: no K/DEF). FLX = RB+WR+TE, cream label (not a position colour); active = cream pill. One line at 360px.

### Desktop standings table `LIVE`
- Equal gaps (≥ 16px) on both sides of the 20K SIMULATIONS divider, measured by visible glyphs; only TEAM gives up width.
- Every re-draw (resize, font load, sort, H2H/Median) lands on exactly the load layout: the rank chips are fitted before the column widths are pinned. Checked 2026-11-04 at 1100 and 1440, H2H and Median, both sites: every cell 0px apart, screenshots identical (after one matched repaint on both sides; the only residue without it is Chromium re-rasterising a repainted panel, 1 corner pixel at 1/255).

### Paper Trail `LIVE`
- Front Office tab after Drafts. **BBP**: Picks / Players switch; **YILM**: players only.
- Picks (**BBP**) `LIVE` (2026-11-06): year buttons (2 rows of 4 below 760px), one panel per round, header "R1 · TEAM · TRADED · VIA" (TRADED and VIA centred over their columns by glyph ink). Row = pick tile | holder (22px logo + name; drafted: player + NFL logo on line 2) | TRADED (RPTS tile `n×`: `--row-divider`, 4px, `--sh-1`, Barlow 700 15px tabular figure + 11px "×" in `--text-dim`; figure `--chalk`, 0 in `--steel`; height = the name's cap + 2 × 3px, width = the round's widest ink + 2 × 3px, one width and left edge per round; digits ink-centred, top = bottom, left = right; centred on the name's cap height) | VIA (original team's 22px logo with the halved shadow, "–" in IBM Plex Sans 600 15px `--text-dim` when never moved; 24px column so the ring's ink sits 16px from the panel edge); grid `52px · 1fr · TRADED (max of header ink and tile) · VIA (24px)`, 12px gaps, 16px right inset. Future rows are one line, 52px, content centred. Pick tile: pick number in the drafted player's position colour, or the projected pick on `--row-divider` for future picks (reverse current H2H seed of the original team, from the Standings board's own `H` order, same slots every round and year, Median ignored; weeks 15-17 final regular-season seeds; offseason (G=0): previous season's final seeds; ink-centred). Ordered by pick. NFL slot on line 2 (Drafts style, one line, right-aligned): Barlow 600 11px .04em caps `--text-dim`, "RD n" and "PK n" (overall pick) with a 6px gap, "UDFA" or "–" (no data); last glyph's ink on the name column's right edge, baseline on the player name, ≥ 12px from the NFL logo; fit: full size -> approved abbreviation (lineup list: "Croskey-M." at 360P) -> slot hidden (pick sheet keeps it), only below 423 CSS px. Holder names that do not fit use the §2.16 short form ("Rev. Apache Master", plain 360 only). Row title / aria-label carry the full names, trade count, via team and NFL slot. Pick sheet: "Projected 1.04 · " before the owner line; title stays "{original}'s pick".
- Players: search + the 50 most recently moved; row = moves tile (position colour) | name + NFL logo over the last move with the team logo | date | GM or "FA". The last-move team name shrinks to 11.5px, then shows the logo only (long names at 360-402).
- Sheet: full-height panel on phones, 460px side panel on desktop (2px frame on its left). Newest first; a `--pg` strip per season ("2024 · MyFantasyLeague" / "Sleeper"); rows = date (month over day) | team logo | action over detail (players and picks link to their own sheets). Back, Esc and the close button close it.

## 7. Spacing and testing

- **Phone scale 0.85** (2026-11-05) `LIVE`: every page sets `<meta viewport width=device-width, initial-scale=0.85>` (pinch-zoom kept; desktop browsers ignore it). On a phone the layout is points / 0.85: **test widths = device 360 / 402 / 440 portrait at scale 0.85** (`tools/device.py` tokens `360P 402P 440P` = 423 / 472 / 517 CSS px in Chromium; Safari may round to 424 / 473 / 518) and landscape `874L 956L` (1028 / 1124 CSS px: 874 = phone layout, 956 = the >=1100px desktop layout). Consequences: the `max-width:380px` rules no longer apply on any phone; `max-width:430px` applies at 360 only. Plain CSS widths (402, 440, 360) are still checked as before for the CSS steps. 1 CSS px = 0.85 pt on a phone: text under 11.76 CSS px renders under 10 pt (list kept, no change yet, §8).
- Widths: 402 (primary), 440, 360 (floor); desktop 1100 and 1440 (navigation also 760, 1099, 1920). Use available width; no dead space.
- 16px between content and any panel edge; 12px between text and any column divider; equal gaps both sides of a divider.
- Nothing clipped, wrapped or ellipsised at 360/390 (agreed exceptions: Trades side headers ellipsise; Paper Trail last-move team names fall back to the logo); no sideways scroll; rows breathe.
- Text optically centred in tiles; equal top/bottom and left/right spacing judged by glyph ink, not the text box; stacked tiles share width and left edge; logos centred on what they sit beside; a tile beside text is never taller than that text.
- Rank tiles beside a figure never poke above its cap top or below its baseline; digits never touch the frame. Check every time with `python3 tools/tilechk.py 402 440 360 1440`: 0 violations on both trackers (exact to 0.05px, Dumb and Nerd).
- Elements must not move between states (Dumb/Nerd, H2H/Median, re-fits on resize).
- Local QA always with real fonts (`tools/realfonts.py`); measurements without them are wrong.
- **Performance budget** (Nicklaus, 2026-11-04; memory definition 2026-11-05) `LIVE`: **under 20,000 elements on first load**, and in **Safari on a Mac, Activity Monitor, the tab's web content process: under 300 MB on a fresh load of Standings and under 300 MB after visiting every tab**, on both trackers. Chromium and WebKitGTK figures (`tools/mem/`) are diagnostics only: they locate causes and compare before/after, they do not decide the budget. Budget status `LIVE`, met (2026-11-05, BBP, Mac Safari, Activity Monitor, fresh process, single tab): **Standings fresh load 99.8 MB** (Safari's blank page 73.9 MB), **after visiting every tab 160.2 MB**; was 471-503 MB on load before `af0f361`. Visited tabs stay built (no drop-on-leave): not needed at 160 MB. How it is met: only the tab shown on load is in `index.html` (Standings, or Playoffs in Weeks 15-17, or the #hash tab, built before the page is revealed); every other tab is fetched the first time it is opened from a file named by its content hash. Matchups, Compare and Rosters are rebuilt on each visit and dropped ~1.5s after leaving (switches, selections and scroll come back); Matchups builds only the selected week; Playoffs builds only the selected bracket game / team panel. A tab that takes over 300ms shows its empty panel frame (no spinner); on failure the frame reads "Couldn't load. Tap to retry" in `--text-dim`. No visual change: every tab at 402 and 1440 pixel-identical to the one-file page. Check before shipping anything that adds markup: element count on load and Chromium memory after Standings and after every tab (local QA over http, not file://).
- **Diagnostic figures, WebKit (Safari's engine) and Chromium** (2026-11-04; Ubuntu WebKitGTK 2.52 and Chromium, private memory of the page's process, `tools/mem/`; Safari on macOS reports more, e.g. 471-503 MB on Standings in Activity Monitor). Measured before → after the fitter changes below; single runs, noise about ±2 MB at 402 and ±5 MB at 1440:

  | | Blank page | Standings on load | After every tab |
  |---|---|---|---|
  | **BBP** WebKit 402 / 1440 | 149 / 176 | 274 → 252 / 323 → 314 | 466 → 421 / 568 → 564 |
  | **YILM** WebKit 402 / 1440 | 148 / 171-176 | 268 → 245 / 327 → 308 | 456 → 438 / 569 → 557 |
  | **BBP** Chromium 402 / 1440 | 30 / 31 | 173 → 153 / 173 → 134 | 184 → 186 / 242 → 192 |
  | **YILM** Chromium 402 / 1440 | 31 / 31 | 170 → 156 / 166 → 140 | 197 → 209 / 201 → 198 |

  **2026-11-05, after the dropped-tab and matchup-builder fixes** (before → after, median of 3 Chromium runs with forced garbage collection and 2 WebKit runs; MB):

  | | Standings on load | After every tab |
  |---|---|---|
  | **BBP** WebKit 402 / 1440 | 255 → 250 / 317 → 313 | 429 → 374 / 539 → 501 |
  | **YILM** WebKit 402 / 1440 | 246 → 245 / 302 → 304 | 435 → 348 / 537 → 482 |
  | **BBP** Chromium 402 (after GC) | 73 → 73 | 164 → 122 |
  | **YILM** Chromium 402 (after GC) | 70 → 69 | 180 → 117 |

  After every tab, Chromium heap snapshot: JavaScript heap BBP 38.6 → 6.3 MB, YILM 55.3 → 6.1 MB; live DOM nodes BBP 130.8k → 107.6k, YILM 112.2k → 85.1k (Standings itself 4,250 / 5,000 elements). What remains is the tabs kept off-page by design (visited tabs stay built; only Matchups, Compare and Rosters are dropped). Without forced collection, the after-every-tab figure moves 10-18 MB between identical runs (the YILM 197 → 209 on 2026-11-04 was that; with collection the fitter change was −4.5 MB, ±1.5).
  Where the Standings cost sits in WebKit (bisect by removal, 402 / 1440, MB vs the full page): all CSS removed −52 / −62; CSS unused on load removed −12 / +6 (noise); `body *` / `:not(#z)` override rules removed 0 / +18 (noise); web fonts removed +38 / +60 (system fallback costs more); data URIs in script removed −10 / −10; reveal removed +6 / +8; header, year strip, nav band emptied within ±5; Standings board not drawn −78 / −107; fitters disabled −37 / −27, of which JavaScript heap −32 (garbage from repeated fitting passes, held until collection). Shipping each tab's CSS with its chunk would save about 10 MB, so it was not done.
- **Live data** (checked 2026-11-04) `LIVE`: only Matchups updates in place during games (the current week's lineups, scores, totals and game picker), and it polls whenever that week is on the page. Standings, projected finish, sim odds and headers change only through the site rebuild (every 10 min in game windows); the "New scores · Refresh" pill announces it. That pill's check is in `index.html` and runs on every tab, every 2 min. This was already true before on-demand tabs, so nothing outside Matchups lost live updates.

## 8. Features in progress and open items

- Team-colour tiles (Matchups / Playoffs "Colors: Team"): LAC 3.93:1 and KC 4.41:1 tile ink on the team colour, under 4.5:1 (2026-11-06).
- ~~Text under 10 pt at phone scale 0.85~~ closed 2026-11-05: minimum 11 CSS px (§2 rule 16); the only text under 11px is the tile-digit exception.
- **Paper Trail**: `LIVE` (Phases 1-4 built 2026-11-04). Data notes in `CLAUDE.md`.
- **Navigation three levels** (§5): `PENDING`.
- **List patterns** cleanup of Stats and Team Hub (§6): `BRIEFED`, four questions open.
- **Shadow cap** for panels/cards over 60px and the eight audited elements (§2.12): decision pending. Re-measured 2026-11-04 at 402: unchanged. Since the audit, Paper Trail's inactive Picks/Players switch (34px; rule 2px) and its search box (41px; rule 2px) also carry the full 3px.
- **BBP desktop table in Median mode overflows at 1100-1239px** (found 2026-11-04, predates the re-draw fix; not changed): the W-L cell's second line widens the table to 1068px at 1100 (1020px in H2H), so the page scrolls 8px sideways; 1175px at 1240. YILM fits (1027px at 1100).
- **Coloured data contrast** on the lighter row (§4): open.
- **Paper Trail drafted pick tiles** (found 2026-11-06, not changed: the brief kept them as they are): the pick number is centred by advance box, up to 0.53px off by glyph ink (the "1" bearings); future-pick tiles are ink-centred (≤ 0.02px).
- **Reduced opacity still used** (found 2026-11-04, not changed; decide per item): stacked-bar fills `.sbar i` 0.55; season chart OPP tile background 0.55 and playoff values `.wkc .wv.pov` 0.9; Rosters position labels `.cr .pq .pqi>span` 0.85/0.9; lineup-call figures `.dln2 em` 0.9; `.lu .cv .fs small` 0.75; out-of-contention stat values `.out .st .v` 0.85; bye tile `.stc.bye` 0.6; Drafts board cells (`.dfct i` 0.7, `.dfcn small` 0.78, `.dfcr` 0.82, `.dfcs>span` 0.75).

## 9. Decision log

Newest first. One line per decision: date · what · why.

- 2026-11-06 · Fix: Paper Trail NFL slot sat 10.24px below the player's baseline (its baseline marker was a flex item, so the fitter aligned the slot's top); slot is now an inline line, baseline delta 0.24px by an independent check (text box + font descent) · a check that reuses the fitter's own markers cannot catch this.
- 2026-11-06 · Paper Trail picks: trade count and original team move to aligned TRADED / VIA columns (RPTS tile, logo); future rows one line; NFL draft slot on drafted rows (full size -> approved abbreviation -> hidden below 423 CSS px) · left side shows only who picks; columns align row to row.
- 2026-11-06 · Paper Trail picks: rows name the owner ('via' original), future picks numbered and ordered by projected slot (reverse H2H standings; offseason keeps the previous season's final seeds), GM column dropped in Picks; "·" ink-centred, via-name-only fallback · the round was repeated on every row and the owner was hidden in a 44px logo.
- 2026-11-06 · Lineups never ellipsise: one shared name size (floor 12px) and game-line size (floor 11px) per lineup, then 11px, −0.02em, tags to the game line, fixed approved abbreviations (Croskey-M., McCaff., Rodrig., Monang., Henders.); BN moved into the position tile as its third line · names readable at 360P/956L without "…".
- 2026-11-06 · Text floor follow-ups: desktop table figures 15px from 1120px (tile digits 10.25px; 1100-1119px stays 13.5px, BBP team names would overflow by up to 17.7px), The Wire Player/Matchup headings 12.5px, YILM Per start GP header aligned to 0px · same tile size at every width; one header size per row.
- 2026-11-05 · Text floor: no text under 11 CSS px (9.35pt on phones) on either site; Standings stat lines never scale (Luck wraps at 360P/402P, +16px per row at 402P; PF/PA per-week wraps at 360P), tile digits beside figures exempt (10.25px); Rosters values 13px, Wire sort words 12.5px, YILM GP in the column header, BBP "Rev. Apache Master" on phones; all fitter floors 11px · legibility on phones (Nicklaus's floor).
- 2026-11-05 · Playoffs schedule cell fill is token `--sched-cell` (same value; schedule pixel-identical at 402P/1440, both sites) · one name per role.
- 2026-11-05 · Lineup treatment extended to Playoffs (flush rows, slot-group dividers, one centred centre line, bench strip; schedule grid excluded); projection fill is token `--proj-fill` (same value, Matchups pixel-identical); final-score boxes keep green/red lines · Matchups lineup approved; one component, one look.
- 2026-11-05 · Matchups lineup: rows flush (no frame/shadow/gap), 1px --row-divider only between Sleeper slot groups, one centred 1px --line centre line, projection side lines removed, bench as a --pg strip with --text-dim label and --line rule; content unmoved · §2.4 no card-in-panel.
- 2026-11-05 · Phone scale 0.85 via viewport meta (initial-scale=0.85, pinch-zoom kept), both sites; test widths = device 360/402/440 at 0.85 + 874L/956L; layouts equal the 85%-Safari-zoom renders Nicklaus used · same look without setting Safari zoom per site.
- 2026-11-05 · Nav level 2 polish: track edges = group row edges, track height = group button height (text size unchanged, 4px inset all sides), 8px gap under the groups at every width; no spacing token exists, value literal · one band, one height.
- 2026-11-05 · Navigation: groups ordered Game Day, Front Office, The Lab; level 2 tabs are the H2H/Median toggle across the content width (equal segments, else each follows its label), both sites · one component for switches; Front Office before The Lab.

- 2026-11-05 · BBP rank tiles -> scoreboard pack (white/teal/charcoal), --rt 49 to keep the 44px visible tile, Playoff line teal #19B5C4 · Nicklaus's choice.

- 2026-11-05 · Safari memory 471-503 -> 99.8 MB on load, 160.2 MB after every tab (fitter first-pass skip, batched tile sizing, Playoffs/live/HTML leak fixes) · under the 300 MB budget; visited tabs stay built.
- 2026-11-05 · Safari memory test pages removed (`/debug/mem/`, their generator and `robots.txt`) · figures reported.

- 2026-11-05 · Memory budget defined as Mac Safari, Activity Monitor, the tab's web content process: Standings fresh load < 300 MB and after every tab < 300 MB; Chromium and WebKitGTK figures are diagnostics only · one measurement that decides it.
- 2026-11-05 · Memory released after leaving tabs, no visual change: Playoffs matchup builder unpacks one team's block at a time (was every pairing x week, 36 MB BBP / 54 MB YILM held), live scores hold no Matchups elements between polls (a dropped week stayed alive, 23k nodes), no copy of a built tab's HTML kept; after every tab WebKit −55 / −88 MB at 402, JS heap 39 → 6 / 55 → 6 MB; builder output identical on 32 / 38 selections, 50 captures identical · leak check of 2026-11-05.
- 2026-11-05 · Temporary Safari memory test pages at `/debug/mem/` on BBP (§8) · the cost Safari shows is not reproducible off macOS.

- 2026-11-04 · Fitters made cheaper, no visual change: first pass skipped while web fonts load (the page is hidden and they re-run on fonts.ready), rank tiles sized in one batch (reads, then writes; layouts on load 1,864 → 941 at 402, 2,103 → 867 at 1440), stat-line scale set on the stat lines instead of the whole board, one font-metrics canvas; WebKit −9 to −24 MB on load, Chromium −14 to −39 MB; 50 captures identical · Safari measured 400+ MB on Standings; the WebKit bisect put the reproducible part in the fitters' JavaScript churn, not in CSS.

- 2026-11-04 · Desktop standings table re-draws fit the rank chips before pinning column widths; resize lands on the load layout exactly (0px, 1100/1440, H2H and Median, both sites) · a resize left the chips unfitted (13.5px instead of 8.75px), shifting columns by up to 2.4px.
- 2026-11-04 · Live polling left as built: nothing outside Matchups updates in place; Standings/sim/headers come from the rebuild and the site-wide refresh pill · confirmed against the pre-chunk live.js.

- 2026-11-04 · YILM `--text-dim` `#AAB9C7` → `#AEBECC`: 4.76:1 on the lighter row, 6.14:1 on the darker row (verified on the built page at 402/360), still clearly dimmer than white values (1.90:1 to white) · 4.52:1 was too close to the 4.5:1 limit.
- 2026-11-04 · On-demand tabs on both sites: tabs built from content-hashed chunk files when opened (Matchups by week, Playoffs by panel), Matchups/Compare/Rosters dropped after leaving with state restored, hidden tabs out of the document, one width-only resize dispatcher, live scores poll only while the current week is on the page; budget added to §7 · Safari used 3.5-4.3 GB on 434k elements; first view and every tab unchanged.
- 2026-11-04 · YILM labels and units step down to `--text-dim` like BBP's (same elements; 5.83:1 panel, 4.52:1 lighter row); values stay white · two text levels on both sites.
- 2026-11-04 · Token cleanup: `--hair`→`--line`, `--dim`→`--text-dim`, `--plate`→`--frame`, `--dsh`/`--dsh2`→`--sh-hard`, `--pylon`→`--accent` (both sites), unused `--bg`/`--surface`/`--fg`/`--muted`/`--faint` deleted; every tab pixel-identical before/after (one YILM screenshot off by 1/255 in 28 pixels) · one name per role, no aliases.
- 2026-11-04 · Season sim #1 and Bye labels take the sim label colour (BBP `--text-dim`, YILM `--label`) · gold marks top seeds only.
- 2026-11-04 · Token names aligned: `--text-dim` canonical on both (`--dim` alias), YILM `--tier-po` and `--rks` added; `--label` kept as its own lighter step, not aliased; no pixel change (YILM before/after identical) · one name per role, so briefs mean the same thing on both.
- 2026-11-04 · Alabaster is a surface colour, not a text colour: playoff-tier text uses the normal text levels (sim Playoffs label, desktop playoff %, Stats seeds 3-6; YILM seed 2-6 and Playoffs label likewise); Playoff line label stays alabaster · tier identity comes from position and labels; gold means top seeds only.
- 2026-11-04 · BBP rank tiles switched to gold/alabaster/teal (no buffer, rounded); tier tokens follow (playoff alabaster, chasing teal) · Nicklaus's choice of pack.
- 2026-11-04 · Season chart OPP numbers `--text-dim`, Drafts tile position label full ink, no opacity · hierarchy without opacity; `--text-dim` fails on the pastel tiles.
- 2026-11-04 · Every data bar is one framed track (8px, round, frame bg, 1px line border, 1px padding; 1px zero mark) · one bar component on both sites.
- 2026-11-04 · Kept live frame (BBP `#04080A`, YILM `#08111A`) and BBP text `#ECE6DA` · Nicklaus confirmed the live values.
- 2026-11-04 · DESIGN.md reconciled with the built pages and added to both repos; design rules moved here from CLAUDE.md · one source of truth.
- 2026-11-04 · Paper Trail tab (pick chains BBP, player histories both) · trace every pick and player move since 2021.
- 2026-11-04 · Sub-tab row may tighten its gap to 5px and padding to 4px · five Front Office pills on one line at 360.
- 2026-11-03 · Drafts NFL slot column; GM column logo-only below 760px · NFL draft context without losing the player name's room.
- 2026-11-03 · Shadow depth scales with the element (RPTS tiles 1px, original-order logos scaled) · depth proportional to size.
- 2026-11-03 · The Wire FLX filter · RB/WR/TE in one list.
- 2026-11-03 · Drafts RPTS tile, original-order logos 40px · readable rookie points.
- 2026-11-03 · Stats › Trades as pattern B rows · clear zones per trade.
- 2026-11-03 · BBP page `#0C1215`, frame `#04080A`, labels `--text-dim #A0A8B8` · darker page for long viewing; frame stays darker than the page.
- 2026-11-03 · YILM rank column, rank colours, FAAB tile `#4F9FE8` · align with BBP geometry and the league logo.
- 2026-11-03 · YILM has no byes: playoff line only · follow the league's own site.
- 2026-11-03 · Navigation regrouped into Game Day / The Lab / Front Office.
- 2026-11-03 · Four-step depth system with shading AND dividers adopted for rows.
- 2026-11-03 · BBP green-teal (178°) surfaces rejected and reverted; frame and page darkened instead.
- 2026-11-03 · Flat design rules adopted; decorative highlights, accent rails, nested cards and blurred shadows removed.

## 10. Lessons learned

- Build steps can change colours after source; verify the built page.
- "Revert" needs a named commit.
- Ambiguous words ("frame", "blue", "background") cause most misfires; name the element.
- Small hue shifts (178° vs 196°) read as a different colour family on a phone, even at matched lightness.
- Overlapping briefs sent mid-task get merged; send one at a time.
- `!important` on a font size defeats the JS fitters; canvas font metrics before web fonts load are wrong.
