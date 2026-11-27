# Findings (25-27 November 2026, one i9-14900HX + RTX 4080 Laptop GPU)

What we learned while getting the game to run well on this laptop. Our own measurements are in
[results.md](results.md); everything here is counts and descriptions, nothing from the game. Figures from other
projects are as each project reports them, on its own machine, and are marked so.

## In short

1. **Upstream VIctory is GPU-bound on this card; the fast forks are CPU-bound.** Upstream (with its open NVIDIA pull
   requests) spent about 1.7 s of GPU work per frame in the world, against 3-45 ms for the forks. The time is not
   in the number of draws: it sits in work that reaches the title's memory (see *Upstream on this laptop*).
2. **fxceless/victory-fork (on VIctory-NVIDIA) is the fastest tree here**: 48 ms a frame on the Series S profile
   without DLSS, 41 ms with DLSS Quality and frame generation. Its limit is the CPU's work per frame (30-43 ms of
   copies, texture checks and records), not the card.
3. **DLSS helps the CPU too**: at the lower scene scale there is less to copy (copies 24 → 12 ms a frame).
4. **The first session hitches** (140-420 ms) while pipelines are made at first use; the fork's
   `victory warm --used` after that session makes them ahead, and the next session is steady.
5. **Memory is the real limit of a 32 GB laptop**: the game takes 20-23.5 GB. The Series S profile fits with a few
   apps open; Series X needs browsers and launchers closed.
6. **`start /affinity` does not hold for this game** without a fix: the title places its threads itself and Windows
   11 lets that widen the process's mask (see [cpu-affinity.md](cpu-affinity.md); the fix is in `patches/`).

## Upstream on this laptop (runs 2-6)

