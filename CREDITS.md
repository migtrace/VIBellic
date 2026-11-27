# Credits

VIBellic is a small kit (notes, two patches, a measuring tool) on top of other people's work. Everything that makes
the game run is theirs. Thank you all.

## The layer you build

- **[VIctory](https://github.com/Marvisak/VIctory)** by Marvisak and its contributors (GPL-3.0-or-later): the
  loader, the runtime services, the Direct3D 12 back end and the shader recompiler that every project below
  stands on.
- **[foxhound](https://github.com/readmet3xt-lab/foxhound)** by readmet3xt-lab (GPL-3.0-or-later): the base that
  VIctory-NVIDIA moved to, with the work it gathered from many forks (its README names them).
- **[VIctory-NVIDIA](https://github.com/trustno1-coder/VIctory-NVIDIA)** by trustno1-coder and its contributors:
  the NVIDIA-tuned tree, DLSS / frame generation through Streamline, the in-game settings menu.
- **[fxceless/victory-fork](https://github.com/fxceless/victory-fork)** by fxceless and its contributors: the tree
  this kit builds (commit `f299fba`, 27 Nov 2026), rebased on VIctory-NVIDIA, with its launcher settings and the
  water light on 32-lane cards. Its README credits further projects
  (VIctory-7900XTX, cool_fox, DexNom's VIctory, Belobug's AMD fork, xcl and others); that credit carries over here.
- **xcl** (another layer for the same title, GPL-2.0-only): part of the fork's history. The fork's files derived
  from it are the fork's to distribute; this kit does not copy them.

## Projects measured and compared on the same laptop

- **[ZJOU-VICTORY](https://github.com/FQY55kai/ZJOU-VICTORY)** by FQY55kai: built and run here (source revision
  `66450431`, the last one before its packaged release), and its measuring method (two identical runs first, to
  know the noise, before any switch is believed) shaped how `docs/results.md` reads.
- The upstream VIctory pull requests used in our upstream-based comparison build (run 2 in `docs/results.md`):
  #2596 by Creaa, #2683 by pes7, #2633 by chippy01, #2885 by jujumoneylol.
- **[Leonida](https://github.com/ubiquitarianism/leonida)** (GPL-3.0-or-later): its `check_no_game_data.py`
  guards every commit of this repository, so that nothing from the game is ever published.
- The lighting stand-ins we tried on the upstream build (a ray miss and an ambient floor) came from
  **[flamingo](https://github.com/realblastex/flamingo)** by realblastex and
  **[Belobug's fork](https://github.com/Belobug/VIctory-Belobug-AMD)**.

## Not ours and not here

- **NVIDIA Streamline, DLSS and Reflex** are NVIDIA's, under NVIDIA's licences. This repository does not carry
  them; you get them from [NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline) yourself.
- **The game** is its owners'. No game file, code, shader, texture, key or anything taken from them is in this
  repository, and nothing here works around any protection. You need your own copy.

## This kit

The patches, notes and `tools/frame-summary.py` are GPL-3.0-or-later (see `LICENSE`), by the VIBellic
contributors. Much of the work was done with [Claude Code](https://claude.com/claude-code).
