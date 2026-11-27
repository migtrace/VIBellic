"""VIBellic: summarise the 5-second frame lines of one or more `victory run` logs (counts only, nothing from the game).

Usage: python -I tools\\frame-summary.py [--json] [--label NAME] <run log> [more logs]
A run log is what `victory run` prints (save it: `... 2>&1 > run.log`, or the fork launcher's log folder).

What the numbers are (they are statistics of REPORTING WINDOWS, not of single frames):
- The layer prints one line about every 5 seconds: frames a second, milliseconds a frame (the window's mean),
  CPU preparation, GPU time, draws a frame and dropped draws, all averaged over that window.
- A window with >= 500 draws a frame counts as "world" (menus and loading screens have far fewer). This is a
  heuristic: it does not show that the picture was right.
- "median / p10 / p90 window ms" are percentiles of those window means. They are NOT 1 % lows or frame-time
  percentiles; the log has no per-frame times.
- "throughput" is frames / seconds over the world windows, using each window's fps times its length (the time
  since the previous line), when the lines carry timestamps; otherwise it is reported as unknown and only the
  plain mean of window fps ("mean of windows") is given, labelled as such.
- GPU time: if every world window says 0.0, the build's GPU meter is not running: reported as N/A, never 0.
- Frame generation: presents with it on / off and the frames it generated, as the layer counts them. A presented
  frame rate is not derived from them (unknown).

Nothing is printed from a line except these numbers; the input path is not printed (the label is the file name, or
--label). Lines that do not parse are counted, never shown. Keep the log itself on your PC.

Copyright (C) 2026 VIBellic contributors. GPL-3.0-or-later: see LICENSE.
"""
import datetime
import json
import os
import re
import statistics
import sys

ANSI = re.compile(r"\x1b\[[0-9;]*m")
STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)Z?\s")
LINE = re.compile(
    r"([\d.]+) fps, ([\d.]+) ms/frame \(([\d.]+) preparing: copies ([\d.]+) ms ([\d.]+) MB, textures ([\d.]+) ms "
    r"([\d.]+) MB; ([\d.]+) on the GPU; ([\d.]+) copying back ([\d.]+) MB\), (\d+) draws/frame, dropped (\d+)"
)
# A line that looks like a frame report but does not parse completely (counted as malformed, never shown).
LOOKS_LIKE = re.compile(r" fps, [\d.]+ ms/frame ")
FG = re.compile(r"DLSS Frame Generation: (\d+) presents with it on, (\d+) off, (\d+) frames shown by it")
FIELDS = ("fps", "ms", "prep", "copy_ms", "copy_mb", "tex_ms", "tex_mb", "gpu", "back_ms", "back_mb", "draws",
          "dropped")
WORLD_DRAWS = 500


def pct(xs, p):
    """Linear-interpolated percentile p (0-100) of xs; None for no data."""
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def parse_stamp(text):
    try:
        return datetime.datetime.fromisoformat(text)
    except ValueError:
        return None


def read_lines(path):
    """The log's lines, or None when it cannot be read (missing, unreadable)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return None


def summarise_lines(lines):
    """A dict of numbers for one log's lines (see the module docstring for their meaning)."""
    rows, malformed = [], 0
    fg = {"status_lines": 0, "presents_on": 0, "presents_off": 0, "generated": 0}
    prev_time = None
    for raw in lines:
        line = ANSI.sub("", raw)
        m = LINE.search(line)
        stamp = STAMP.match(line)
        when = parse_stamp(stamp.group(1)) if stamp else None
        if m:
            v = [float(x) for x in m.groups()]
            row = dict(zip(FIELDS, v))
            row["seconds"] = (when - prev_time).total_seconds() if (when and prev_time) else None
            rows.append(row)
            if when:
                prev_time = when
        elif LOOKS_LIKE.search(line):
            malformed += 1
        g = FG.search(line)
        if g:
            fg["status_lines"] += 1
            fg["presents_on"] += int(g.group(1))
            fg["presents_off"] += int(g.group(2))
            fg["generated"] += int(g.group(3))
    world = [r for r in rows if r["draws"] >= WORLD_DRAWS]
    menus = [r for r in rows if r["draws"] < 100]
    out = {
        "statistics_of": "5-second reporting windows (not single frames)",
        "frame_lines": len(rows),
        "malformed_frame_lines": malformed,
        "world_windows": len(world),
        "world_rule": f"draws/frame >= {WORLD_DRAWS}",
        "menu_windows_median_ms": statistics.median(r["ms"] for r in menus) if menus else None,
        "frame_generation": fg if fg["status_lines"] else None,
        "presented_fps": None,
    }
    if not world:
        return out
    ms = [r["ms"] for r in world]
    mean = lambda k: statistics.fmean(r[k] for r in world)
    timed = [r for r in world if r["seconds"] and r["seconds"] > 0]
    seconds = sum(r["seconds"] for r in timed)
    frames = sum(r["fps"] * r["seconds"] for r in timed)
    gpu_values = [r["gpu"] for r in world]
    out.update({
        "window_ms_median": statistics.median(ms),
        "window_ms_p10": pct(ms, 10),
        "window_ms_p90": pct(ms, 90),
        "window_ms_min": min(ms),
        "window_ms_max": max(ms),
        "mean_of_window_fps": mean("fps"),
        "throughput_fps": frames / seconds if seconds > 0 else None,
        "throughput_seconds": seconds if seconds > 0 else None,
        "windows_at_30_cap": sum(1 for x in ms if x <= 33.4),
        "prep_ms": mean("prep"),
        "copy_ms": mean("copy_ms"),
        "copy_mb": mean("copy_mb"),
        "tex_ms": mean("tex_ms"),
        "tex_mb": mean("tex_mb"),
        "gpu_ms": None if all(g == 0.0 for g in gpu_values) else statistics.fmean(gpu_values),
        "back_ms": mean("back_ms"),
        "back_mb": mean("back_mb"),
        "draws": mean("draws"),
        "dropped": mean("dropped"),
        "dropped_share": mean("dropped") / mean("draws") if mean("draws") else None,
    })
    return out