Base: VIctory `63bcca4` with pull requests #2596, #2683, #2633 and #2885, the set that made every GPU and shader
test pass on this card (plain `63bcca4` fails two GPU tests and crashes the shader tests in the NVIDIA driver,
upstream #2317 / #2571). Series X profile, the intro of the game.

| Experiment | Result |
|---|---|
| Baseline | 1,829 ms a frame (0.5 fps): 171 ms of CPU preparation, about 1,680 ms of GPU work, 2,600 draws, 22 % dropped |
| GPU timing (diagnostics build) | the cost is in a few small compute dispatches, not in the many draws: clears and resets of lighting tiles, texture feedback and probe tables cost 18-245 ms each (about 500 ms a frame of clearing), then scattering passes and the deferred draws |
| Loop limit 4,096 instead of 2^20 (does a loop run away?) | no change (2,114 ms): runaway loops are not the cause |
| More dynamic descriptor slots on the capped heap (the card's heap holds 1,000,000 views, the title asks for 1.25 million) | draws dropped for want of slots: 265 → 0 a frame; speed unchanged (GPU-bound) |
| Host copies of title memory in video memory instead of system memory | one world sample: GPU work 1,683 → 232 ms, but the CPU's change checks then cross the bus (1.5 s copying back): unconfirmed, and upstream #3028 (RTX 5070 Ti) saw no change from the same move |

Working hypothesis, not proven: code that reaches title memory by address or through views (page tables, write
marks, view strides), added upstream after the forks branched, is what makes even tiny clear kernels slow on this
card. Upstream pull request #3312 (shadow buffers, page tables and dirty bitmaps in video memory on discrete GPUs)
is aimed at exactly this; it was open on 27 November.

## Forks on this laptop (runs 7-10)

- **ZJOU-VICTORY** (`66450431`, its last source revision before it became a packaged release): 316 ms a frame,
  about 5 fps once settled, GPU 45 ms. Its plain build prints "0.0 on the GPU" because its GPU meter only works in
  diagnostics builds, so a reported "GPU 0.0 ms" means not measured. Its README's 68.6 ms appears to come from a
  build of theirs with switches this revision does not have (its measuring script sets them).
- **fxceless/victory-fork** (`f299fba`, rebased on VIctory-NVIDIA on 27 November): 61 ms on its first session,
  48 ms once pipelines were made ahead, 41 ms with DLSS Quality + frame generation (one generated frame per
  rendered one, so about twice that is shown). Series X without DLSS: 83 ms early on, before memory ran short.
- In the fxfork runs the card was busy by its own count (nvidia-smi 100 %), yet the frame waited on the CPU:
  both are near their limit at these settings.

## How we measured, without anyone at the PC

- The layer's 5-second frame lines (`victory run` prints them); a line with 500 or more draws is the world.
  `tools/frame-summary.py` makes the tables.
- fxfork reads `VICTORY_KEYS=15:Enter,20:Enter,...` (Enter = A at those seconds, with or without focus), so a run
  passes the start screen by itself. A fresh data folder waits at the start screen; a copied save and settings
  profile go straight to the world after the presses.
- A watcher stopped each run after 50-60 world lines, or earlier when available memory fell under 700 MB, a
  hardware error came from a core in use, or the process's CPU mask changed. The title ignores a window close: the
  watcher ends it after 30 s.
- Five minutes, one run per setting. ZJOU-VICTORY measured 9.2 % between two identical runs on the same GPU:
  differences smaller than that are noise.

## NVIDIA-relevant projects (survey of 26-27 November)

Figures are each project's own claims, on its own hardware; we did not reproduce them except where stated.

| Project | Base | Reported | Their hardware | Notes |
|---|---|---|---|---|
| [fxceless/victory-fork](https://github.com/fxceless/victory-fork) | VIctory-NVIDIA, foxhound | 26-30 fps opening rooms, Series X 1440p, DLSS Quality | RTX 5070 12 GB desktop | **measured here: 41-48 ms Series S** |
| [VIctory-NVIDIA](https://github.com/trustno1-coder/VIctory-NVIDIA) | foxhound | 20-22 fps Series S, half scale | RTX 5070 12 GB | DLSS / FSR 3 frame generation, settings menu |
| [foxhound](https://github.com/readmet3xt-lab/foxhound) | many forks | (its README) | RTX 4070 SUPER | the base of the two above |
| [ZJOU-VICTORY](https://github.com/FQY55kai/ZJOU-VICTORY) | fxceless (older) | 14-15 fps Series S | **RTX 4080 Laptop 12 GB** | **measured here: 316 ms**; see above |
| [flamingo](https://github.com/realblastex/flamingo) | fxceless (older) | 9-14 fps Series S | RTX 4070 12 GB | ray miss / ambient stand-ins, faces, skinning work |
| [VItoriaBr](https://github.com/uiliannn/VItoriaBr) | upstream | 4-6 fps default, 22 experimental; GPU 50-65 ms | RTX 5060 Ti 16 GB | NVIDIA barrier and shared-memory fixes on the upstream base |
| [AnyXboxX](https://github.com/LooperSalty/AnyXboxX) | VIctory-derived | 12.5-13.8 fps | RTX 4070 SUPER | measured switch sets, RDNA2 reference tests |
| [victory-nvidia-8gb](https://github.com/soldsawn/victory-nvidia-8gb) | fxceless (older) | 8-10 fps at 1080p | RTX 4060 Laptop 8 GB | lower texture levels and resolution for 8 GB cards |
| [Leonida](https://github.com/ubiquitarianism/leonida) | its own layer | none in the world reported | - | compile gate and pipeline prewarm ideas; very active |

Safety: build from source and read scripts before running them. Several projects in this space ship packaged
archives or launchers, and fake "GTA VI for PC" downloads were reported spreading malware in November 2026. Nothing
here needs a download other than the source, Rust's toolchain and, for DLSS, NVIDIA's own GitHub release.

## Still open

- Why upstream is GPU-bound on this card (the hypothesis above): worth a measured pull request upstream.
- Series X with DLSS and frame generation, with other apps closed.
- The picture: not judged in these unattended runs.
