# Optimisation gap analysis (first pass, 27 November 2026)

Task brief: a local task brief (VIBELLIC_CLAUDE_CODE_OPTIMISATION_PROMPT.md, not published). Evidence classes used below:
**SRC** = source inspected at the pinned revision; **MNT** = maintainer-reported measurement; **LOC** = local
measurement on this laptop (one run unless stated); **HYP** = unverified hypothesis.

## 0. Checkpoint (resolved roots and revisions)

| | Path | Branch | Full commit | Dirty |
|---|---|---|---|---|
| Kit | `<kit checkout>` | `laptop-kit` (= origin) | `74ca1160877f0a2f353311218975ddf7042e4e0d` | only this file and the tool changes of this pass |
| Runtime | `<runtime checkout>` | `fx-testing` | `2665637e87cc6a18ee920f3cdc2220e926d7cbe6` | clean at start |
| Runtime base | fxceless/victory-fork | `main` (unchanged since) | `f299fba1a02b68dba12b2f8d995dacaeb55081ef` | |
| Affinity patches | on fx-testing as `30f6041` / `2665637` (from `5d16d51e3b09ddd7c2a0521729121b8cb575db6a`, `75eede2f2499fab90db9a06025a1a954d853e8dd`) | | | |

Playable build: `<workspace>\build\fx\victory.exe` = byte-identical to the runtime's
`target\release\victory.exe` (built 2026-11-27 18:50). Config `<workspace>\victory-fx.toml` (through
`VICTORY_CONFIG`); no `victory.toml` and **no `victory-settings.txt`** in the runtime, so no saved-menu overrides.
Launch path used by every measured run: `tools\fx-env.cmd` (+ `fx-run.cmd`, `fx-run-dlss.cmd`, `play-fx.cmd`), **not**
the fork's `scripts\play-foxhound.ps1` / `victory play`: that launcher's extra behaviour (`-Fps` → lifted interval,
FG prepared while off, menu file) did not apply to runs 8-12.

