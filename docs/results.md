# Results: i9-14900HX + RTX 4080 Laptop GPU (12 GB) + 32 GB

Measured on 27 November 2026 (run 2 on 26 November) on one laptop. Counts only: nothing from the game.

| | |
|---|---|
| Laptop | Acer Predator Helios 16 (PH16-72), on mains power, Windows power plan Balanced |
| CPU | Intel Core i9-14900HX (8 P-cores + 16 E-cores, 32 threads) |
| GPU | NVIDIA GeForce RTX 4080 Laptop GPU, 12 GB, driver 621.40, Resizable BAR on, hardware GPU scheduling on |
| Memory | 32 GB DDR5-5600 |
| System | Windows 11 (build 26300) |
| Game | the Xbox Series build v1.0.2.1, your own copy |

## How it was measured

- The numbers are the layer's own: every 5 seconds `victory run` prints the frame rate, the milliseconds of a
  frame and the draws in it. A line with 500 or more draws is the world; menus and loading screens have far fewer.
  `tools/frame-summary.py` turns a log into the figures below.
- Each run went from the start screen into the opening of the game (the first minutes in the world) and was ended
  automatically after 50-60 world lines (about five minutes), by a watcher that also guarded free memory. The
  start screen was passed without anyone at the keyboard: the fork reads `VICTORY_KEYS=15:Enter,20:Enter,...`
  (key presses at those seconds; Enter is A).
- The title paces itself at 30 frames a second (33.3 ms), so 33 ms is the best a frame shows here unless the fork
  launcher's `-Fps` lifts the cap.
- One run per row: a run of the same settings can differ by about 10 % (ZJOU-VICTORY measured 9.2 % between two
  identical runs). Treat small differences as noise.
- The picture was not checked in these runs (nobody watched them).

## The runs

| Run | Build | Settings | Profile | World ms/frame, median (p10-p90) | fps, mean | Notes |
|---|---|---|---|---|---|---|
| 10 | fxceless/victory-fork `f299fba` + `patches/` | fork launcher's settings, **DLSS Quality + frame generation 2x** | Series S | **41.4** (36.5-59.1) | 22.8 rendered | last minute 34-39 ms (26-29 fps rendered); one generated frame per rendered one, so about twice that is shown |
| 9b | same | fork launcher's settings, no DLSS, pipelines made ahead (`victory warm --used`) | Series S | **48.1** (46.9-66.7) | 19.4 | steady 46-50 ms; a busy scene (about 4,100 draws a frame) |
| 8 | same | same, first run | Series S | 60.9 (35.0-283) | 15.1 | pipelines made at first use: 140-420 ms hitches |
| 9a | same | same | Series X | 83.3 (63.3-352), 15 lines | 10.1 | stopped early for memory: the game took 23.5 GB with other apps open |
| 7 | ZJOU-VICTORY `66450431` + `patches/` | its own measured set | Series S | 316 (117-1,381) | 3.9 | its diagnostics build |
| 2 | VIctory `63bcca4` + upstream PRs #2596, #2683, #2633, #2885 | defaults | Series X | 1,829 (1,309-2,736) | 0.57 | the card busy about 1.7 s a frame |

What it costs the machine (runs 8-10): the game's working set is 20-23.5 GB, so close browsers and launchers
before playing on a 32 GB laptop (Series X needs that most); the card's memory stays at 8.9-11.0 GB of 12. In
the Series S runs (8, 9b, 10) the CPU's work for a frame (copies, textures, records) is 30-43 ms: that, not the
GPU, is the limit, and DLSS's lower scene scale makes it smaller too.

## Not measured yet

- Series X with DLSS and frame generation, with other apps closed (the fork's own tests are on that profile:
  26-30 frames a second on an RTX 5070 12 GB desktop at 1440p).
- Longer play: these are five-minute runs of the opening.
- The picture, side by side with and without DLSS.
