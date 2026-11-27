# VIBellic

**Grand Theft Auto VI (Xbox Series X|S) on a gaming laptop: 24 fps rendered, about twice that shown with DLSS
frame generation, on an i9-14900HX + RTX 4080 Laptop GPU (12 GB) + 32 GB.** From files you supply.

VIBellic is a laptop kit for the [VIctory](https://github.com/Marvisak/VIctory) family of open-source layers that
run the game's Xbox Series build natively on Windows. It does not hold a layer of its own: it tells you which tree
ran best on this hardware, the settings that were measured, two small patches, and a tool to measure your own
runs, so that owners of the same kind of laptop can start where we ended.

The layer is **[fxceless/victory-fork](https://github.com/fxceless/victory-fork)** (on
[VIctory-NVIDIA](https://github.com/trustno1-coder/VIctory-NVIDIA), on [foxhound](https://github.com/readmet3xt-lab/foxhound),
on VIctory). All of the work that makes the game run is theirs: see [CREDITS.md](CREDITS.md).

## Results on this laptop

Acer Predator Helios 16 (PH16-72): Core i9-14900HX, GeForce RTX 4080 Laptop GPU 12 GB (driver 621.40), 32 GB
DDR5-5600, Windows 11, on mains power. The opening of the game, five-minute runs, the layer's own frame counts.

| Settings | Profile | Frame time (median) | Frames a second |
|---|---|---|---|
| **DLSS Quality + DLSS frame generation 2x** | Series S | **41 ms** (34-39 ms in the last minute) | **24 rendered (26-29 in the last minute), about twice that shown** |
| No DLSS, pipelines made ahead | Series S | 48 ms, steady | 21 |
| No DLSS, first run | Series S | 61 ms, hitches while pipelines are made | 16 |
| No DLSS | Series X | 83 ms (short run, see notes) | 12 |
| For comparison: upstream VIctory + its NVIDIA pull requests | Series X | 1,829 ms | 0.5 |

Every run, its settings and its limits: [docs/results.md](docs/results.md). What we learned getting here (why
upstream is slow on this card, how we measured, a survey of the NVIDIA forks): [docs/findings.md](docs/findings.md).
The title paces itself at 30 frames
a second, and these are early numbers from one machine: the picture was not judged and longer play was not
measured.

### Same laptop, or close to it?

If yours has a 14th-generation HX Core i9 (or a similar 13th-generation one), an RTX 4080 Laptop GPU with 12 GB
and 32 GB of memory, the numbers above are what to expect. The limit here is the CPU's work for each frame
(30-43 ms), not the card, so the CPU and memory matter at least as much as the GPU. Please report what yours
does (see *Reporting* below).

## Getting started

You need: Windows 10 or 11, 32 GB of memory, an NVIDIA RTX 40 or newer laptop GPU with a recent driver, Rust
([rustup](https://rustup.rs); the toolchain is pinned), the Visual Studio Build Tools with *Desktop development
with C++*, Git, and **your own copy** of the game's Xbox Series build v1.0.2.1 (the folder with
`game_scarlett_master.exe`). Nothing of the game is in this repository or in the layer's.

```powershell
git clone https://github.com/migtrace/VIBellic
git clone https://github.com/fxceless/victory-fork
cd victory-fork
git checkout f299fba                       # the tree measured here
# Optional: the two patches (they only matter when you start the game on chosen CPU cores, see below)
git apply ..\VIBellic\patches\0001-hle-thread-affinity-stays-within-the-launch-mask.patch
git apply ..\VIBellic\patches\0002-hle-empty-thread-affinity-mask-passed-on.patch
copy victory.example.toml victory.toml     # set game_dir to your copy; keep every path outside this folder
cargo build --release --locked -p victory
target\release\victory.exe shaders        # once per build: every shader into the cache (about 2 minutes here)
```

DLSS and frame generation use NVIDIA's own files, which no repository may carry. The fork's
`Get-NVIDIA-DLSS.cmd` fetches them (about 70 MB) from [NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline)
on GitHub; or download `streamline-sdk-v2.14.16.zip` from that project's releases yourself and copy the DLLs the
fork names (`sl.*.dll`, `nvngx_dlss.dll`, `nvngx_dlssg.dll`, from `bin\x64`) into `nvidia-sdk\Streamline\bin\x64`
in the fork's folder. Windows' *Hardware-accelerated GPU scheduling* must be on for frame generation.

Then play with the fork's own launcher, on the settings measured above:

```powershell
.\scripts\play-foxhound.ps1 -Exe 'D:\MyDump\game_scarlett_master.exe' -SeriesS -Dlss quality -FrameGen
```

- Leave out `-Dlss quality -FrameGen` to play without NVIDIA's files (the title's own upscaling, row 2 above).
- The launcher lifts the title's own 30 fps pace by default; `-Fps 30` keeps it, as in every run above.
- `-SeriesS` is the lighter profile (1280x720 inside). Without it the launcher uses Series X at 1440p; on a 32 GB
  laptop close browsers, game launchers and the like first: Series X took the game to 23.5 GB here.
- After your first session, `target\release\victory.exe warm --used` makes ahead the pipelines that session drew
  with, so the next one does not hitch on them (row 3 to row 2 above).
- In the game, F1 is the fork's settings menu and F3 its stats panel; Enter or Space is A, Esc is Menu, or use
  a controller.

## Memory on a 32 GB laptop

The game takes 20-23.5 GB, so check Task Manager's *Available* memory before you start: about 25 GB is
comfortable. A browser with many tabs, chat and AI desktop apps, game launchers (Steam, Epic), music, cloud
sync and VPN apps each take hundreds of MB to a few GB; close them for the session, and take the ones you do not
need every day out of *Settings > Apps > Startup*. Keep the laptop maker's control app (fans, power), the audio
and NVIDIA services and your antivirus. Leave Windows' paging file on (system managed): with it a tight moment
slows down instead of ending the game.

## Reporting

`tools/frame-summary.py` reads a run's log and prints counts only (frame times, draws, memory moved), which you
can paste into an issue here without sharing anything from the game:

```powershell
python -I VIBellic\tools\frame-summary.py "$env:LOCALAPPDATA\victory\logs\foxhound-<date>.log"
```

Keep the log itself on your PC: it names the game's shaders and addresses. Say which laptop, which profile and
which settings, and whether it was the first session after a build.

## Side note

[Running the game on chosen CPU cores](docs/cpu-affinity.md): why `start /affinity` does not hold for this game
without the patches here, and why this kit needed it.

## License

This kit (patches, notes, `tools/`) is GPL-3.0-or-later, like VIctory: see [LICENSE](LICENSE). What you build is
the fork's, under its own licence notes. Not affiliated with the game's makers, Microsoft or NVIDIA.
