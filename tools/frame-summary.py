"""VIBellic: summarise the 5-second frame lines of one or more `victory run` logs (counts only, nothing from the game).

Usage: python -I tools\\frame-summary.py <run log> [more logs]
A run log is what `victory run` prints (save it: `... 2>&1 > run.log`, or the fork launcher's log folder).
World windows are lines with >= 500 draws/frame (as in docs/results.md); menus and loading screens have far fewer.
The output is counts only, so it can be shared in an issue; the log itself names shaders and addresses: keep it.

Copyright (C) 2026 VIBellic contributors. GPL-3.0-or-later: see LICENSE.
"""
import re
import statistics
import sys

LINE = re.compile(
    r"([\d.]+) fps, ([\d.]+) ms/frame \(([\d.]+) preparing: copies ([\d.]+) ms ([\d.]+) MB, textures ([\d.]+) ms "
    r"([\d.]+) MB; ([\d.]+) on the GPU; ([\d.]+) copying back ([\d.]+) MB\), (\d+) draws/frame, dropped (\d+)"
)


def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def summarise(path):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LINE.search(line)
            if m:
                v = [float(x) for x in m.groups()]
                rows.append(dict(fps=v[0], ms=v[1], prep=v[2], copy_ms=v[3], copy_mb=v[4], tex_ms=v[5], tex_mb=v[6],
                                 gpu=v[7], back_ms=v[8], back_mb=v[9], draws=v[10], dropped=v[11]))
    world = [r for r in rows if r["draws"] >= 500]
    print(f"== {path}")
    print(f"frame lines {len(rows)}, world lines {len(world)}")
    menus = [r for r in rows if r["draws"] < 100]
    if menus:
        print(f"menus/loading (<100 draws): median {statistics.median(r['ms'] for r in menus):.1f} ms/frame")
    if not world:
        return
    ms = [r["ms"] for r in world]
    mean = lambda k: statistics.fmean(r[k] for r in world)
    print(f"world ms/frame: median {statistics.median(ms):.1f}, p10 {pct(ms, 10):.1f}, p90 {pct(ms, 90):.1f}, "
          f"min {min(ms):.1f}, max {max(ms):.1f}; mean fps {mean('fps'):.2f}")
    print(f"world means/frame: preparing {mean('prep'):.1f} ms (copies {mean('copy_ms'):.1f} ms {mean('copy_mb'):.1f} MB, "
          f"textures {mean('tex_ms'):.1f} ms {mean('tex_mb'):.1f} MB), GPU {mean('gpu'):.1f} ms, copying back "
          f"{mean('back_ms'):.1f} ms {mean('back_mb'):.1f} MB; draws {mean('draws'):.0f}, dropped {mean('dropped'):.0f} "
          f"({100 * mean('dropped') / max(mean('draws'), 1):.1f} %)")


for p in sys.argv[1:]:
    summarise(p)