def summarise(path):
    lines = read_lines(path)
    if lines is None:
        return {"error": "log not readable"}
    return summarise_lines(lines)


def fmt(x, nd=1):
    return "unknown" if x is None else f"{x:,.{nd}f}"


def text_report(label, s):
    out = [f"== {label}"]
    if "error" in s:
        return out + [f"error: {s['error']}"]
    out.append(f"frame lines {s['frame_lines']} (malformed, not shown: {s['malformed_frame_lines']}), "
               f"world windows {s['world_windows']} ({s['world_rule']}); statistics of {s['statistics_of']}")
    if s["menu_windows_median_ms"] is not None:
        out.append(f"menus/loading windows (<100 draws): median {fmt(s['menu_windows_median_ms'])} ms/frame")
    if s["world_windows"]:
        out.append(f"world window ms/frame: median {fmt(s['window_ms_median'])}, p10 {fmt(s['window_ms_p10'])}, "
                   f"p90 {fmt(s['window_ms_p90'])}, min {fmt(s['window_ms_min'])}, max {fmt(s['window_ms_max'])}; "
                   f"windows at the 30 fps cap: {s['windows_at_30_cap']}")
        out.append(f"rendered throughput {fmt(s['throughput_fps'], 2)} fps over {fmt(s['throughput_seconds'], 0)} s "
                   f"of world windows; mean of window fps {fmt(s['mean_of_window_fps'], 2)}")
        gpu = "N/A (GPU meter not running in this build)" if s["gpu_ms"] is None else f"{fmt(s['gpu_ms'])} ms"
        out.append(f"world means/frame: preparing {fmt(s['prep_ms'])} ms (copies {fmt(s['copy_ms'])} ms "
                   f"{fmt(s['copy_mb'])} MB, textures {fmt(s['tex_ms'])} ms {fmt(s['tex_mb'])} MB), GPU {gpu}, "
                   f"copying back {fmt(s['back_ms'])} ms {fmt(s['back_mb'])} MB; draws {fmt(s['draws'], 0)}, "
                   f"dropped {fmt(s['dropped'], 0)} ({fmt(100 * s['dropped_share'] if s['dropped_share'] is not None else None)} %)")
    fg = s["frame_generation"]
    if fg:
        out.append(f"frame generation: {fg['presents_on']:,} presents with it on, {fg['presents_off']:,} off, "
                   f"{fg['generated']:,} generated (layer's counts); presented fps: unknown")
    return out


def main(argv):
    as_json, label, paths = False, None, []
    it = iter(argv)
    for a in it:
        if a == "--json":
            as_json = True
        elif a == "--label":
            label = next(it, None)
        else:
            paths.append(a)
    if not paths:
        print(__doc__.split("\n\n")[1])
        return 2
    results = []
    for p in paths:
        name = label if (label and len(paths) == 1) else os.path.basename(p)
        results.append((name, summarise(p)))
    if as_json:
        print(json.dumps([dict(label=n, **s) for n, s in results], indent=2))
    else:
        for n, s in results:
            print("\n".join(text_report(n, s)))
    return 1 if any("error" in s for _, s in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