Inputs read: the brief and `VIBELLIC_COMPARISON_2026-11-27.md` (complete); `VIBELLIC_FINDINGS_2026-11-27.md`
(complete); `gemini-code-1795815592120.md` (complete); `VIBELLIC_RESEARCH_MERGED.md` (complete, earlier this
session); `VIBellic_OSINT_Update_2026-11-27.md` (the file without "(1)"): TL;DR, evidence policy, both leaderboard
tables, cards 3.18-3.23 (Vice-Tay, Vilocity, foxhound, VIctory-NVIDIA, -RT, sm86), next checks and coverage log read;
the other cards (older and AMD/Linux leads) and the query/source registers were scanned by heading only.
Files live in `VIBellic\docs\`, not `docs\research\`.

Hardware confirmed locally: i9-14900HX (32 logical processors; **30 eligible** under `FFFFFCFF`), RTX 4080 Laptop
12 GB (driver 621.40; DXGI local budget 11,227 MB at swap-chain creation, run 12), 32 GB DDR5-5600 (2 x 16 GB),
Windows 11 26300, on AC, plan Balanced, Resizable BAR on, HAGS on (Streamline: frame generation supported).

## 1. Effective settings inventory (runs 8-12; readers at `2665637`)

All read once (`OnceLock`/startup) unless noted: none is a live A/B toggle in a release build.

| Switch | Reader (SRC) | Default if unset | Our runs | Notes |
|---|---|---|---|---|
| `VICTORY_THIN`, `JOIN_PARTS=8`, `RELAY=2`, `RELAY_COPY`, `WIDE_BACK`, `CARD_REHASH_RUNS`, `JOIN_COPIES`, `CARD_STEPS=2`, `CARD_AWAKE`, `CARD_BUFFERS_MIN_KB=64`, `INDIRECT_WINDOW`, `INDIRECT_BATCH=2`, `UPLOAD_AHEAD`, `SHOW_AFTER`, `MAP_THREADS` | list/thin.rs, host.rs, shadow.rs, host/card_steps.rs, host/awake.rs, draw.rs, texture/ahead.rs, descriptor/host.rs, xmem.rs | off / fork defaults | **set** (fork launcher block) | thin lists, joined copies, card steps, upload-ahead are already present and enabled: not to be "added" |
| texture block (`TEXTURE_POOL`, `RIPE_BLOCKS=0`, `TEXTURE_NO_WAIT`, `TEXTURE_CATCHUP=0`, `TEXTURE_STAGE_MS=16`, `LEVELS_ON_DEMAND=0`, ...) | pool.rs, texture.rs, draw.rs, tiles.rs, descriptor/host.rs | fork defaults | set | |
| heap-record block (`HEAP_SYNC_FIRST`, `SYNC_IN_PLACE`, `SPANS_QUICK`, `SYNC_FINE`, `HEAP_SYNC_AT_SUBMIT`) | host.rs, descriptor.rs, descriptor/host.rs, heap_marks.rs | off | set | |
| `VICTORY_QUICK_FIND` | shadow.rs `quick_find()` via `toggled!` | **on** (`=0` off; A/B bit only in diagnostics builds) | default (on) | per-thread `FOUND` cache, 1,024 slots, exact (address, len) key, invalidated by `BUFFERS_CHANGED` |
| `VICTORY_BVH_BUILDER` | pipeline.rs `builder_runs()`, pipeline/make.rs | **off** (only `=1` runs it) | unset → **RT off** | with it off, RT-resolve shaders are skipped (unless `VICTORY_RT_RESOLVE=1`) and screen-probe ray activation is skipped (unless `VICTORY_ACTIVATE_RAYS`) |
| `VICTORY_WATER_LIGHT` | pipeline/make.rs | off: two water-light programs **left out on 32-lane hosts** | unset → left out | omitted work |
| `VICTORY_LEAVE_OUT` | pipeline/make.rs | none | **two programs left out** (decal-heap defragmentation, heat-haze pass; the fork launcher's list, identifiers not reproduced here) | omitted work |
| `VICTORY_AMBIENT=0.8`, `_AIR=1.5`, `_SPECULAR=1`, `EARLY_DEPTH=1` | ambient.rs, emit/mod.rs | off | set | lighting stand-ins (RT is off) |
| `VICTORY_FRAME_INTERVAL_MS` | gpu frame.rs `asked()` **and** loader frame_rate.rs (patches the title's own rate at load) | unset → title's 33,333 us | unset → **30 fps cap** | takes precedence over `_US` |
| `VICTORY_FRAME_INTERVAL_US` | gpu frame.rs `interval_override()` | unset | unset | our clock only (1,000-1,000,000 us); the fork launcher sets it from `-Fps` (default 1000 = uncapped) |
| `VICTORY_DLSS`, `_DLSS_MODE`, `VICTORY_FRAMEGEN`, `_FRAMEGEN_X`, `VICTORY_STREAMLINE_DIR`, `VICTORY_TEXTURE_ROOM_PERCENT=80` | streamline.rs, resource.rs | off | runs 10-12 on; runs 8-9b off (FG **not** prepared) | Streamline loaded with OTA off; DLSS scene scale 0.667 |
| `VICTORY_KEYS` | gameinput.rs (release builds here) | none | runs 8-11 (Enter presses) | |
| `VICTORY_HEAP_WORKER` (research §3.2.4) | **not found** in this tree | - | - | absent under that name; equivalents not established |

Console profile: `--console` (default **Series X**). `fx-run.cmd`/`fx-run-dlss.cmd` pass their arguments through, so
**a run started without arguments is Series X** (run 11, by mistake); `play-fx.cmd` defaults to Series S.

## 2. Existing-feature matrix vs. the research

| Technique | Upstream inspected | Local | State | Bottleneck addressed | NVIDIA | Licence | Risk | Test |
|---|---|---|---|---|---|---|---|---|
| Thin lists / joined copies / card steps / upload-ahead | fork launcher block (SRC) | same readers at `2665637` | **present, enabled** | CPU submission | yes | GPL-3.0-or-later | - | none needed |
| Thread-local lookup cache | VIctory-Fast `e0e549a2` shadow.rs `FOUND` (8,192) + `SpanCache` (32 MRU ranges) + `SHADOW_EPOCH` | shadow.rs `FOUND` (1,024), `BUFFERS_CHANGED` | **present, smaller**; range cache **absent** | buffer lookups on recording threads (the local source comment: 7 % of their time before `FOUND`) | yes | GPL-3.0 (repo LICENSE; file header not separately checked) | slot count: low; range cache: medium (lifetime/Weak handling, loose windows) | slot count: unit tests + release A/B |
| Ranged seqlock / GPU-only copyback | VIctory-Fast `e0e549a2` shadow.rs | absent | absent | copy-back | ? | GPL-3.0 | **high** (CPU reads, aliases) | out of this pass |
| Frame-interval lift | fork frame.rs + loader frame_rate.rs (SRC) | present | present, unused (30 cap) | rendered fps above 30 only | yes | GPL-3.0-or-later | game speed must be checked | needs a person watching |
| DLSS SR / 2x FG | streamline.rs (SRC) | present | on in runs 10-12 | GPU (SR), presentation (FG) | yes (RTX 40: 2x) | vendor DLLs local only | Series X: out of VRAM | LOC run 11 |
| Pipeline book + `warm --used` | fork (SRC) | present | used after runs 8 and 12 | first-use hitches, dropped draws | yes | GPL-3.0-or-later | - | LOC runs 8→9b |
| Worker pools sized by `available_parallelism()` | land.rs, shadow.rs, pipeline/make.rs, dstorage.rs, translate.rs, warm.rs (SRC) | present | **sizes for 32** although 30 are eligible (LOC probe: `available_parallelism()` = 32 under FFFFFCFF) | oversubscription under the mask | yes | ours | low | candidate 3 |
| Heap worker thread | research only | not found | absent/unknown | texture uploads | ? | - | - | not pursued |
| Native DXR, RDNA wave32 presets, MFG unlockers, other upscalers | research | - | out of scope this pass | | | | | |

Already satisfied or superseded: "switch to ZJOU" (run 7: 316 ms vs fxfork 48 ms); "add thin lists / joined
copies / upload-ahead / card buffers" (all present and on); "GPU 0.0 ms means idle" (ZJOU's meter is
diagnostics-only); "the faulty core may be used for a control" (never).

## 3. Local evidence (LOC), with conditions

All Series S unless stated, title cap 30 fps, RT off, water-light and the two LEAVE_OUT programs omitted, release
build `2665637`, opening of the game unless stated, 5-second reporting windows (not per-frame data).

| Run | Upscaler / FG | Scene, length | Window median | Mean of windows | Dropped | Notes |
|---|---|---|---|---|---|---|
| 8 | title's / off (not prepared) | opening, ~5 min, unattended | 60.9 ms | 15.1 fps | 14.9 % | cold pipelines |
| 9b | title's / off | opening, ~5 min | 48.1 ms | 19.4 fps | 14.8 % | warmed |
| 10 | DLSS Q / 2x on | opening, ~5 min | 41.4 ms | 22.8 fps | 15.2 % | FG generated frames throughout |
| 11 | DLSS Q / 2x on, **Series X** | opening, ~5 min, scripted keys | 95.8 ms | 10.7 fps | 9.6 % | 2,695 DLSS "out of VRAM"; card 11,926 MB of a 10,791 MB budget; FG produced 86 frames |
| 12 | DLSS Q / 2x on | **hand-played ~10 min** | 40.6 ms | 22.0 fps | **28.9 %** | first moving gameplay; up to 1,027 pipelines queued: first-use drops and 125-442 ms spikes; 351 pipelines warmed afterwards |

Presented fps: **unknown** (the FG status lines count presents and generated frames per interval, but not a
presented-frame rate the tool can validate). Per-frame lows/p95/p99: **not available** (no per-frame timing exists
in release builds: only the 5-second report line and the F3 panel).

## 4. Candidates (at most three), ranked

1. **Measurement / configuration ambiguity (do first, no runtime change).** fx-run scripts default to Series X
   when given no arguments (cause of run 11); summaries treat GPU 0.0 as a number; FG readiness is not recorded.
   Fix in tools; record effective settings per run.
2. **`FOUND` slot count as a switch** (`VICTORY_FOUND_SLOTS`, default = today's 1,024, so off by default). Minimal,
   GPL-3.0 provenance (VIctory-Fast `e0e549a2` uses 8,192), invalidation unchanged. Bottleneck relevance is HYP:
   preparing is 30-43 ms a frame and lookups are part of it, but no release counter measures the hit rate.
   Requires an A/A noise band first; a win must exceed it.
3. **Worker pools sized from the effective mask** (popcount of `GetProcessAffinityMask`) instead of 32. Small,
   safety-aligned; benefit HYP (2 of 32 threads oversubscribed).

Rejected for this pass: span-cache port (depends on epoch plumbing and loose-window lifetime rules: too large to
validate here), GPU-only copyback (high risk), frame-interval lift (needs game-speed verification by a person),
Series X with FG (does not fit 12 GB: run 11), any new skip list.

## 5. What was done and measured (27 November, 22:00-22:41)

Tools (kit, uncommitted): `tools/frame-summary.py` (share-safe output: label instead of path, malformed lines
counted never shown, `--json`, time-weighted throughput, GPU N/A when the meter is all zero, FG counts with
presented fps unknown, cap-window count; old invocation unchanged) and `tools/test_frame_summary.py` (13 synthetic
tests, stdlib only: `python -I -B -m unittest discover -s tools -p "test_*.py"`: **13 passed**). On real logs it
reproduces the earlier medians exactly (runs 9b, 10, 12: 48.1, 41.4, 40.6 ms).

Local runner fixes (outside the kit, `<workspace>\tools`): `fx-run.cmd` defaults to Series S when
given no arguments (run 11 was Series X by accident), takes `VIBELLIC_EXE`, writes the build's SHA-256 into the
log; `fx-run-dlssq.cmd` = the brief's baseline (DLSS Quality, FG off and not prepared, RT off, 30 cap) and refuses
to run without the NVIDIA files; `ab-sequence.ps1` = interleaved A/B with preflight (no other victory.exe, >= 24 GB
available, WHEA unchanged), a lock file, and a stop on any safety stop of the watcher (`watch-run.ps1`: affinity,
WHEA by APIC, memory). Every CPU-heavy process this pass was started under FFFFFCFF and sampled at FFFFFCFF.

Runtime candidate 2 (uncommitted in the runtime worktree; `patches/0003-experimental-found-slots.patch`):
`VICTORY_FOUND_SLOTS`. Checks: `cargo test -p victory-gpu --lib shadow::` 38 passed / 1 ignored (4 new);
`cargo test -p victory-hle --lib modules::kernel` 7 passed (both affinity tests); release build OK (into
`<workspace>\build\fx-found`, SHA-256 B246B26E...; the playable build is untouched); patch applies to
and reverts from a clean `2665637` file (content identical after revert).

A/B (same build, separate launches, interleaved A1 B1 A2 B2; Series S, DLSS Quality, FG off, RT off, water light
and two LEAVE_OUT programs omitted, title cap 30, warmed shader cache and pipelines, opening of the game,
unattended with scripted Enter presses, 60 world windows each, release build). Statistics are of 5-second windows:

| Run | FOUND slots | Median ms | p10-p90 ms | Throughput fps | Preparing ms | Draws | Dropped |
|---|---|---|---|---|---|---|---|
| A1 | 1,024 | 40.5 | 34.7-99.6 | 22.10 | 31.5 | 3,790 | 16.4 % |
| B1 | 8,192 | 49.5 | 38.5-112.6 | 19.23 | 36.8 | 4,713 | 11.4 % |
| A2 | 1,024 | 44.4 | 35.1-118.5 | 20.33 | 35.9 | 3,748 | 24.2 % |
| B2 | 8,192 | 43.0 | 41.3-71.0 | 20.88 | 36.6 | 4,155 | 13.6 % |

- **INVALID AS A COMPARISON (found afterwards):** the user was playing during these four runs, not knowing they
  were measurements. Their input, on top of the scripted presses, explains the different scenes (draws 3,750-4,710)
  and spreads. So the 9.8 % / 8.0 % differences between A1 and A2 are **not** an A/A noise band, and nothing can be
  concluded about `VICTORY_FOUND_SLOTS` from them. The runs stay listed for the record. Repeat hands-off.
- What still holds: with these settings the layer rendered 19-22 fps throughput (40-50 ms median windows) at
  Series S in the opening, much as run 10 with FG on (41.4 ms). The switch stays off until a valid A/B.
- WHEA ID 19 stayed at 45 through all runs; no display-driver resets; available memory >= 25.8 GB before each run.
- Summaries (no game data): `<workspace>\results\ab-A1.json` ... `ab-B2.json`,
  `ab-found-slots-2026-11-27.csv`.

One rule broken during the inventory, recorded: a one-line probe of `available_parallelism()` was run once under
mask `0000FFFF`, which includes the excluded LP 8/9 (milliseconds; no WHEA event followed). Every other process
was masked FFFFFCFF.

## 6. Handoff

- Not tested: a moving-gameplay route (only the opening, unattended; plus run 12 hand-played); per-frame lows
  (the runtime has no per-frame times); presented fps; the 60 fps interval path (needs a person to judge game
  speed); a 20-minute stability run; the picture.
- Stable settings: as runs 9b/10/12 (`tools\play-fx.cmd`, Series S, DLSS Quality, FG 2x optional). Experimental:
  `VICTORY_FOUND_SLOTS` (not yet measured validly: the first A/B had a player at the keyboard). Do not use
  Series X with DLSS + FG on 12 GB (run 11: out of VRAM).
- Rejected: span-cache port, GPU-only copyback, frame-interval lift, Series X + FG, new skip lists.
- Next experiment (one): candidate 3, worker pools sized from the effective mask, measured the same way; a fixed,
  repeatable route first (`VICTORY_KEYS_FILE` exists in the runtime), since scene variation (draws +/-25 %) is
  larger than the effects being looked for.

Commands (Windows PowerShell):

```powershell
# tests of the kit's tool
Set-Location '<kit checkout>'; python -I -B -m unittest discover -s tools -p "test_*.py"
# candidate tests + build (masked, detached)
cmd /c 'start "VIBellic candidate" /min /affinity FFFFFCFF cmd /c <workspace>\tools\fx-candidate-build.cmd'
# the A/B sequence (detached; status in logs\ab-sequence.status)
Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','RemoteSigned','-File','<workspace>\tools\ab-sequence.ps1'
# summarise a run (counts only)
python -I '<kit checkout>\tools\frame-summary.py' --json '<workspace>\logs\run-fx-20261127-221215.log'
# remove the experiment from the runtime worktree
Set-Location '<runtime checkout>'; git apply -R '<kit checkout>\patches\0003-experimental-found-slots.patch'
```
